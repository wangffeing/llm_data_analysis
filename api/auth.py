import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer
from services.user_service import get_user_service
from config import get_config  # 添加统一配置导入

security = HTTPBearer(auto_error=False)

# 移除冗余的环境变量读取
# JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')  # 删除
# JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))  # 删除

def _verify_jwt_token(token: str, secret_key: str) -> dict:
    """通用JWT令牌验证函数"""
    try:
        # 使用固定算法，简化配置
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

def _generate_jwt_token(payload: dict, secret_key: str, expires_hours: int = 24) -> str:
    """通用JWT令牌生成函数"""
    payload['exp'] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, secret_key, algorithm='HS256')

def get_admin_secret_key() -> str:
    """获取管理员密钥"""
    config = get_config()
    if not config.admin_api_key:
        raise HTTPException(status_code=500, detail="管理员密钥未配置")
    return hashlib.sha256(config.admin_api_key.encode()).hexdigest()

def get_user_secret_key() -> str:
    """获取用户密钥"""
    config = get_config()
    # 使用管理员密钥作为用户密钥的基础，确保安全性
    user_key = f"user_{config.admin_api_key}"
    return hashlib.sha256(user_key.encode()).hexdigest()

def verify_admin_key(admin_key: str) -> bool:
    """验证管理员密钥"""
    config = get_config()
    return admin_key == config.admin_api_key


def generate_admin_session_token() -> str:
    """生成管理员会话令牌"""
    secret_key = get_admin_secret_key()
    payload = {
        'type': 'admin_session',
        'iat': datetime.utcnow()
    }
    return _generate_jwt_token(payload, secret_key)

def verify_admin_session_token(token: str) -> bool:
    """验证管理员会话令牌"""
    try:
        secret_key = get_admin_secret_key()
        payload = _verify_jwt_token(token, secret_key)
        return payload.get('type') == 'admin_session'
    except HTTPException:
        return False

# 简化权限验证函数，移除冗余的多个验证函数
def verify_admin_permission(request: Request) -> bool:
    """统一的管理员权限验证"""
    config = get_config()
    
    # 如果未启用认证，直接返回True
    if not config.enable_auth:
        return True
    
    # 检查Cookie中的会话令牌
    token = request.cookies.get('admin_token')
    if not token:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    return verify_admin_session_token(token)

def verify_admin_permission_optional(request: Request) -> bool:
    """可选的管理员权限验证"""
    try:
        return verify_admin_permission(request)
    except HTTPException:
        return False



def generate_admin_token(admin_key: str) -> str:
    """生成管理员令牌"""
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=403, detail="无效的管理员密钥")
    return generate_admin_session_token()

# 用户相关函数保持不变
def verify_user_credentials(app_code: str, token: str) -> Optional[Dict[str, Any]]:
    """验证用户凭据"""
    user_service = get_user_service()
    return user_service.verify_user(app_code, token)

def verify_user_credentials_optional(app_code: str, token: str) -> Optional[Dict[str, Any]]:
    """可选的用户凭据验证（不抛出异常）"""
    try:
        return verify_user_credentials(app_code, token)
    except Exception as e:
        print(f"用户凭据验证失败: {e}")
        return None

def generate_user_session_token(user_info: Dict[str, Any]) -> str:
    """生成用户会话令牌"""
    try:
        secret_key = get_user_secret_key()
        payload = {
            'type': 'user_session',
            'user_id': user_info.get('user_id'),
            'username': user_info.get('username'),
            'app_code': user_info.get('app_code', 'default'),
            'permissions': user_info.get('permissions', []),
            'department_name': user_info.get('department_name'),
            'team_name': user_info.get('team_name'),
            'role': user_info.get('role'),
            'iat': datetime.utcnow()
        }
        return _generate_jwt_token(payload, secret_key)
    except Exception as e:
        # 使用 print 或者导入 logging
        print(f"生成用户会话令牌失败: {str(e)}")
        raise

def verify_user_session_token(token: str) -> Optional[Dict[str, Any]]:
    """验证用户会话令牌"""
    try:
        secret_key = get_user_secret_key()
        payload = _verify_jwt_token(token, secret_key)
        
        if payload.get('type') != 'user_session':
            return None
            
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'app_code': payload.get('app_code'),
            'permissions': payload.get('permissions', [])
        }
    except HTTPException:
        return None

def verify_user_session(request: Request) -> Optional[Dict[str, Any]]:
    """验证用户会话（基于Cookie）"""
    token = request.cookies.get('user_session')
    if not token:
        return None
    return verify_user_session_token(token)

def verify_admin_permission_cookie(request: Request) -> bool:
    """基于Cookie的管理员权限验证"""
    config = get_config()
    if not config.enable_auth:
        return True
    
    token = request.cookies.get('admin_token')
    if not token:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    return verify_admin_session_token(token)

def verify_admin_permission_optional_cookie(request: Request) -> bool:
    """可选的基于Cookie的管理员权限验证"""
    try:
        return verify_admin_permission_cookie(request)
    except HTTPException:
        return False