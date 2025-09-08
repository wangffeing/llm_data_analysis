import re
import os
import shutil
import base64
import mimetypes
import asyncio
import textwrap
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from services.sse_service import SSEService
from event_handlers.sse_event_handler import SSEEventHandler, SSEMessageType
from session_manager import SessionManager
from models.chat_models import ChatMessage
from services.data_source_service import DataSourceService
from taskweaver.memory.attachment import AttachmentType
from taskweaver.app.app import TaskWeaverApp
from config import get_config

logger = logging.getLogger(__name__)

class TaskWeaverError(Exception):
    """TaskWeaver相关错误"""
    pass

class ChatService:
    def __init__(self,
                 session_manager: SessionManager,
                 taskweaver_app,
                 sse_service: SSEService,
                 max_workers: int = 5,
                 task_timeout: int = 1800):
        self.session_manager = session_manager
        self.base_taskweaver_app = taskweaver_app
        self.sse_service = sse_service
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_timeout = task_timeout
        self._active_tasks: Dict[str, asyncio.Task] = {}
        
        # 初始化数据源服务
        config = get_config()
        self.data_source_service = DataSourceService(config.config_db_path)
        
        # 设置TaskWeaver日志级别
        logging.getLogger('taskweaver').setLevel(logging.WARNING)

    @asynccontextmanager
    async def _get_taskweaver_session_context(self, session_data: Dict, session_id: str):
        """获取TaskWeaver会话的上下文管理器，使用会话级别配置"""
        taskweaver_session = session_data.get("taskweaver_session")
        created_new = False
        
        try:
            if taskweaver_session is None:
                session_config = session_data.get("session_config", {})
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
                await self._cleanup_taskweaver_session(session_data, session_id)
            raise
    
    async def _cleanup_taskweaver_session(self, session_data: Dict, session_id: str):
        """异步清理TaskWeaver会话"""
        try:
            taskweaver_session = session_data.get("taskweaver_session")
            if taskweaver_session and hasattr(taskweaver_session, 'stop'):
                # 在线程池中执行可能阻塞的清理操作
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    self.executor,
                    taskweaver_session.stop
                )
            session_data["taskweaver_session"] = None
            session_data["taskweaver_app"] = None
        except Exception as cleanup_error:
            logger.error(f"[{session_id}] 清理TaskWeaver会话失败: {cleanup_error}")
    
    def _create_configured_taskweaver_app(self, session_config: Dict):
        """根据会话配置创建TaskWeaver应用"""
        try:
            if not session_config:
                return self.base_taskweaver_app
            
            project_dir = os.path.join(os.path.dirname(__file__), "../project")
            taskweaver_app = TaskWeaverApp(
                app_dir=project_dir,
                config=session_config
            )
            
            logger.info(f"创建配置化TaskWeaver应用成功，配置: {session_config}")
            return taskweaver_app
                
        except Exception as e:
            logger.error(f"创建配置化TaskWeaver应用失败: {e}")
            return self.base_taskweaver_app
    
    async def process_message(self, session_id: str, message: ChatMessage):
        event_handler = None
        # task_id = f"{session_id}_{datetime.now().timestamp()}"
        task_id = f"{session_id}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"

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
    
            async with self._get_taskweaver_session_context(session_data, session_id) as taskweaver_session:
                prompt = await self._build_prompt(message, session_id)
                files = await self._process_uploaded_files(message, taskweaver_session, session_id)
                
                event_handler = SSEEventHandler(session_id, self.sse_service)
    
                response_round = await self._execute_taskweaver_task(
                    taskweaver_session, prompt, event_handler, task_id, files
                )
                
                final_response, output_files = await self._process_taskweaver_response(
                    response_round, session_data
                )
    
                data = {
                    "response": final_response,
                    "session_id": session_id
                }
                if output_files:
                    data["files"] = output_files
                    
                await self.sse_service.send_message(session_id, SSEMessageType.CHAT_COMPLETED, data)
            
        except Exception as e:
            logger.exception(f"[{session_id}] TaskWeaver执行失败: {e}")
            await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                "error": "系统内部错误，请稍后重试",
                "error_type": "system_error"
            })
            
        finally:
            await self._cleanup_resources(event_handler, task_id, session_id)
    
    async def _process_uploaded_files(self, message: ChatMessage, taskweaver_session, session_id: str) -> Optional[List[Dict]]:
        """异步处理上传的文件"""
        if not (hasattr(message, 'uploaded_files') and message.uploaded_files):
            return None
            
        files = []
        execution_cwd = taskweaver_session.execution_cwd
        
        for file_info in message.uploaded_files:
            try:
                target_file_path = os.path.join(execution_cwd, file_info['saved_name'])
                
                if os.path.exists(file_info['saved_path']):
                    # 异步文件操作
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        self.executor,
                        self._move_file_sync,
                        file_info['saved_path'],
                        target_file_path
                    )
                    
                    files.append({
                        "name": file_info['original_name'],
                        "path": target_file_path
                    })
                    logger.info(f"文件处理成功: {file_info['original_name']}")
                else:
                    logger.error(f"源文件不存在: {file_info['saved_path']}")
                    
            except Exception as e:
                logger.error(f"处理文件 {file_info['original_name']} 失败: {e}")
                await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                    "error": f"文件处理失败: {file_info['original_name']}",
                    "error_type": "file_processing_error"
                })
        
        return files if files else None
    
    def _move_file_sync(self, src_path: str, dst_path: str):
        """同步移动文件"""
        shutil.copy2(src_path, dst_path)
        os.remove(src_path)
    
    async def _cleanup_resources(self, event_handler, task_id: str, session_id: str):
        """清理资源"""
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
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise

        finally:
            self._active_tasks.pop(task_id, None)

    async def _build_prompt(self, message: ChatMessage, session_id: str) -> str:
        """构建提示词"""
        prompt = message.content
    
        if message.selected_table:
            prompt = await self._build_table_prompt(message, session_id)
        elif hasattr(message, 'uploaded_files') and message.uploaded_files:
            prompt = await self._build_file_prompt(message)
    
        return prompt
    
    async def _build_table_prompt(self, message: ChatMessage, session_id: str) -> str:
        """构建表格相关的提示词"""
        data_sources = await self.data_source_service.get_all_data_sources()
        if message.selected_table not in data_sources:
            await self.sse_service.send_message(session_id, SSEMessageType.ERROR, {
                "error": "选择的数据源不存在"
            })
            raise TaskWeaverError("选择的数据源不存在")

        table_info = data_sources[message.selected_table]
        prompt = textwrap.dedent(f"""
        请根据任务使用sql_pull_data插件从数据库中相应数据，并完成用户任务。
        
        ## 任务表信息：
        - 表名: {table_info['table_name']}
        - 表描述: {table_info['table_des']}
        - 字段信息: {table_info['table_columns']}
        - 字段描述: {table_info['table_columns_names']}
        """).strip()

        if '## 任务描述' in message.content and '## 分析目标' in message.content:
            prompt += message.content
        else:
            prompt += textwrap.dedent(f"""
            ## 任务： {message.content}
            """).strip()
            
        return prompt
    
    async def _build_file_prompt(self, message: ChatMessage) -> str:
        """构建文件相关的提示词"""
        file_names = [file_info['original_name'] for file_info in message.uploaded_files]
        
        file_contents = []
        for file_info in message.uploaded_files:
            try:
                content = await self._read_file_preview(file_info['saved_path'])
                file_contents.append(content)
            except Exception as e:
                logger.error(f"读取文件预览失败 {file_info['original_name']}: {e}")
                file_contents.append("")
        
        valid_contents = [content for content in file_contents if content]
        if valid_contents:
            return f"数据文件前2行内容如下：{chr(10).join(valid_contents)}\n请根据当前数据文件完成以下任务：{message.content}\n\n请使用中文回复。"
        else:
            return f"请根据上传的文件完成以下任务：{message.content}\n\n请使用中文回复。"
    
    async def _read_file_preview(self, file_path: str) -> str:
        """异步读取文件预览"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor,
            self._read_file_preview_sync,
            file_path
        )
    
    def _read_file_preview_sync(self, file_path: str) -> str:
        """同步读取文件预览"""
        try:
            if file_path.endswith('.csv'):
                import pandas as pd
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, nrows=2, encoding=encoding)
                        return f"CSV文件:\n{df.to_string()}"
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                return "CSV文件读取失败：编码不支持"
                
            elif file_path.endswith(('.xlsx', '.xls')):
                import pandas as pd
                df = pd.read_excel(file_path, nrows=2)
                return f"Excel文件:\n{df.to_string()}"
                
            elif file_path.endswith('.json'):
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    snippet = f.read(2000)
                return f"JSON文件预览:\n{snippet[:1000]}"
                
            return ""
        except Exception as e:
            logger.error(f"读取文件预览失败: {e}")
            return ""

    async def _process_taskweaver_response(self, response_round, session_data) -> Tuple[str, List[Dict]]:
        """处理TaskWeaver响应"""
        final_response = ""
        session_cwd_path = session_data["taskweaver_session"].execution_cwd
        files = []
        seen_paths = set()

        ALLOWED_EXTENSIONS = {".csv", ".json", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".txt", ".vis"}

        def is_allowed_file(filename: str) -> bool:
            return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

        async def process_and_add_file(file_path_or_name: str):
            file_name = os.path.basename(file_path_or_name)
            if file_name in seen_paths:
                return
                
            absolute_file_path = (
                file_path_or_name if os.path.isabs(file_path_or_name) 
                else os.path.normpath(os.path.join(session_cwd_path, file_name))
            )
            session_cwd_abs = os.path.abspath(session_cwd_path)

            # 安全检查
            if not absolute_file_path.startswith(session_cwd_abs):
                logger.warning(f"检测到潜在的路径遍历攻击，已阻止访问: {file_name}")
                return

            file_content = await self._read_file_content_safe(absolute_file_path)
            if file_content:
                files.append({
                    "name": file_name,
                    "path": file_path_or_name,
                    "type": "file",
                    "content": file_content,
                    "mime_type": self._get_mime_type(file_name)
                })
                seen_paths.add(file_name)
        
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
                    for post in response_round.post_list:
                        if post.message.find(file_name) >= 0:
                            await process_and_add_file(file_name)
                    # if os.path.isfile(full_path) and file_name in final_response and file_name not in seen_paths:
                    #     await process_and_add_file(file_name)

            return final_response, files
                        
        except Exception as e:
            logger.error(f"处理TaskWeaver响应失败: {e}")
            return final_response or "处理响应时出现错误", []

    async def _read_file_content_safe(self, file_path: str) -> str:
        """安全地异步读取文件内容"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            # 检查文件大小（限制为10MB）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:
                logger.warning(f"文件过大，跳过: {file_path} ({file_size} bytes)")
                return ""
            
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor, 
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
            logger.info(f"取消了 {cancelled_count} 个任务")
            return True
        return False

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