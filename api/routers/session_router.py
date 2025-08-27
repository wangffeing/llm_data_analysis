import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import Optional

from dependencies import get_session_manager, get_sse_service
from session_manager import SessionManager
from services.sse_service import SSEService, SSEMessageType
from models.chat_models import SessionResponse
from auth import verify_admin_permission_optional
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create", response_model=SessionResponse)
@rate_limit("100/minute")  # 每分钟最多5次会话创建
async def create_session(
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager),
    sse_service: SSEService = Depends(get_sse_service),
    is_admin: bool = Depends(verify_admin_permission_optional)
):
    """创建新会话 - 带权限和频率控制"""
    try:
        # 获取客户端信息用于会话安全
        client_ip = getattr(request.client, 'host', 'unknown')
        user_agent = request.headers.get('user-agent', 'unknown')
        
        # 如果不是管理员，进行额外限制
        if not is_admin:
            # 检查当前IP的会话数量
            active_sessions = session_manager.get_sessions_by_ip(client_ip)
            if len(active_sessions) >= 3:  # 非管理员最多3个活跃会话
                raise HTTPException(
                    status_code=429, 
                    detail="当前IP活跃会话数已达上限，请关闭一些会话后重试"
                )
        
        # 创建会话时传入安全信息
        session_id = session_manager.create_session(
            custom_config={
                "client_ip": client_ip,
                "user_agent": user_agent,
                "is_admin_session": is_admin,
                "created_by": "admin" if is_admin else "user"
            }
        )
        session_data = session_manager.get_session(session_id)

        # 发送会话创建消息（清理敏感信息）
        safe_session_data = {
            "session_id": session_id,
            "conversation_id": session_data["conversation_id"],
            "created_at": session_data["created_at"],
            "status": session_data["status"]
        }
        await sse_service.send_message(session_id, SSEMessageType.SESSION_CREATED, safe_session_data)

        logger.info(f"会话创建成功: {session_id}, IP: {client_ip}, 管理员: {is_admin}")

        # HTTP 响应
        return SessionResponse(
            session_id=session_id,
            conversation_id=session_data["conversation_id"],
            created_at=session_data["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")

@router.get("/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager),
    is_admin: bool = Depends(verify_admin_permission_optional)
):
    """获取会话信息 - 带访问控制"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 验证会话访问权限
        client_ip = getattr(request.client, 'host', 'unknown')
        session_ip = session_data.get("client_ip")
        
        # 如果不是管理员且IP不匹配，拒绝访问
        if not is_admin and session_ip and session_ip != client_ip:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        # 过滤敏感信息
        safe_data = {
            "session_id": session_id,
            "conversation_id": session_data["conversation_id"],
            "created_at": session_data["created_at"],
            "last_activity": session_data.get("last_activity"),
            "status": session_data.get("status"),
            "message_count": len(session_data.get("messages", []))
        }
        
        # 管理员可以看到更多信息
        if is_admin:
            safe_data.update({
                "client_ip": session_data.get("client_ip"),
                "user_agent": session_data.get("user_agent"),
                "memory_usage": session_data.get("memory_usage", 0),
                "resource_count": session_data.get("resource_count", 0)
            })
        
        return safe_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话失败")

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """删除会话"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail="删除会话失败")

@router.post("/{session_id}/heartbeat")
async def session_heartbeat(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """会话心跳检测"""
    try:
        success = session_manager.update_heartbeat(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "heartbeat_received",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"心跳更新失败 for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="心跳更新失败")