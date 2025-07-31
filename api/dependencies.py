import asyncio
import threading
from typing import Optional
from session_manager import SessionManager
from services.chat_service import ChatService
from taskweaver.app.app import TaskWeaverApp
from db_connection import create_db_connection
from config import get_config
from services.sse_service import SSEService
import os
import logging

logger = logging.getLogger(__name__)

# 全局实例缓存（线程安全的单例模式）
_session_manager: Optional[SessionManager] = None
_taskweaver_app: Optional[TaskWeaverApp] = None
_chat_service: Optional[ChatService] = None
_sse_service: Optional[SSEService] = None
_config = None
_lock = threading.Lock()

class DependencyError(Exception):
    """依赖注入相关错误"""
    pass

def get_session_manager() -> SessionManager:
    """获取会话管理器实例（线程安全）"""
    global _session_manager
    if _session_manager is None:
        with _lock:
            if _session_manager is None:
                _session_manager = SessionManager()
                logger.info("SessionManager initialized")
    return _session_manager

def get_taskweaver_app() -> TaskWeaverApp:
    """获取TaskWeaver应用实例（线程安全）"""
    global _taskweaver_app
    if _taskweaver_app is None:
        with _lock:
            if _taskweaver_app is None:
                try:
                    project_path = os.path.join(os.path.dirname(__file__), "project")
                    if not os.path.exists(project_path):
                        raise DependencyError(f"TaskWeaver项目路径不存在: {project_path}")
                    
                    _taskweaver_app = TaskWeaverApp(app_dir=project_path, use_local_uri=True)
                    logger.info("TaskWeaver应用初始化成功")
                except Exception as e:
                    logger.error(f"TaskWeaver初始化失败: {e}")
                    raise DependencyError(f"TaskWeaver初始化失败: {e}")
    return _taskweaver_app

def get_db_connection():
    """获取数据库连接（GaussDB）"""
    try:
        return create_db_connection()
    except Exception as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise DependencyError(f"数据库连接失败: {e}")

def get_sse_service() -> SSEService:
    """获取已初始化的SSE服务实例"""
    if _sse_service is None:
        raise DependencyError("SSEService尚未初始化。请在应用启动时进行配置。")
    return _sse_service

def set_sse_service(svc: SSEService):
    """设置SSE服务实例（线程安全）"""
    global _sse_service
    with _lock:
        _sse_service = svc
        logger.info("SSE服务实例已设置")

def get_chat_service() -> ChatService:
    """获取聊天服务实例（线程安全）"""
    global _chat_service
    if _chat_service is None:
        with _lock:
            if _chat_service is None:
                try:
                    _chat_service = ChatService(
                        session_manager=get_session_manager(),
                        taskweaver_app=get_taskweaver_app(),
                        sse_service=get_sse_service()
                    )
                    logger.info("ChatService initialized")
                except Exception as e:
                    logger.error(f"ChatService初始化失败: {e}")
                    raise DependencyError(f"ChatService初始化失败: {e}")
    return _chat_service

def get_app_config():
    """获取应用配置（线程安全）"""
    global _config
    if _config is None:
        with _lock:
            if _config is None:
                _config = get_config()
    return _config

async def cleanup_dependencies():
    """清理所有资源"""
    global _sse_service, _chat_service, _taskweaver_app, _session_manager
    
    logger.info("开始清理依赖资源...")
    
    # 清理聊天服务
    if _chat_service:
        try:
            if hasattr(_chat_service, 'shutdown'):
                _chat_service.shutdown()
            logger.info("ChatService已关闭")
        except Exception as e:
            logger.error(f"关闭ChatService失败: {e}")
    
    # 清理SSE服务
    if _sse_service:
        try:
            await _sse_service.cleanup()
            logger.info("SSE服务已清理")
        except Exception as e:
            logger.error(f"清理SSE服务失败: {e}")
    
    # 清理TaskWeaver应用
    if _taskweaver_app:
        try:
            if hasattr(_taskweaver_app, 'stop'):
                _taskweaver_app.stop()
            logger.info("TaskWeaver应用已停止")
        except Exception as e:
            logger.error(f"停止TaskWeaver应用失败: {e}")
    
    # 清理会话管理器
    if _session_manager:
        try:
            if hasattr(_session_manager, 'clear_all_sessions'):
                _session_manager.clear_all_sessions()
            logger.info("会话管理器已清理")
        except Exception as e:
            logger.error(f"清理会话管理器失败: {e}")
    
    logger.info("依赖资源清理完成")
