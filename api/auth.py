"""
权限管理模块
提供简单的API密钥验证功能
"""

from fastapi import HTTPException, Header, Depends
from typing import Optional
import os
from config import Config

def verify_admin_permission(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """
    验证管理员权限
    
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