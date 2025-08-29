import logging
import uuid
import threading
import shutil
import os
import psutil
import gc
import weakref
import asyncio
from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta
from taskweaver.session.session import Session
from taskweaver.app.app import TaskWeaverApp
import copy
from collections import OrderedDict
import time

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """增强的内存监控器"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取当前内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
                "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
                "percent": memory_percent,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "swap_mb": getattr(memory_info, 'swap', 0) / 1024 / 1024  # 交换内存
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0,
                "available_mb": 0,
                "swap_mb": 0
            }
    
    @staticmethod
    def is_memory_pressure(threshold_percent: float = 80.0) -> bool:
        """检查是否存在内存压力"""
        memory_info = MemoryMonitor.get_memory_usage()
        return memory_info["percent"] > threshold_percent
    
    @staticmethod
    def get_process_open_files() -> int:
        """获取进程打开的文件数量"""
        try:
            process = psutil.Process()
            return len(process.open_files())
        except Exception:
            return 0

class SessionManager:
    def __init__(self,
                 cleanup_interval_minutes: int = 60,  # 缩短清理间隔
                 max_sessions: int = 10,  # 降低最大会话数
                 memory_threshold_percent: float = 75.0,  # 降低内存压力阈值
                 force_cleanup_threshold_percent: float = 85.0,  # 降低强制清理阈值
                 session_timeout_minutes: int = 120):  # 会话超时时间
        
        self.sessions: OrderedDict[str, Dict] = OrderedDict()  # 使用OrderedDict支持LRU
        self.conversation_ids: Dict[str, str] = {}
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.max_sessions = max_sessions
        self.memory_threshold_percent = memory_threshold_percent
        self.force_cleanup_threshold_percent = force_cleanup_threshold_percent
        self.session_timeout_minutes = session_timeout_minutes
        
        self._lock = threading.RLock()
        self._cleanup_timer: Optional[threading.Timer] = None
        self._memory_monitor = MemoryMonitor()
        self._shutdown_flag = False
        
        # 增强的统计信息
        self._stats = {
            "total_created": 0,
            "total_cleaned": 0,
            "memory_cleanups": 0,
            "force_cleanups": 0,
            "timeout_cleanups": 0,
            "workspace_cleanups": 0,
            "last_cleanup_time": None,
            "cleanup_errors": 0
        }
        
        # 跟踪活跃的异步任务
        self._active_tasks: Set[asyncio.Task] = set()
        
        # 跟踪工作空间路径
        self._workspace_paths: Set[str] = set()
        
        self._start_cleanup_timer()
        
        # 优化的默认配置
        self.default_config = {
            "llm.api_type": "lingyun",
            "llm.model": "qwen2.5-32b",
            "execution_service.kernel_mode": "local",
            "code_generator.enable_auto_plugin_selection": "false",
            "code_generator.allowed_plugins": ["sql_pull_data"],
            "code_interpreter.code_verification_on": "false",
            "code_interpreter.allowed_modules": [
                "pandas", "matplotlib", "numpy", "sklearn", "scipy", 
                "seaborn", "datetime", "typing", "json"
            ],
            "logging.log_file": "taskweaver.log",
            "logging.log_folder": "logs",
            "logging.log_level": "WARNING",
            "planner.prompt_compression": "true",
            "code_generator.prompt_compression": "true",
            "session.max_internal_chat_round_num": 15,  # 降低轮次限制
            "session.roles": ["planner", "code_interpreter", "recepta"]
        }
        
    def _start_cleanup_timer(self):
        """启动定时清理任务"""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        
        if self._shutdown_flag:
            return
            
        self._cleanup_timer = threading.Timer(
            self.cleanup_interval_minutes * 60,
            self._periodic_cleanup
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
        
    def _periodic_cleanup(self):
        """增强的定期清理机制"""
        try:
            if self._shutdown_flag:
                return
                
            start_time = time.time()
            logger.info("开始定期清理会话...")
            
            # 检查内存使用情况
            memory_info = self._memory_monitor.get_memory_usage()
            open_files = self._memory_monitor.get_process_open_files()
            
            logger.info(f"内存使用情况: {memory_info}, 打开文件数: {open_files}")
            
            # 清理超时会话
            timeout_cleaned = self._cleanup_timeout_sessions()
            
            # 根据内存压力调整清理策略
            if memory_info["percent"] > self.force_cleanup_threshold_percent:
                logger.warning(f"内存使用率过高 ({memory_info['percent']:.1f}%)，执行强制清理")
                force_cleaned = self._force_cleanup()
                self._stats["force_cleanups"] += 1
                logger.info(f"强制清理完成，清理了 {force_cleaned} 个会话")
            elif memory_info["percent"] > self.memory_threshold_percent:
                logger.info(f"内存压力较大 ({memory_info['percent']:.1f}%)，执行积极清理")
                aggressive_cleaned = self._aggressive_cleanup()
                self._stats["memory_cleanups"] += 1
                logger.info(f"积极清理完成，清理了 {aggressive_cleaned} 个会话")
            else:
                # 正常清理
                normal_cleaned = self.cleanup_inactive_sessions(self.cleanup_interval_minutes)
                logger.info(f"正常清理完成，清理了 {normal_cleaned} 个会话")
            
            # 清理孤立的工作空间
            self._cleanup_orphaned_workspaces()
            
            # 取消已完成的异步任务
            self._cleanup_completed_tasks()
            
            # 强制垃圾回收
            collected = gc.collect()
            logger.info(f"垃圾回收清理了 {collected} 个对象")
            
            # 更新统计信息
            cleanup_time = time.time() - start_time
            self._stats["last_cleanup_time"] = datetime.now().isoformat()
            logger.info(f"定期清理完成，耗时 {cleanup_time:.2f} 秒")
            
        except Exception as e:
            logger.error(f"定期清理会话失败: {e}")
            self._stats["cleanup_errors"] += 1
        finally:
            if not self._shutdown_flag:
                self._start_cleanup_timer()
    
    def _cleanup_timeout_sessions(self) -> int:
        """清理超时会话"""
        with self._lock:
            timeout_threshold = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
            sessions_to_remove = []
            
            for session_id, session_data in self.sessions.items():
                last_activity = session_data.get("last_activity")
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity)
                
                if last_activity and last_activity < timeout_threshold:
                    sessions_to_remove.append(session_id)
            
            cleaned_count = 0
            for session_id in sessions_to_remove:
                if self._delete_session_internal(session_id):
                    cleaned_count += 1
                    logger.info(f"清理超时会话: {session_id}")
            
            self._stats["timeout_cleanups"] += cleaned_count
            return cleaned_count
    
    def _force_cleanup(self) -> int:
        """强制清理 - 清理最老的会话直到内存使用降低"""
        with self._lock:
            initial_count = len(self.sessions)
            target_count = max(1, initial_count // 3)  # 清理2/3的会话
            
            # 按最后活动时间排序，清理最老的会话
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda x: x[1].get("last_activity", datetime.min)
            )
            
            cleaned_count = 0
            for session_id, _ in sessions_by_activity:
                if len(self.sessions) <= target_count:
                    break
                    
                if self._delete_session_internal(session_id):
                    cleaned_count += 1
            
            logger.warning(f"强制清理完成，清理了 {cleaned_count} 个会话")
            return cleaned_count
    
    def _aggressive_cleanup(self) -> int:
        """积极清理 - 使用更短的超时时间"""
        # 使用更短的超时时间进行清理
        short_timeout = max(5, self.cleanup_interval_minutes // 3)
        cleaned = self.cleanup_inactive_sessions(short_timeout)
        
        # 如果清理的会话不够，进一步清理
        if cleaned < 2 and len(self.sessions) > self.max_sessions // 2:
            additional_cleaned = self._cleanup_lru_sessions(2)
            cleaned += additional_cleaned
            
        return cleaned
    
    def _cleanup_lru_sessions(self, count: int) -> int:
        """清理最近最少使用的会话"""
        with self._lock:
            if len(self.sessions) <= count:
                return 0
            
            # OrderedDict的前面是最老的
            sessions_to_remove = list(self.sessions.keys())[:count]
            
            cleaned_count = 0
            for session_id in sessions_to_remove:
                if self._delete_session_internal(session_id):
                    cleaned_count += 1
                    logger.info(f"LRU清理会话: {session_id}")
            
            return cleaned_count
    
    def _cleanup_orphaned_workspaces(self):
        """清理孤立的工作空间目录"""
        try:
            workspace_base = self.get_workspace_base_dir()
            if not os.path.exists(workspace_base):
                return
                
            # 获取所有活跃会话的工作空间路径
            active_workspaces = set()
            with self._lock:
                for session_data in self.sessions.values():
                    workspace_path = session_data.get("workspace_path")
                    if workspace_path:
                        active_workspaces.add(os.path.basename(workspace_path))
            
            # 扫描工作空间目录
            orphaned_count = 0
            for item in os.listdir(workspace_base):
                item_path = os.path.join(workspace_base, item)
                if os.path.isdir(item_path) and item not in active_workspaces:
                    # 检查目录的修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                    if mtime < datetime.now() - timedelta(hours=2):  # 2小时前的目录
                        try:
                            shutil.rmtree(item_path)
                            orphaned_count += 1
                            logger.info(f"清理孤立工作空间: {item_path}")
                        except Exception as e:
                            logger.error(f"清理孤立工作空间失败 {item_path}: {e}")
            
            if orphaned_count > 0:
                self._stats["workspace_cleanups"] += orphaned_count
                logger.info(f"清理了 {orphaned_count} 个孤立工作空间")
                
        except Exception as e:
            logger.error(f"清理孤立工作空间失败: {e}")
    
    def _cleanup_completed_tasks(self):
        """清理已完成的异步任务"""
        completed_tasks = [task for task in self._active_tasks if task.done()]
        for task in completed_tasks:
            self._active_tasks.discard(task)
            try:
                # 获取任务结果以清理异常
                task.result()
            except Exception as e:
                logger.debug(f"异步任务异常: {e}")
    
    def _enforce_session_limit(self):
        """强制执行会话数量限制"""
        with self._lock:
            if len(self.sessions) >= self.max_sessions:
                excess_count = len(self.sessions) - self.max_sessions + 1
                cleaned = self._cleanup_lru_sessions(excess_count)
                logger.info(f"会话数量超限，清理了 {cleaned} 个最老会话")
        
    def create_session(self, session_id: str = None, custom_config: Dict = None) -> str:
        """创建新会话，支持自定义配置和会话数量限制"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        with self._lock:
            # 检查会话数量限制
            self._enforce_session_limit()
            
            if session_id in self.sessions:
                logger.warning(f"Session {session_id} already exists")
                # 移动到末尾（LRU更新）
                self.sessions.move_to_end(session_id)
                self.sessions[session_id]["last_activity"] = datetime.now()
                return session_id
    
            try:
                conversation_id = str(uuid.uuid4())
                created_at = datetime.now()
                
                # 提取元信息（不要混入 TaskWeaver 的 session_config）
                meta = {}
                if custom_config:
                    # 拷贝避免修改调用方传入对象
                    cfg_copy = copy.deepcopy(custom_config)
                    for k in ["client_ip", "user_agent", "is_admin_session", "created_by"]:
                        if k in cfg_copy:
                            meta[k] = cfg_copy.pop(k)
                    custom_config = cfg_copy  # 剩余才是真正的 TaskWeaver 配置

                # 合并默认配置和自定义配置
                session_config = copy.deepcopy(self.default_config)
                if custom_config:
                    session_config.update(custom_config)
    
                session_data = {
                    "conversation_id": conversation_id,
                    "taskweaver_session": None,
                    "taskweaver_app": None,
                    "messages": [],
                    "created_at": created_at.isoformat(),
                    "last_activity": created_at,
                    "status": "active",
                    "client_ip": meta.get("client_ip"),
                    "user_agent": meta.get("user_agent"),
                    "is_admin_session": bool(meta.get("is_admin_session", False)),
                    "created_by": meta.get("created_by"),
                    "last_heartbeat": created_at,
                    "workspace_path": None,
                    "session_config": session_config,
                    "memory_usage": 0,  # 跟踪内存使用
                    "resource_count": 0,  # 跟踪资源数量
                    "cleanup_attempts": 0,  # 跟踪清理尝试次数
                    "last_cleanup_attempt": None
                }
                
                self.sessions[session_id] = session_data
                self.conversation_ids[session_id] = conversation_id
                
                self._stats["total_created"] += 1
                logger.info(f"Created session: {session_id} with conversation: {conversation_id}")
                return session_id
                
            except Exception as e:
                logger.error(f"Failed to create session {session_id}: {e}")
                raise

    def update_session_config(self, session_id: str, new_config: Dict) -> bool:
        """更新会话配置并重建TaskWeaver会话"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session_data = self.sessions[session_id]
            
            # 更新配置
            session_data["session_config"].update(new_config)
            
            # 清理现有的TaskWeaver会话，强制重建
            self._cleanup_taskweaver_session(session_data)
            
            logger.info(f"会话 {session_id} 配置已更新，将在下次使用时重建TaskWeaver会话")
            return True
    
    def get_session_config(self, session_id: str) -> Optional[Dict]:
        """获取会话的配置"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            return copy.deepcopy(self.sessions[session_id].get("session_config", {}))
    
    def create_taskweaver_app_for_session(self, session_id: str, base_taskweaver_app) -> Optional[object]:
        """为会话创建专用的TaskWeaver应用实例"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session_data = self.sessions[session_id]
            
            try:
                # 创建会话专用的TaskWeaver应用
                session_data["taskweaver_app"] = base_taskweaver_app
                return base_taskweaver_app
                
            except Exception as e:
                logger.error(f"Failed to create TaskWeaver app for session {session_id}: {e}")
                return None

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取指定的会话（LRU更新）"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            # 更新最后活动时间和LRU位置
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions.move_to_end(session_id)  # 移动到末尾
            return copy.deepcopy(self.sessions[session_id])

    def get_or_create_session(self, session_id: str, custom_config: Dict = None) -> Dict:
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session["last_activity"] = datetime.now()
                self.sessions.move_to_end(session_id)
                return copy.deepcopy(session)

            self.create_session(session_id, custom_config)
            return copy.deepcopy(self.sessions.get(session_id))

    def update_heartbeat(self, session_id: str) -> bool:
        """更新会话的心跳时间"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_heartbeat"] = datetime.now()
                self.sessions[session_id]["last_activity"] = datetime.now()
                self.sessions.move_to_end(session_id)  # LRU更新
                logger.debug(f"Heartbeat updated for session: {session_id}")
                return True
            return False

    def _cleanup_taskweaver_session(self, session_data: Dict) -> None:
        """增强的TaskWeaver会话资源清理"""
        try:
            session_data["cleanup_attempts"] = session_data.get("cleanup_attempts", 0) + 1
            session_data["last_cleanup_attempt"] = datetime.now().isoformat()
            
            taskweaver_session = session_data.get("taskweaver_session")
            taskweaver_app = session_data.get("taskweaver_app")
            
            # 清理TaskWeaver会话
            if taskweaver_session:
                try:
                    # 获取工作空间路径
                    if hasattr(taskweaver_session, 'execution_cwd'):
                        workspace_path = taskweaver_session.execution_cwd
                        session_data["workspace_path"] = workspace_path
                        self._workspace_paths.add(workspace_path)
                    
                    # 停止所有正在运行的任务
                    if hasattr(taskweaver_session, 'stop_all_tasks'):
                        taskweaver_session.stop_all_tasks()
                    
                    # 清理会话状态
                    if hasattr(taskweaver_session, 'clear_state'):
                        taskweaver_session.clear_state()
                    
                    # 关闭会话
                    if hasattr(taskweaver_session, 'stop'):
                        taskweaver_session.stop()
                    elif hasattr(taskweaver_session, 'close'):
                        taskweaver_session.close()
                    
                    # 清理会话内部状态
                    if hasattr(taskweaver_session, 'clear'):
                        taskweaver_session.clear()
                    
                    # 清理内存中的对话历史
                    if hasattr(taskweaver_session, 'conversation_history'):
                        taskweaver_session.conversation_history.clear()
                    
                    # 清理执行上下文
                    if hasattr(taskweaver_session, 'execution_context'):
                        taskweaver_session.execution_context = None
                        
                except Exception as session_cleanup_error:
                    logger.error(f"清理TaskWeaver会话失败: {session_cleanup_error}")
            
            # 清理TaskWeaver应用实例
            if taskweaver_app:
                try:
                    # 停止应用级别的服务
                    if hasattr(taskweaver_app, 'stop_services'):
                        taskweaver_app.stop_services()
                    
                    # 清理应用缓存
                    if hasattr(taskweaver_app, 'clear_cache'):
                        taskweaver_app.clear_cache()
                    
                    # 关闭应用
                    if hasattr(taskweaver_app, 'cleanup'):
                        taskweaver_app.cleanup()
                    elif hasattr(taskweaver_app, 'close'):
                        taskweaver_app.close()
                    elif hasattr(taskweaver_app, 'shutdown'):
                        taskweaver_app.shutdown()
                    
                    # 清理应用级别的资源
                    if hasattr(taskweaver_app, 'release_resources'):
                        taskweaver_app.release_resources()
                        
                except Exception as app_cleanup_error:
                    logger.error(f"清理TaskWeaver应用失败: {app_cleanup_error}")
            
            # 清空引用并重置计数器
            session_data["taskweaver_session"] = None
            session_data["taskweaver_app"] = None
            session_data["memory_usage"] = 0
            session_data["resource_count"] = 0
            
            # 显式删除对象引用
            if taskweaver_session:
                del taskweaver_session
            if taskweaver_app:
                del taskweaver_app
            
            # 强制垃圾回收
            gc.collect()
            
            logger.info("TaskWeaver会话和应用已彻底清理")
        except Exception as e:
            logger.error(f"清理TaskWeaver会话失败: {e}")
            session_data["cleanup_attempts"] = session_data.get("cleanup_attempts", 0) + 1
    
    def _cleanup_workspace(self, workspace_path: str) -> None:
        """增强的工作空间清理"""
        try:
            if not workspace_path or not os.path.exists(workspace_path):
                return
                
            # 安全路径检查
            safe_base = os.path.abspath(self.get_workspace_base_dir())
            abs_path = os.path.abspath(workspace_path)
            if not abs_path.startswith(safe_base):
                logger.warning(f"拒绝删除非工作空间路径: {workspace_path}")
                return

            # 强制关闭可能打开的文件句柄
            try:
                import psutil
                current_process = psutil.Process()
                for file_info in current_process.open_files():
                    if abs_path in file_info.path:
                        logger.warning(f"检测到打开的文件: {file_info.path}")
            except Exception:
                pass
            
            # 递归删除目录
            def remove_readonly(func, path, _):
                """处理只读文件的删除"""
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            
            shutil.rmtree(abs_path, onerror=remove_readonly)
            
            # 从跟踪集合中移除
            self._workspace_paths.discard(workspace_path)
            
            logger.info(f"已删除工作空间目录: {abs_path}")
            
        except Exception as e:
            logger.error(f"清理工作空间失败 {workspace_path}: {e}")
    
    def get_workspace_base_dir(self) -> str:
        """获取工作空间基础目录"""
        try:
            from config import get_config
            config = get_config()
            return os.path.join(config.taskweaver_project_path, "workspace", "sessions")
        except Exception:
            # fallback路径
            return os.path.join(os.getcwd(), "project", "workspace", "sessions")

    def _delete_session_internal(self, session_id: str) -> bool:
        """内部会话删除方法（不加锁）"""
        if session_id not in self.sessions:
            return False
        
        try:
            session_data = self.sessions[session_id]
            
            # 清理TaskWeaver会话
            self._cleanup_taskweaver_session(session_data)
            
            # 清理工作空间
            workspace_path = session_data.get("workspace_path")
            if workspace_path:
                self._cleanup_workspace(workspace_path)
            
            # 从字典中移除
            del self.sessions[session_id]
            if session_id in self.conversation_ids:
                del self.conversation_ids[session_id]
            
            self._stats["total_cleaned"] += 1
            logger.info(f"Session {session_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def delete_session(self, session_id: str, chat_service=None) -> bool:
        """删除指定的会话（增强清理）"""
        with self._lock:
            return self._delete_session_internal(session_id)

    def cleanup_inactive_sessions(self, inactive_minutes: int = 60) -> int:
        """清理非活跃会话"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=inactive_minutes)
            sessions_to_remove = []
            
            for session_id, session_data in self.sessions.items():
                last_activity = session_data.get("last_activity")
                if isinstance(last_activity, str):
                    try:
                        last_activity = datetime.fromisoformat(last_activity)
                    except ValueError:
                        # 如果解析失败，认为是很久以前的会话
                        last_activity = datetime.min
                
                if last_activity and last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            cleaned_count = 0
            for session_id in sessions_to_remove:
                if self._delete_session_internal(session_id):
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} inactive sessions")
            
            return cleaned_count

    def get_session_stats(self) -> Dict:
        """获取会话管理统计信息"""
        with self._lock:
            memory_info = self._memory_monitor.get_memory_usage()
            
            return {
                "active_sessions": len(self.sessions),
                "max_sessions": self.max_sessions,
                "memory_usage": memory_info,
                "open_files": self._memory_monitor.get_process_open_files(),
                "workspace_paths_tracked": len(self._workspace_paths),
                "active_tasks": len(self._active_tasks),
                "stats": copy.deepcopy(self._stats),
                "cleanup_interval_minutes": self.cleanup_interval_minutes,
                "session_timeout_minutes": self.session_timeout_minutes
            }

    def shutdown(self):
        """优雅关闭会话管理器"""
        logger.info("开始关闭SessionManager...")
        
        self._shutdown_flag = True
        
        # 停止定时器
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
        
        # 取消所有活跃任务
        for task in list(self._active_tasks):
            if not task.done():
                task.cancel()
        
        # 清理所有会话
        with self._lock:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                try:
                    self._delete_session_internal(session_id)
                except Exception as e:
                    logger.error(f"关闭时清理会话 {session_id} 失败: {e}")
        
        # 清理所有跟踪的工作空间
        for workspace_path in list(self._workspace_paths):
            try:
                self._cleanup_workspace(workspace_path)
            except Exception as e:
                logger.error(f"关闭时清理工作空间 {workspace_path} 失败: {e}")
        
        # 最终垃圾回收
        gc.collect()
        
        logger.info(f"SessionManager已关闭，清理了 {self._stats['total_cleaned']} 个会话")

    def __del__(self):
        """析构函数确保资源清理"""
        try:
            if not self._shutdown_flag:
                self.shutdown()
        except Exception:
            pass  # 析构函数中不应抛出异常

    def get_sessions_by_ip(self, client_ip: str, only_active: bool = True) -> List[str]:
        """
        根据客户端 IP 返回会话 ID 列表。
        - only_active=True 时，仅统计 status == 'active' 的会话。
        """
        if not client_ip:
            return []
        with self._lock:
            result = []
            for sid, data in self.sessions.items():
                if data.get("client_ip") == client_ip:
                    if (not only_active) or (data.get("status") == "active"):
                        result.append(sid)
            return result