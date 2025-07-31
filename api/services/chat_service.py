import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import os
import shutil
import base64
import mimetypes
import asyncio
from concurrent.futures import ThreadPoolExecutor
import textwrap
import logging
from contextlib import asynccontextmanager

from services.sse_service import SSEService
from event_handlers.sse_event_handler import SSEEventHandler, SSEMessageType
from session_manager import SessionManager
from models.chat_models import ChatMessage
from config import DATA_SOURCES
from taskweaver.memory.attachment import AttachmentType
from fastapi import HTTPException
import tempfile
import json
from taskweaver.app.app import TaskWeaverApp

logger = logging.getLogger(__name__)

FILE_TYPE_MAP = {
    ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'): 'image',
    ('mp3', 'wav', 'flac', 'aac'): 'audio',
    ('csv',): 'csv',
    ('xlsx', 'xls'): 'excel',
    ('pdf',): 'pdf',
    ('txt', 'log'): 'text',
    ('py', 'js', 'html', 'css', 'json'): 'code'
}

class TaskWeaverError(Exception):
    """TaskWeaver相关错误"""
    pass

class ChatService:
    def __init__(self,
                 session_manager: SessionManager,
                 taskweaver_app,
                 sse_service: SSEService,
                 max_workers: int = 10,
                 task_timeout: int = 1200):
        self.session_manager = session_manager
        self.base_taskweaver_app = taskweaver_app
        self.sse_service = sse_service
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_timeout = task_timeout
        self._active_tasks: Dict[str, asyncio.Task] = {}

        logging.getLogger('taskweaver').setLevel(logging.WARNING)
        
    @asynccontextmanager
    async def _get_taskweaver_session_context(self, session_data: Dict, session_id: str):
        """获取TaskWeaver会话的上下文管理器，使用会话级别配置"""
        taskweaver_session = session_data.get("taskweaver_session")
        created_new = False
        
        try:
            if taskweaver_session is None:
                # 获取会话配置
                session_config = session_data.get("session_config", {})
                
                # 根据会话配置创建TaskWeaver会话
                taskweaver_app = self._create_configured_taskweaver_app(session_config)
                taskweaver_session = taskweaver_app.get_session()
                
                session_data["taskweaver_session"] = taskweaver_session
                session_data["taskweaver_app"] = taskweaver_app
                created_new = True
                logger.info(f"[{session_id}] 创建新的TaskWeaver会话，配置: {session_config}")
            
            yield taskweaver_session
            
        except Exception as e:
            logger.error(f"[{session_id}] TaskWeaver会话错误: {e}")
            if created_new and taskweaver_session:
                try:
                    if hasattr(taskweaver_session, 'stop'):
                        taskweaver_session.stop()
                    session_data["taskweaver_session"] = None
                    session_data["taskweaver_app"] = None
                except Exception as cleanup_error:
                    logger.error(f"[{session_id}] 清理失败的TaskWeaver会话时出错: {cleanup_error}")
            raise
    
    def _create_configured_taskweaver_app(self, session_config: Dict):
        """根据会话配置创建TaskWeaver应用"""
        try:
            if not session_config:
                return self.base_taskweaver_app
            
            # 获取项目目录
            project_dir = os.path.join(os.path.dirname(__file__), "../project")
            
            # 直接使用配置字典创建TaskWeaver应用实例
            taskweaver_app = TaskWeaverApp(
                app_dir=project_dir,
                config=session_config  # TaskWeaver支持直接传递配置字典
            )
            
            logger.info(f"创建配置化TaskWeaver应用成功，配置: {session_config}")
            return taskweaver_app
                
        except Exception as e:
            logger.error(f"创建配置化TaskWeaver应用失败: {e}")
            # 回退到基础应用
            return self.base_taskweaver_app
    
    async def process_message(self, session_id: str, message: ChatMessage):
        event_handler = None
        task_id = f"{session_id}_{datetime.now().timestamp()}"
        
        try:
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                    "message": "会话不存在"
                })
                return
    
            # 添加用户消息到历史
            user_message = {
                "role": "user",
                "content": message.content,
                "selected_table": message.selected_table,
                "timestamp": datetime.now().isoformat(),
                "is_intermediate": False
            }
            session_data["messages"].append(user_message)
    
            # 获取或创建TaskWeaver会话
            async with self._get_taskweaver_session_context(session_data, session_id) as taskweaver_session:
                # 简化：直接使用基础的prompt构建方法，因为模板内容已经包含在message.content中
                prompt = await self._build_prompt(message, session_id)
    
                files = None
                if hasattr(message, 'uploaded_files') and message.uploaded_files:
                    files = []
                    for file_info in message.uploaded_files:
                        try:
                            execution_cwd = taskweaver_session.execution_cwd
                            target_file_path = os.path.join(execution_cwd, file_info['saved_name'])
    
                            if os.path.exists(file_info['saved_path']):
                                shutil.copy2(file_info['saved_path'], target_file_path)
                                os.remove(file_info['saved_path'])
                                logger.info(f"文件移动成功: {file_info['saved_path']} -> {target_file_path}")
                            else:
                                logger.error(f"源文件不存在: {file_info['saved_path']}")
                                continue
    
                            files.append({
                                "name": file_info['original_name'],
                                "path": target_file_path
                            })
                            
                        except Exception as e:
                            logger.error(f"处理文件 {file_info['original_name']} 失败: {e}")
                            await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                                "error": f"文件处理失败: {file_info['original_name']}",
                                "error_type": "file_processing_error"
                            })
                            continue
    
                event_handler = SSEEventHandler(session_id, self.sse_service)
    
                # 执行TaskWeaver任务
                response_round = await self._execute_taskweaver_task(
                    taskweaver_session, prompt, event_handler, task_id, files
                )
                
                final_response, files = await self._process_taskweaver_response(
                    response_round, session_data
                )
    
                # 发送完成消息
                data = {"response": final_response}
                if files:
                    data["files"] = files
                await self.sse_service.send_message(session_id, SSEMessageType.CHAT_COMPLETED, data)
            
        except Exception as e:
            logger.exception(f"[{session_id}] TaskWeaver执行失败: {e}")
            await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                "error": "系统内部错误，请稍后重试",
                "error_type": "system_error"
            })
            
        finally:
            if event_handler:
                try:
                    event_handler.cleanup()
                except Exception as e:
                    logger.error(f"[{session_id}] 清理事件处理器失败: {e}")
            
            self._active_tasks.pop(task_id, None)
            logger.info(f"[{session_id}] 消息处理完成，资源已清理")

    async def _execute_taskweaver_task(self, taskweaver_session, prompt: str, 
                                     event_handler, task_id: str, files: Optional[List[Dict]] = None) -> Any:
        def _run_taskweaver():
            try:
                # 移除错误的 set_context 调用
                # TaskWeaver Session 对象没有 set_context 方法
                # 模板信息已经包含在 prompt 中
                
                return taskweaver_session.send_message(
                    prompt,
                    event_handler=event_handler,
                    files=files
                )
            except Exception as e:
                logger.error(f"TaskWeaver线程执行失败: {e}")
                raise TaskWeaverError(f"TaskWeaver执行失败: {str(e)}")
        
        loop = asyncio.get_running_loop()
        task = loop.create_task(
            asyncio.wait_for(
                loop.run_in_executor(self.executor, _run_taskweaver),
                timeout=self.task_timeout
            )
        )
        
        self._active_tasks[task_id] = task
        
        try:
            return await task
        except asyncio.CancelledError:
            logger.warning(f"TaskWeaver任务被取消: {task_id}")
            raise TaskWeaverError("任务被取消")
        except asyncio.TimeoutError:
            logger.error(f"TaskWeaver任务超时: {task_id}")
            task.cancel()  # 取消任务
            raise
        finally:
            self._active_tasks.pop(task_id, None)

    async def _build_prompt(self, message: ChatMessage, session_id: str) -> str:
        """构建提示词"""
        prompt = message.content
    
        if message.selected_table:
            if message.selected_table not in DATA_SOURCES:
                await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                    "error": "选择的数据源不存在"
                })
                raise TaskWeaverError("选择的数据源不存在")
    
            table_info = DATA_SOURCES[message.selected_table]
            prompt = textwrap.dedent(f"""
            请使用sql_pull_data插件从数据库中获取数据并完成任务。
            
            **数据源信息：**
            表名: {table_info['table_name']}
            表描述: {table_info['table_des']}
            字段信息: {table_info['table_columns']}
            字段描述: {table_info['table_columns_names']}\n""").strip()

            if message.content.find('## 任务描述') >= 0 and message.content.find('## 分析目标') >=0:
                prompt += message.content
            else:
                prompt += textwrap.dedent(f"""
                {prompt}
                **数据分析要求：**
                1. **数据理解**请先从数据库|文件中获取相关数据，理解数据结构和业务含义
                2. **业务洞察**提供具有客服运营指导意义的专业分析结果
                3. **实用建议**：给出具体的客服服务优化或运营改进建议
                **分析任务：** {message.content}
                请使用专业的客服和移动通信术语，确保分析结果对客服管理和移动通信行业具有实际意义。
                """).strip()

        # 在 _build_prompt 方法中添加实际的文件内容读取
        elif hasattr(message, 'uploaded_files') and message.uploaded_files:
            file_names = [file_info['original_name'] for file_info in message.uploaded_files]
            files_list = "\n".join([f"- {name}" for name in file_names])

            file_contents = []
            for file_info in message.uploaded_files:
                file_path = file_info['saved_path']
                try:
                    # 在_build_prompt_with_files方法中修复CSV读取
                    if file_path.endswith('.csv'):
                        import pandas as pd
                        # 尝试多种编码
                        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                        df = None
                        for encoding in encodings:
                            try:
                                df = pd.read_csv(file_path, nrows=2, encoding=encoding)
                                break
                            except (UnicodeDecodeError, UnicodeError):
                                continue
                        
                        if df is not None:
                            content = f"CSV文件 :\n{df.to_string()}"
                        else:
                            content = "CSV文件读取失败：编码不支持"
                    elif file_path.endswith(('.xlsx', '.xls')):
                        import pandas as pd
                        try:
                            df = pd.read_excel(file_path, nrows=2)
                            content = f"Excel文件 :\n{df.to_string()}"
                        except Exception as e:
                            content = f"Excel文件读取失败：{str(e)}"
                    elif file_path.endswith('.json'):
                        import json
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        content = f"JSON文件 :\n{json.dumps(data, ensure_ascii=False, indent=2)[:1000]}"
                    else:
                        content = f""
                    file_contents.append(content)
                except Exception as e:
                    file_contents.append(f"")
                
                prompt = f"""数据文件前2行内容如下：{chr(10).join(file_contents)}\n请根据当前数据文件完成以下任务：{message.content}\n\n请使用中文回复。"""
    
        return prompt

    async def _process_taskweaver_response(self, response_round, session_data) -> Tuple[str, List[Dict]]:
        """处理TaskWeaver响应"""
        final_response = ""
        session_cwd_path = session_data["taskweaver_session"].execution_cwd
        files = []
        seen_paths = set()

        ALLOWED_EXTENSIONS = {".csv", ".json", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".txt", ".vis"}

        def is_allowed_file(filename: str) -> bool:
            ext = os.path.splitext(filename)[1].lower()
            return ext in ALLOWED_EXTENSIONS

        async def process_and_add_file(file_path_or_name: str):
            if file_path_or_name in seen_paths:
                return

            # 统一处理路径和文件名
            file_name = os.path.basename(file_path_or_name)
            absolute_file_path = file_path_or_name if os.path.isabs(file_path_or_name) else os.path.normpath(os.path.join(session_cwd_path, file_name))
            session_cwd_abs = os.path.abspath(session_cwd_path)

            # 安全检查
            if not absolute_file_path.startswith(session_cwd_abs):
                logger.warning(f"检测到潜在的路径遍历攻击，已阻止访问: {file_name}")
                return  # 或 continue

            file_content = await self._read_file_content_safe(absolute_file_path)
            if file_content:
                files.append({
                    "name": file_name,
                    "path": file_path_or_name,  # or just file_name
                    "type": "file",
                    "content": file_content,
                    "mime_type": self._get_mime_type(file_name)  # 用文件名判断mime更通用
                })
                seen_paths.add(file_path_or_name)
        try:
            artifact_paths = [
                p for post in response_round.post_list
                for a in post.attachment_list
                if a.type == AttachmentType.artifact_paths
                for p in a.content
            ]

            for post in response_round.post_list:
                if post.send_from == "User":
                    continue
                final_response = post.message
                pattern = r"file_name:\s*([\w\-. ]+\.[a-zA-Z0-9]+)"
                matches = re.findall(pattern, post.message)
                for file_name in matches:
                    await process_and_add_file(file_name)

            for file_path in artifact_paths:
                await process_and_add_file(file_path)

            if os.path.isdir(session_cwd_path):
                for file_name in os.listdir(session_cwd_path):
                    if not is_allowed_file(file_name):
                        continue
                    full_path = os.path.join(session_cwd_path, file_name)
                    await process_and_add_file(file_name)
                    # if os.path.isfile(full_path) and file_name in final_response and file_name not in seen_paths:
                    #     await process_and_add_file(file_name)

            return final_response, files
            
        except Exception as e:
            logger.error(f"处理TaskWeaver响应失败: {e}")
            return final_response or "处理响应时出现错误", []

    async def _read_file_content_safe(self, file_path: str) -> str:
        """安全地读取文件内容"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                return ""
            
            # 检查文件大小（限制为10MB）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:
                logger.warning(f"文件过大，跳过: {file_path} ({file_size} bytes)")
                return ""
            
            # 异步读取文件
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, 
                self._read_file_sync, 
                file_path
            )
            
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""

    def _read_file_sync(self, file_path: str) -> str:
        """同步读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试二进制读取并base64编码
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    return base64.b64encode(content).decode('utf-8')
            except Exception as e:
                logger.error(f"二进制读取文件失败 {file_path}: {e}")
                return ""
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""

    def _get_mime_type(self, file_path: str) -> str:
        """获取文件MIME类型"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('image'):
                mime_type = 'image'
            if file_path.endswith('.vis'):
                mime_type = 'gpt_vis'
            return mime_type or "application/octet-stream"
        except Exception:
            return 'application/octet-stream'

    async def cancel_task(self, session_id: str) -> bool:
        """取消指定会话的活跃任务"""
        cancelled_count = 0
        tasks_to_cancel = [
            task for task_id, task in self._active_tasks.items()
            if task_id.startswith(session_id)
        ]
        
        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
                cancelled_count += 1
        
        if cancelled_count > 0:
            logger.info(f"取消了 {cancelled_count} 个任务，会话: {session_id}")
            await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                "message": f"已取消 {cancelled_count} 个正在执行的任务"
            })
        
        return cancelled_count > 0

    async def shutdown(self):
        """关闭服务，清理所有资源"""
        logger.info("开始关闭ChatService...")
        
        # 取消所有活跃任务
        for task_id, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                logger.info(f"取消任务: {task_id}")
        
        # 等待所有任务完成或取消
        if self._active_tasks:
            await asyncio.gather(
                *self._active_tasks.values(),
                return_exceptions=True
            )
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("ChatService已关闭")

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "active_tasks": len(self._active_tasks),
            "executor_threads": self.executor._threads if hasattr(self.executor, '_threads') else 0,
            "task_timeout": self.task_timeout
        }