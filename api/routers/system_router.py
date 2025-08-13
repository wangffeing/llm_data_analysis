import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from dependencies import get_sse_service
from services.sse_service import SSEService
from auth import (
    verify_admin_permission, 
    verify_admin_permission_cookie,
    verify_admin_permission_optional_cookie,
    generate_admin_token
)
from config import Config

logger = logging.getLogger(__name__)
router = APIRouter()

class AdminLoginRequest(BaseModel):
    admin_key: str

class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    expires_at: str

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

@router.post("/verify-admin-key")
async def verify_admin_key(_: bool = Depends(verify_admin_permission)):
    """验证管理员密钥（向后兼容）"""
    return {"success": True, "message": "管理员密钥验证成功"}

@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest, response: Response):
    """管理员登录"""
    config = Config()
    
    # 如果未启用认证，直接返回成功
    if not config.enable_auth:
        return AdminLoginResponse(
            success=True,
            message="认证已禁用，自动授予管理员权限",
            expires_at=(datetime.utcnow() + timedelta(hours=24)).isoformat()
        )
    
    # 验证管理员密钥
    if request.admin_key != config.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="无效的管理员密钥"
        )
    
    # 生成 JWT token
    token = generate_admin_token(request.admin_key)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # 设置 httpOnly cookie
    response.set_cookie(
        key="admin_token",
        value=token,
        max_age=24 * 60 * 60,  # 24小时
        httponly=True,  # 防止 XSS
        secure=True,  # 在生产环境中启用 HTTPS
        samesite="lax"  # CSRF 保护
    )
    
    logger.info("管理员登录成功")
    
    return AdminLoginResponse(
        success=True,
        message="登录成功",
        expires_at=expires_at.isoformat()
    )

@router.post("/admin/logout")
async def admin_logout(response: Response):
    """管理员登出"""
    # 清除 cookie
    response.delete_cookie(
        key="admin_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    logger.info("管理员登出成功")
    
    return {"success": True, "message": "登出成功"}

@router.get("/admin/status")
async def admin_status(request: Request):
    """检查管理员登录状态"""
    is_admin = verify_admin_permission_optional_cookie(request)
    
    return {
        "is_logged_in": is_admin,
        "timestamp": datetime.now().isoformat()
    }