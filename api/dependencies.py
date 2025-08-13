import threading
from typing import Optional
from session_manager import SessionManager
from services.chat_service import ChatService
from services.sse_service import SSEService
from taskweaver.app.app import TaskWeaverApp
from config import Config
import logging
import atexit
import asyncio

logger = logging.getLogger(__name__)

# 全局实例
_session_manager: Optional[SessionManager] = None
_chat_service: Optional[ChatService] = None
_sse_service: Optional[SSEService] = None
_taskweaver_app: Optional[TaskWeaverApp] = None
_db_connection = None
_initialization_lock = threading.Lock()
_shutdown_registered = False

def get_session_manager() -> SessionManager:
    """获取SessionManager单例实例"""
    global _session_manager
    if _session_manager is None:
        with _initialization_lock:
            if _session_manager is None:
                _session_manager = SessionManager()
                logger.info("SessionManager实例已创建")
    return _session_manager

def get_taskweaver_app() -> TaskWeaverApp:
    # 获取TaskWeaverApp单例实例
    global _taskweaver_app
    if _taskweaver_app is None:
        with _initialization_lock:
            if _taskweaver_app is None:
                config = Config()
                _taskweaver_app = TaskWeaverApp(
                    app_dir=config.taskweaver_project_path,
                    log_level=config.log_level or "INFO"
                )
                logger.info("TaskWeaverApp实例已创建")
    return _taskweaver_app

def get_sse_service() -> SSEService:
    """获取SSEService单例实例"""
    global _sse_service
    if _sse_service is None:
        with _initialization_lock:
            if _sse_service is None:
                _sse_service = SSEService()
                logger.info("SSEService实例已创建")
    return _sse_service

def set_sse_service(sse_service: SSEService):
    """设置SSE服务实例（用于main_sse.py中的配置）"""
    global _sse_service
    _sse_service = sse_service

def get_chat_service() -> ChatService:
    """获取ChatService单例实例"""
    global _chat_service
    if _chat_service is None:
        with _initialization_lock:
            if _chat_service is None:
                _chat_service = ChatService(
                    taskweaver_app=get_taskweaver_app(),
                    session_manager=get_session_manager(),
                    sse_service=get_sse_service()
                )
                logger.info("ChatService实例已创建")
    return _chat_service

def get_db_connection():
    """获取数据库连接（兼容性接口）"""
    global _db_connection
    if _db_connection is None:
        from db_connection import get_db_manager
        _db_connection = get_db_manager()
    return _db_connection

async def cleanup_dependencies():
    """异步资源清理函数（用于FastAPI lifespan）"""
    global _sse_service, _chat_service, _taskweaver_app, _session_manager, _db_connection
    
    logger.info("开始清理应用资源...")
    
    cleanup_stats = {
        "sse_service": False,
        "chat_service": False,
        "session_manager": False,
        "taskweaver_app": False,
        "db_connection": False
    }
    
    try:
        # 1. 首先停止SSE服务
        if _sse_service:
            try:
                if hasattr(_sse_service, 'cleanup'):
                    await _sse_service.cleanup()
                elif hasattr(_sse_service, 'shutdown'):
                    if asyncio.iscoroutinefunction(_sse_service.shutdown):
                        await _sse_service.shutdown()
                    else:
                        _sse_service.shutdown()
                cleanup_stats["sse_service"] = True
                logger.info("SSEService已清理")
            except Exception as e:
                logger.error(f"清理SSEService时出错: {e}")
            finally:
                _sse_service = None

        # 2. 清理ChatService
        if _chat_service:
            try:
                if hasattr(_chat_service, 'shutdown'):
                    if asyncio.iscoroutinefunction(_chat_service.shutdown):
                        await _chat_service.shutdown()
                    else:
                        _chat_service.shutdown()
                elif hasattr(_chat_service, 'cleanup'):
                    if asyncio.iscoroutinefunction(_chat_service.cleanup):
                        await _chat_service.cleanup()
                    else:
                        _chat_service.cleanup()
                cleanup_stats["chat_service"] = True
                logger.info("ChatService已清理")
            except Exception as e:
                logger.error(f"清理ChatService时出错: {e}")
            finally:
                _chat_service = None

        # 3. 清理SessionManager（包含工作空间清理）
        if _session_manager:
            try:
                # 强制清理所有会话（包含TaskWeaver工作空间）
                _session_manager.shutdown()
                cleanup_stats["session_manager"] = True
                logger.info("SessionManager已清理")
            except Exception as e:
                logger.error(f"清理SessionManager时出错: {e}")
            finally:
                _session_manager = None

        # 4. 清理数据库连接
        if _db_connection:
            try:
                if hasattr(_db_connection, 'disconnect'):
                    _db_connection.disconnect()
                cleanup_stats["db_connection"] = True
                logger.info("数据库连接已清理")
            except Exception as e:
                logger.error(f"清理数据库连接时出错: {e}")
            finally:
                _db_connection = None

        # 5. 最后清理TaskWeaverApp
        if _taskweaver_app:
            try:
                # 停止所有TaskWeaver会话
                if hasattr(_taskweaver_app, 'session_manager') and _taskweaver_app.session_manager:
                    _taskweaver_app.session_manager.stop_all_sessions()
                
                # 清理应用本身
                if hasattr(_taskweaver_app, 'cleanup'):
                    _taskweaver_app.cleanup()
                elif hasattr(_taskweaver_app, 'shutdown'):
                    _taskweaver_app.shutdown()
                    
                cleanup_stats["taskweaver_app"] = True
                logger.info("TaskWeaverApp已清理")
            except Exception as e:
                logger.error(f"清理TaskWeaverApp时出错: {e}")
            finally:
                _taskweaver_app = None

        # 记录清理结果
        success_count = sum(cleanup_stats.values())
        total_count = len(cleanup_stats)
        logger.info(f"资源清理完成: {success_count}/{total_count} 个组件成功清理")
        logger.info(f"清理详情: {cleanup_stats}")
        
    except Exception as e:
        logger.error(f"资源清理过程中发生未预期错误: {e}")

def _cleanup_resources():
    """同步资源清理函数（用于atexit）"""
    try:
        # 如果在异步环境中，创建新的事件循环
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop and not loop.is_closed():
            loop.run_until_complete(cleanup_dependencies())
        else:
            # 创建新的事件循环
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(cleanup_dependencies())
            new_loop.close()
            
    except Exception as e:
        logger.error(f"atexit清理过程中发生错误: {e}")

def register_cleanup():
    """注册应用关闭时的资源清理"""
    global _shutdown_registered
    if not _shutdown_registered:
        atexit.register(_cleanup_resources)
        _shutdown_registered = True
        logger.info("资源清理函数已注册到atexit")

# 自动注册清理函数
register_cleanup()
