"""
权限管理模块
提供基于 Cookie 和 JWT 的安全认证功能
"""

from fastapi import HTTPException, Header, Depends, Request, Response
from typing import Optional
import os
from config import Config
import jwt
from datetime import datetime, timedelta

def verify_admin_permission_cookie(request: Request):
    """
    基于 Cookie 的管理员权限验证
    
    Args:
        request: FastAPI 请求对象
        
    Raises:
        HTTPException: 当权限验证失败时抛出403错误
        
    Returns:
        bool: 验证成功返回 True
    """
    config = Config()
    
    # 如果未启用认证，直接通过
    if not config.enable_auth:
        return True
    
    # 从 Cookie 中获取 admin token
    admin_token = request.cookies.get("admin_token")
    
    if not admin_token:
        raise HTTPException(
            status_code=401,
            detail="需要管理员权限。请先登录管理员账户。"
        )
    
    # 验证 JWT token
    try:
        payload = jwt.decode(admin_token, config.secret_key, algorithms=["HS256"])
        admin_key = payload.get("admin_key")
        
        if admin_key != config.admin_api_key:
            raise HTTPException(
                status_code=403,
                detail="无效的管理员权限。请重新登录。"
            )
            
        return True
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="管理员权限已过期。请重新登录。"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=403,
            detail="无效的管理员权限。请重新登录。"
        )

def verify_admin_permission_optional_cookie(request: Request):
    """
    可选的基于 Cookie 的管理员权限验证
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        bool: 是否具有管理员权限
    """
    config = Config()
    
    # 如果未启用认证，直接返回True
    if not config.enable_auth:
        return True
    
    # 从 Cookie 中获取 admin token
    admin_token = request.cookies.get("admin_token")
    
    if not admin_token:
        return False
    
    # 验证 JWT token
    try:
        payload = jwt.decode(admin_token, config.secret_key, algorithms=["HS256"])
        admin_key = payload.get("admin_key")
        return admin_key == config.admin_api_key
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False

def verify_admin_permission(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """
    验证管理员权限（保持向后兼容）
    
    Args:
        x_admin_key: 从请求头获取的管理员密钥
        
    Raises:
        HTTPException: 当权限验证失败时抛出403错误
    """
    config = Config()
    
    # 如果未启用认证，直接通过
    if not config.enable_auth:
        return True
    
    # 检查是否提供了密钥
    if not x_admin_key:
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限。请在请求头中提供 X-Admin-Key。"
        )
    
    # 验证密钥
    if x_admin_key != config.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="无效的管理员密钥。请检查您的权限设置。"
        )
    
    return True

def verify_admin_permission_optional(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """
    可选的管理员权限验证（用于某些可能需要权限的操作）
    
    Args:
        x_admin_key: 从请求头获取的管理员密钥
        
    Returns:
        bool: 是否具有管理员权限
    """
    config = Config()
    
    # 如果未启用认证，直接返回True
    if not config.enable_auth:
        return True
    
    # 如果没有提供密钥，返回False
    if not x_admin_key:
        return False
    
    # 验证密钥
    return x_admin_key == config.admin_api_key

def generate_admin_token(admin_key: str) -> str:
    """生成管理员认证令牌"""
    config = Config()
    payload = {
        "admin_key": admin_key,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
        "type": "admin"
    }
    return jwt.encode(payload, config.secret_key, algorithm="HS256")

def generate_session_token(session_id: str) -> str:
    """生成会话令牌"""
    config = Config()
    payload = {
        "session_id": session_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, config.secret_key, algorithm="HS256")

def verify_session_token(token: str) -> Optional[str]:
    """验证会话令牌"""
    try:
        config = Config()
        payload = jwt.decode(token, config.secret_key, algorithms=["HS256"])
        return payload.get("session_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None