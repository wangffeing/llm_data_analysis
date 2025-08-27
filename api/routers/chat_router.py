import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from dependencies import get_chat_service, get_session_manager, get_sse_service
from services.chat_service import ChatService
from services.sse_service import SSEService
from session_manager import SessionManager
from models.chat_models import ChatMessage
from utils.input_validator import InputValidator
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stream/{session_id}")
async def stream_chat(session_id: str, sse_service: SSEService = Depends(get_sse_service)):
    """SSE聊天流"""
    return StreamingResponse(
        sse_service.add_connection(session_id),
        media_type="text/event-stream",
        headers={
            # 核心防缓冲headers
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive", 
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            "Transfer-Encoding": "chunked",  # 强制分块传输
            "Content-Encoding": "identity",  # 禁用压缩
            
            # HTTP/1.0兼容性
            "Pragma": "no-cache",
            "Expires": "0",
            
            # CORS和安全
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Expose-Headers": "*",
            
            # 代理服务器优化
            "X-Proxy-Buffering": "no",  # 禁用代理缓冲
            "X-Nginx-Buffering": "no",  # 禁用Nginx特定缓冲
        }
    )



# 修改消息发送路由
@router.post("/message/{session_id}")
@rate_limit("100/minute")  # 每分钟最多10条消息
async def send_message(
    request: Request,
    session_id: str,
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
    session_mgr: SessionManager = Depends(get_session_manager)
):
    # 验证会话ID
    session_id = InputValidator.validate_session_id(session_id)
    
    # 验证消息内容
    if len(message.content) > 10000:
        raise HTTPException(status_code=400, detail="消息过长")
    
    # 清理消息内容
    message.content = InputValidator.sanitize_string(message.content, 10000)
    
    # 验证表名（如果提供）
    # if hasattr(message, 'selected_table') and message.selected_table:
    #     message.selected_table = InputValidator.validate_table_name(message.selected_table)

    try:
        # 后台处理消息
        background_tasks.add_task(
            chat_service.process_message,
            session_id,
            message
        )
        
        return {
            "status": "accepted",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="消息处理失败")

@router.get("/history/{session_id}/messages")
async def get_chat_history(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """获取聊天历史"""
    try:
        session_data = session_mgr.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = session_data.get("messages", [])
        return {
            "session_id": session_id,
            "messages": messages,
            "total_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
