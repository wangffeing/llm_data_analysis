import logging
from datetime import datetime
from fastapi import APIRouter, Depends

from dependencies import get_sse_service
from services.sse_service import SSEService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(sse_service: SSEService = Depends(get_sse_service)):
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sse_stats": sse_service.get_stats(),
    }

@router.get("/stats")
async def get_stats(sse_service: SSEService = Depends(get_sse_service)):
    """获取系统统计信息"""
    return {
        "status": "running",
        "sse_stats": sse_service.get_stats()
    }