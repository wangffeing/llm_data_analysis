import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import timedelta
from typing import Dict, Any
from dependencies import get_sse_service
from services.sse_service import SSEService
from services.user_service import get_user_service
from auth import (
    verify_admin_permission, 
    verify_admin_permission_cookie,
    verify_admin_permission_optional_cookie,
    generate_admin_token,
    verify_user_credentials,
    verify_user_credentials_optional,
    generate_user_session_token,
    verify_user_session,
    require_user_session
)
from config import Config, get_config

logger = logging.getLogger(__name__)
router = APIRouter()

class AdminLoginRequest(BaseModel):
    admin_key: str

class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    expires_at: str

class UserVerificationRequest(BaseModel):
    app_code: str
    token: str

class UserVerificationResponse(BaseModel):
    success: bool
    message: str
    user_id: str = ""
    username: str = ""
    permissions: list = []
    expires_at: str = ""

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

@router.post("/verify-user", response_model=UserVerificationResponse)
async def verify_user_endpoint(request: UserVerificationRequest):
    try:
        user_service = get_user_service()
        user_info = await user_service.verify_user(request.app_code, request.token)
        
        if user_info:
            # 生成用户会话令牌
            session_token = generate_user_session_token(user_info)
            
            # 创建响应
            response = JSONResponse(content={
                "success": True,
                "message": "用户验证成功",
                "user_id": user_info.get('user_id'),
                "username": user_info.get('username'),
                "permissions": user_info.get('permissions', []),
                "department_name": user_info.get('department_name'),
                "team_name": user_info.get('team_name'),
                "role": user_info.get('role'),
                "expires_at": user_info.get('expires_at')
            })
            
            # 设置用户会话Cookie
            response.set_cookie(
                key="user_session",
                value=session_token,
                max_age=86400,  # 24小时
                httponly=True,
                secure=False,  # 开发环境设为False
                samesite="lax"
            )
            
            return response
        else:
            raise HTTPException(status_code=401, detail="用户验证失败")
            
    except Exception as e:
        logger.error(f"用户验证错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.get("/user-status")
async def get_user_status(request: Request):
    """检查用户登录状态"""
    # 修复：移除 await，因为 verify_user_session 不是异步函数
    user_info = verify_user_session(request)
    
    return {
        "is_logged_in": user_info is not None,
        "user_info": user_info if user_info else None,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/user/logout")
async def user_logout(response: Response):
    """用户登出"""
    # 修复：统一Cookie名称为 user_session
    response.delete_cookie(
        key="user_session",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    logger.info("用户登出成功")
    
    return {"success": True, "message": "登出成功"}

@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    config = get_config()
    return {
        "user_verification_enabled": config.enable_user_verification,
        "auth_enabled": config.enable_auth,
        "timestamp": datetime.now().isoformat()
    }