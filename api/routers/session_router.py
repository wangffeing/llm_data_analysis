import logging
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from dependencies import get_session_manager, get_sse_service
from session_manager import SessionManager
from services.sse_service import SSEService,SSEMessageType
from models.chat_models import SessionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create", response_model=SessionResponse)
async def create_session(
    session_manager: SessionManager = Depends(get_session_manager),
    sse_service: SSEService = Depends(get_sse_service)
):
    """创建新会话"""
    try:
        session_id = session_manager.create_session()
        session_data = session_manager.get_session(session_id)

        # 发送会话创建消息
        await sse_service.send_message(session_id, SSEMessageType.SESSION_CREATED, session_data)

        # HTTP 响应
        return SessionResponse(
            session_id=session_id,
            conversation_id=session_data["conversation_id"],
            created_at=session_data["created_at"]
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")

@router.get("/{session_id}")
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """获取会话信息"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
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