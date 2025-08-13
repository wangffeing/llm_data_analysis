import logging
import uuid
import threading
import shutil
import os
import psutil
import gc
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from taskweaver.session.session import Session
from taskweaver.app.app import TaskWeaverApp
import copy
from collections import OrderedDict

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """内存监控器"""
    
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
                "available_mb": psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0,
                "available_mb": 0
            }
    
    @staticmethod
    def is_memory_pressure(threshold_percent: float = 80.0) -> bool:
        """检查是否存在内存压力"""
        memory_info = MemoryMonitor.get_memory_usage()
        return memory_info["percent"] > threshold_percent

class SessionManager:
    def __init__(self,
                 cleanup_interval_minutes: int = 60,  # 缩短清理间隔
                 max_sessions: int = 10,  # 最大会话数限制
                 memory_threshold_percent: float = 80.0,  # 内存压力阈值
                 force_cleanup_threshold_percent: float = 90.0):  # 强制清理阈值
        
        self.sessions: OrderedDict[str, Dict] = OrderedDict()  # 使用OrderedDict支持LRU
        self.conversation_ids: Dict[str, str] = {}
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.max_sessions = max_sessions
        self.memory_threshold_percent = memory_threshold_percent
        self.force_cleanup_threshold_percent = force_cleanup_threshold_percent
        
        self._lock = threading.RLock()
        self._cleanup_timer: Optional[threading.Timer] = None
        self._memory_monitor = MemoryMonitor()
        
        # 统计信息
        self._stats = {
            "total_created": 0,
            "total_cleaned": 0,
            "memory_cleanups": 0,
            "force_cleanups": 0
        }
        
        self._start_cleanup_timer()
        
        # 默认配置模板
        self.default_config = {
            "llm.api_type": "qwen",
            "llm.model": "qwen3-14b",
            "execution_service.kernel_mode": "local",
            "code_generator.enable_auto_plugin_selection": "false",
            "code_generator.allowed_plugins": ["sql_pull_data"],  # 添加插件过滤配置
            "code_interpreter.code_verification_on": "false",
            "code_interpreter.allowed_modules": ["pandas", "matplotlib", "numpy", "sklearn", "scipy", "seaborn", "datetime", "typing", "json"],
            "logging.log_file": "taskweaver.log",
            "logging.log_folder": "logs",
            "logging.log_level": "WARNING",
            "planner.prompt_compression": "true",
            "code_generator.prompt_compression": "true",
            "session.max_internal_chat_round_num": 20,
            "session.roles": ["planner", "code_interpreter", "recepta"]
        }
        
    def _start_cleanup_timer(self):
        """启动定时清理任务"""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
        
        self._cleanup_timer = threading.Timer(
            self.cleanup_interval_minutes * 60,
            self._periodic_cleanup
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
        
    def _periodic_cleanup(self):
        """定期清理非活跃会话和内存监控"""
        try:
            # 检查内存使用情况
            memory_info = self._memory_monitor.get_memory_usage()
            logger.info(f"内存使用情况: {memory_info}")
            
            # 根据内存压力调整清理策略
            if memory_info["percent"] > self.force_cleanup_threshold_percent:
                logger.warning(f"内存使用率过高 ({memory_info['percent']:.1f}%)，执行强制清理")
                self._force_cleanup()
                self._stats["force_cleanups"] += 1
            elif memory_info["percent"] > self.memory_threshold_percent:
                logger.info(f"内存压力较大 ({memory_info['percent']:.1f}%)，执行积极清理")
                self._aggressive_cleanup()
                self._stats["memory_cleanups"] += 1
            else:
                # 正常清理
                self.cleanup_inactive_sessions(self.cleanup_interval_minutes)
            
            # 强制垃圾回收
            gc.collect()
            
        except Exception as e:
            logger.error(f"定期清理会话失败: {e}")
        finally:
            self._start_cleanup_timer()
    
    def _force_cleanup(self):
        """强制清理 - 清理最老的会话直到内存使用降低"""
        with self._lock:
            initial_count = len(self.sessions)
            target_count = max(1, initial_count // 2)  # 清理一半会话
            
            # 按最后活动时间排序，清理最老的会话
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda x: x[1].get("last_activity", datetime.min)
            )
            
            cleaned_count = 0
            for session_id, _ in sessions_by_activity:
                if len(self.sessions) <= target_count:
                    break
                    
                self.delete_session(session_id)
                cleaned_count += 1
            
            logger.warning(f"强制清理完成，清理了 {cleaned_count} 个会话")
            self._stats["total_cleaned"] += cleaned_count
    
    def _aggressive_cleanup(self):
        """积极清理 - 使用更短的超时时间"""
        # 使用更短的超时时间进行清理
        short_timeout = max(5, self.cleanup_interval_minutes // 2)
        cleaned = self.cleanup_inactive_sessions(short_timeout)
        
        # 如果清理的会话不够，进一步清理
        if cleaned < 3 and len(self.sessions) > self.max_sessions // 2:
            self._cleanup_lru_sessions(3)
    
    def _cleanup_lru_sessions(self, count: int):
        """清理最近最少使用的会话"""
        with self._lock:
            if len(self.sessions) <= count:
                return
            
            # OrderedDict的前面是最老的
            sessions_to_remove = list(self.sessions.keys())[:count]
            
            for session_id in sessions_to_remove:
                self.delete_session(session_id)
                logger.info(f"LRU清理会话: {session_id}")
            
            self._stats["total_cleaned"] += len(sessions_to_remove)
    
    def _enforce_session_limit(self):
        """强制执行会话数量限制"""
        with self._lock:
            if len(self.sessions) >= self.max_sessions:
                excess_count = len(self.sessions) - self.max_sessions + 1
                self._cleanup_lru_sessions(excess_count)
                logger.info(f"会话数量超限，清理了 {excess_count} 个最老会话")
        
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
                    "resource_count": 0  # 跟踪资源数量
                }
                
                self.sessions[session_id] = session_data
                self.conversation_ids[session_id] = conversation_id
                
                # 移除弱引用相关代码，因为dict不支持弱引用
                # self._session_refs[session_id] = weakref.ref(session_data)  # 删除这行
                
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
            if "taskweaver_session" in session_data:
                try:
                    taskweaver_session = session_data["taskweaver_session"]
                    if taskweaver_session and hasattr(taskweaver_session, 'stop'):
                        taskweaver_session.stop()
                except Exception as e:
                    logger.error(f"停止TaskWeaver会话失败: {e}")
                
                session_data["taskweaver_session"] = None
                session_data["taskweaver_app"] = None
            
            logger.info(f"会话 {session_id} 配置已更新，将在下次使用时重建TaskWeaver会话")
            return True
    
    def get_session_config(self, session_id: str) -> Optional[Dict]:
        """获取会话的配置"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            return self.sessions[session_id].get("session_config", {})
    
    def create_taskweaver_app_for_session(self, session_id: str, base_taskweaver_app) -> Optional[object]:
        """为会话创建专用的TaskWeaver应用实例"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session_data = self.sessions[session_id]
            session_config = session_data.get("session_config", {})
            
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
            return self.sessions[session_id]

    def get_or_create_session(self, session_id: str, custom_config: Dict = None) -> Dict:
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session["last_activity"] = datetime.now()
                return session

            self.create_session(session_id, custom_config)
            return self.sessions.get(session_id)

    def update_heartbeat(self, session_id: str) -> bool:
        """更新会话的心跳时间"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_heartbeat"] = datetime.now()
                logger.debug(f"Heartbeat updated for session: {session_id}")
                return True
            return False

    def _cleanup_taskweaver_session(self, session_data: Dict) -> None:
        """增强的TaskWeaver会话资源清理"""
        try:
            taskweaver_session = session_data.get("taskweaver_session")
            taskweaver_app = session_data.get("taskweaver_app")
            
            if taskweaver_session:
                # 获取工作空间路径
                if hasattr(taskweaver_session, 'execution_cwd'):
                    workspace_path = taskweaver_session.execution_cwd
                    session_data["workspace_path"] = workspace_path
                
                # 停止TaskWeaver会话
                try:
                    if hasattr(taskweaver_session, 'stop'):
                        taskweaver_session.stop()
                    elif hasattr(taskweaver_session, 'close'):
                        taskweaver_session.close()
                    
                    # 清理会话内部状态
                    if hasattr(taskweaver_session, 'clear'):
                        taskweaver_session.clear()
                        
                except Exception as session_cleanup_error:
                    logger.error(f"清理TaskWeaver会话失败: {session_cleanup_error}")
            
            # 清理TaskWeaver应用实例
            if taskweaver_app:
                try:
                    if hasattr(taskweaver_app, 'cleanup'):
                        taskweaver_app.cleanup()
                    elif hasattr(taskweaver_app, 'close'):
                        taskweaver_app.close()
                    elif hasattr(taskweaver_app, 'shutdown'):
                        taskweaver_app.shutdown()
                        
                    # 清理应用缓存
                    if hasattr(taskweaver_app, 'clear_cache'):
                        taskweaver_app.clear_cache()
                        
                except Exception as app_cleanup_error:
                    logger.error(f"清理TaskWeaver应用失败: {app_cleanup_error}")
            
            # 清空引用
            session_data["taskweaver_session"] = None
            session_data["taskweaver_app"] = None
            session_data["memory_usage"] = 0
            session_data["resource_count"] = 0
            
            # 强制垃圾回收
            del taskweaver_session, taskweaver_app
            gc.collect()
            
            logger.info("TaskWeaver会话和应用已彻底清理")
        except Exception as e:
            logger.error(f"清理TaskWeaver会话失败: {e}")
    
    def _cleanup_workspace(self, workspace_path: str) -> None:
        """删除整个工作空间目录（含安全路径检查）"""
        try:
            if workspace_path and os.path.exists(workspace_path):
                # 修正安全路径检查 - 使用正确的基础路径
                safe_base = os.path.abspath(self.get_workspace_base_dir())
                abs_path = os.path.abspath(workspace_path)
                if not abs_path.startswith(safe_base):
                    logger.warning(f"拒绝删除非工作空间路径: {workspace_path}")
                    return

                # 支持模式匹配删除
                if "*" in workspace_path or "session_" in workspace_path:
                    import glob
                    for path in glob.glob(workspace_path):
                        if os.path.exists(path):
                            shutil.rmtree(path)
                            logger.info(f"已删除工作空间目录: {path}")
                else:
                    shutil.rmtree(abs_path)
                    logger.info(f"已删除工作空间目录: {abs_path}")
            else:
                logger.debug(f"工作空间目录不存在或路径无效: {workspace_path}")
        except Exception as e:
            logger.error(f"清理工作空间失败 {workspace_path}: {e}")
    
    def get_workspace_base_dir(self) -> str:
        """获取工作空间基础目录"""
        from config import get_config
        config = get_config()
        return os.path.join(config.taskweaver_project_path, "workspace", "sessions")

    def delete_session(self, session_id: str, chat_service=None) -> bool:
        """删除指定的会话（增强清理）"""
        with self._lock:
            if session_id not in self.sessions:
                logger.warning(f"Session {session_id} not found for deletion")
                return False
    
            try:
                session_data = self.sessions[session_id]
                
                # 先取消活跃任务（如果提供了chat_service）
                if chat_service:
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(chat_service.cancel_task(session_id))
                        else:
                            asyncio.run(chat_service.cancel_task(session_id))
                    except Exception as cancel_error:
                        logger.error(f"取消会话任务失败: {cancel_error}")
                
                # 清理TaskWeaver会话
                self._cleanup_taskweaver_session(session_data)
                
                # 清理工作空间
                workspace_path = session_data.get("workspace_path")
                if workspace_path:
                    self._cleanup_workspace(workspace_path)
                
                # 删除会话记录
                del self.sessions[session_id]
                if session_id in self.conversation_ids:
                    del self.conversation_ids[session_id]

                logger.info(f"Deleted session: {session_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self.sessions.keys())

    def clear_all_sessions(self) -> None:
        with self._lock:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                self.delete_session(session_id)
            
            logger.info(f"清理了 {len(session_ids)} 个会话")

    def get_conversation_id(self, session_id: str) -> str:
        with self._lock:
            return self.conversation_ids.get(session_id, "")

    def cleanup_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        activity_cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
        heartbeat_cutoff = datetime.now() - timedelta(minutes=2)
        inactive_sessions = []

        with self._lock:
            for sid, data in list(self.sessions.items()):
                last_activity = data.get("last_activity")
                last_heartbeat = data.get("last_heartbeat")

                # 检查活动时间
                is_inactive = False
                if isinstance(last_activity, str):
                    try:
                        last_activity = datetime.fromisoformat(last_activity)
                    except ValueError:
                        last_activity = None
                
                if last_activity and last_activity < activity_cutoff:
                    is_inactive = True

                # 检查心跳时间
                is_heartbeat_lost = False
                if not is_inactive:
                    if isinstance(last_heartbeat, str):
                        try:
                            last_heartbeat = datetime.fromisoformat(last_heartbeat)
                        except ValueError:
                            last_heartbeat = None
                    
                    if last_heartbeat and last_heartbeat < heartbeat_cutoff:
                        is_heartbeat_lost = True

                if is_inactive or is_heartbeat_lost:
                    logger.info(
                        f"将清理会话 {sid}: "
                        f"inactive={is_inactive}, heartbeat_lost={is_heartbeat_lost}"
                    )
                    inactive_sessions.append(sid)

            for session_id in inactive_sessions:
                self.delete_session(session_id)

        cleaned_count = len(inactive_sessions)
        self._stats["total_cleaned"] += cleaned_count
        logger.info(f"清理了 {cleaned_count} 个非活跃会话")
        return cleaned_count

    def get_session_message_history(self, session_id: str) -> List[Dict]:
        with self._lock:
            session_data = self.sessions.get(session_id)
            if session_data:
                return session_data.get("messages", [])
            return []

    def get_session_stats(self) -> Dict:
        with self._lock:
            total_sessions = len(self.sessions)
            active_sessions = sum(1 for s in self.sessions.values() if s.get("status") == "active")
            memory_info = self._memory_monitor.get_memory_usage()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "cleanup_interval_minutes": self.cleanup_interval_minutes,
                "max_sessions": self.max_sessions,
                "memory_usage": memory_info,
                "cleanup_stats": self._stats
            }

    def force_memory_cleanup(self) -> Dict:
        """手动触发内存清理"""
        try:
            before_memory = self._memory_monitor.get_memory_usage()
            
            # 执行强制清理
            self._force_cleanup()
            
            # 强制垃圾回收
            import gc
            collected = gc.collect()
            
            after_memory = self._memory_monitor.get_memory_usage()
            
            return {
                "before_memory": before_memory,
                "after_memory": after_memory,
                "objects_collected": collected,
                "sessions_cleaned": self._stats["total_cleaned"]
            }
        except Exception as e:
            logger.error(f"手动内存清理失败: {e}")
            return {"error": str(e)}

    def shutdown(self) -> None:
        """关闭SessionManager并清理所有资源"""
        logger.info("开始关闭SessionManager...")
        
        # 取消定时器
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
        
        # 清理所有会话
        self.clear_all_sessions()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        logger.info("SessionManager已关闭")
    
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