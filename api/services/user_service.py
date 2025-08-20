import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from config import get_config

logger = logging.getLogger(__name__)

class UserService:
    """用户验证服务"""
    
    def __init__(self):
        self.config = get_config()
        
    async def verify_user(self, app_code: str, token: str) -> Optional[Dict[str, Any]]:
        """
        验证用户的appCode和token
        
        Args:
            app_code: 应用代码
            token: 用户令牌
            
        Returns:
            用户信息字典，验证失败返回None
        """
        # 检查是否启用用户验证
        if not self.config.enable_user_verification:
            logger.warning("用户验证功能已禁用，跳过验证")
            # 如果禁用验证，返回默认用户信息
            return {
                'user_id': 'default_user',
                'username': '默认用户',
                'permissions': ['data_analysis', 'report_generation'],
                'expires_at': None
            }
        
        # 检查必需的配置
        if not self.config.user_verification_api_url:
            logger.error("用户验证API URL未配置")
            return None
            
        if not self.config.user_verification_api_token:
            logger.error("用户验证API Token未配置")
            return None
        
        try:
            # 准备请求数据
            headers = {
                # 'Authorization': f'Bearer {self.config.user_verification_api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'appCode': app_code,
                'token': token
            }
            
            # 发送验证请求
            timeout = aiohttp.ClientTimeout(total=self.config.user_verification_api_timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.config.user_verification_api_url,
                    json=data,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return_code = result.get('returnCode')

                        if return_code == '0':
                            # 从object字段提取用户信息
                            user_object = result.get('object', {})
                            logger.info(f"用户验证成功: {user_object.get('userCode', 'Unknown')}")
                            
                            return {
                                'user_id': user_object.get('userCode'),  # 使用userCode作为user_id
                                'username': user_object.get('userCode'),  # 使用userCode作为username
                                'department_name': user_object.get('departmentName'),
                                'team_name': user_object.get('teamName'),
                                'role': user_object.get('role'),
                                'department_id': user_object.get('departmentId'),
                                'team_id': user_object.get('teamId'),
                                'permissions': get_permissions_from_role(user_object.get('role', '')),

                                'expires_at': None  # API未提供过期时间
                            }
                        else:
                            logger.warning(f"用户验证失败: {result.get('returnMessage', 'Unknown error')}")
                            return None
                    else:
                        logger.error(f"用户验证API返回错误状态码: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("用户验证请求超时")
            return None
        except Exception as e:
            logger.error(f"用户验证请求失败: {str(e)}")
            return None
    
    async def get_user_permissions(self, app_code: str, token: str) -> list:
        """
        获取用户权限列表
        
        Args:
            app_code: 应用代码
            token: 用户令牌
            
        Returns:
            用户权限列表
        """
        result = await self.verify_user(app_code, token)
        if result["success"]:
            return result.get("permissions", [])
        return []
    
    def has_permission(self, permissions: list, required_permission: str) -> bool:
        """
        检查用户是否具有指定权限
        
        Args:
            permissions: 用户权限列表
            required_permission: 需要的权限
            
        Returns:
            是否具有权限
        """
        return required_permission in permissions or "admin" in permissions

# 全局用户服务实例
_user_service_instance: Optional[UserService] = None

def get_user_service() -> UserService:
    """获取用户服务实例（单例模式）"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance


def get_permissions_from_role(role: str) -> List[str]:
    """根据角色获取权限列表"""
    role_permissions = {
        '员工': ['data_analysis', 'report_generation'],
        '组长': ['data_analysis', 'report_generation'],
        '经理': ['data_analysis', 'report_generation', 'user_management'],
        '管理员': ['admin', 'data_analysis', 'report_generation', 'user_management']
    }
    return role_permissions.get(role, ['data_analysis'])