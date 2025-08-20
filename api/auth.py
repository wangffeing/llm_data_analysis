import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer
from services.user_service import get_user_service

security = HTTPBearer(auto_error=False)

# JWT配置
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

def _verify_jwt_token(token: str, secret_key: str) -> dict:
    """通用JWT令牌验证函数"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

def _generate_jwt_token(payload: dict, secret_key: str, expires_hours: int = JWT_EXPIRATION_HOURS) -> str:
    """通用JWT令牌生成函数"""
    payload['exp'] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)

def get_admin_secret_key() -> str:
    """获取管理员密钥"""
    admin_key = os.getenv('ADMIN_KEY')
    if not admin_key:
        raise HTTPException(status_code=500, detail="管理员密钥未配置")
    return hashlib.sha256(admin_key.encode()).hexdigest()

def get_user_secret_key() -> str:
    """获取用户密钥"""
    user_key = os.getenv('USER_SECRET_KEY', 'default_user_secret')
    return hashlib.sha256(user_key.encode()).hexdigest()

def verify_admin_key(admin_key: str) -> bool:
    """验证管理员密钥"""
    expected_key = os.getenv('ADMIN_KEY')
    if not expected_key:
        return False
    return admin_key == expected_key

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

def verify_admin_session(request: Request) -> bool:
    """验证管理员会话（基于Cookie）"""
    token = request.cookies.get('admin_session')
    if not token:
        return False
    return verify_admin_session_token(token)

def require_admin_session(request: Request) -> bool:
    """要求管理员会话（装饰器用）"""
    if not verify_admin_session(request):
        raise HTTPException(status_code=401, detail="需要管理员权限")
    return True

# 新增的管理员权限验证函数
def verify_admin_permission(request: Request) -> bool:
    """验证管理员权限（必需）"""
    return require_admin_session(request)

def verify_admin_permission_cookie(request: Request) -> bool:
    """基于Cookie验证管理员权限（必需）"""
    if not verify_admin_session(request):
        raise HTTPException(status_code=401, detail="需要管理员权限")
    return True

def verify_admin_permission_optional_cookie(request: Request) -> bool:
    """基于Cookie验证管理员权限（可选，不抛出异常）"""
    try:
        return verify_admin_session(request)
    except HTTPException:
        return False

def verify_admin_permission_optional(request: Request) -> bool:
    """验证管理员权限（可选，不抛出异常）"""
    try:
        return require_admin_session(request)
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

def require_user_session(request: Request) -> Dict[str, Any]:
    """要求用户会话（装饰器用）"""
    user_info = verify_user_session(request)
    if not user_info:
        raise HTTPException(status_code=401, detail="需要用户登录")
    return user_info

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """获取当前用户信息（可选）"""
    # 首先尝试从Cookie获取
    user_info = verify_user_session(request)
    if user_info:
        return user_info
    
    # 然后尝试从Header获取
    app_code = request.headers.get('X-App-Code')
    token = request.headers.get('X-Token')
    
    if app_code and token:
        return verify_user_credentials_optional(app_code, token)
    
    return None

def get_current_user_required(request: Request) -> Dict[str, Any]:
    """获取当前用户信息（必需）"""
    user_info = get_current_user_optional(request)
    if not user_info:
        raise HTTPException(status_code=401, detail="需要用户认证")
    return user_info

def check_user_permission(user_info: Dict[str, Any], required_permission: str) -> bool:
    """检查用户权限"""
    user_service = get_user_service()
    return user_service.check_permission(user_info.get('user_id'), required_permission)

def require_permission(permission: str):
    """权限装饰器"""
    def decorator(func):
        def wrapper(request: Request, *args, **kwargs):
            user_info = get_current_user_required(request)
            if not check_user_permission(user_info, permission):
                raise HTTPException(status_code=403, detail=f"需要权限: {permission}")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator