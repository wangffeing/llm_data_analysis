import json
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from session_manager import SessionManager

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, session_manager: SessionManager, config_path: str = None):
        self.session_manager = session_manager
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "../project/taskweaver_config.json")
        self.config_path = Path(config_path)
        
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置（只读）"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取全局配置文件失败: {e}")
            return {}
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """获取会话配置"""
        session_config = self.session_manager.get_session_config(session_id)
        if session_config is None:
            # 如果会话不存在，返回全局配置
            return self.get_global_config()
        return session_config
    
    def update_session_config(self, session_id: str, new_config: Dict[str, Any]) -> bool:
        """更新会话配置"""
        try:
            # 验证配置
            if not self._validate_config(new_config):
                logger.error("配置验证失败")
                return False
            
            # 更新会话配置
            success = self.session_manager.update_session_config(session_id, new_config)
            if success:
                logger.info(f"会话 {session_id} 配置更新成功")
            return success
                
        except Exception as e:
            logger.error(f"更新会话配置失败: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置的有效性（公共方法）"""
        return self._validate_config(config)
    
    def validate_roles(self, roles: List[str]) -> bool:
        """验证角色列表的有效性"""
        valid_roles = ["planner", "code_interpreter", "recepta"]
        if not isinstance(roles, list):
            logger.error(f"角色必须是列表格式")
            return False
        
        for role in roles:
            if role not in valid_roles:
                logger.error(f"无效的角色: {role}")
                return False
        
        return True
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置的有效性"""
        # 验证session.roles
        if "session.roles" in config:
            roles = config["session.roles"]
            if not self.validate_roles(roles):
                return False
        
        # 验证code_interpreter.allowed_modules
        if "code_interpreter.allowed_modules" in config:
            modules = config["code_interpreter.allowed_modules"]
            if not isinstance(modules, list):
                logger.error(f"code_interpreter.allowed_modules必须是列表")
                return False
        
        return True
    
    def get_available_roles(self) -> List[str]:
        """获取可用的角色列表"""
        return ["planner", "code_interpreter", "recepta"]
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return [
            "qwen3-14b",
            "qwen3-32b",
            "qwen3-8b",
            "qwen3-30b-a3b",
            "qwen-turbo-2025-07-15",
            "qwen-plus-2025-07-14",
            "qwen3-30b-a3b-instruct-2507",
            "qwen3-30b-a3b-thinking-2507",
            "qwen3-235b-a22b-thinking-2507",
            "qwen3-235b-a22b-instruct-2507",
            "qwen3-coder-plus-2025-07-22",
            "qwen3-coder-480b-a35b-instruct",
            "qwen3-coder-flash-2025-07-28",
            ""
        ]
    
    def get_available_modules(self) -> List[str]:
        """获取可用的Python模块列表"""
        return [
            "pandas", "matplotlib", "numpy", "sklearn", "scipy", 
            "seaborn", "datetime", "typing", "json", "requests",
            "plotly", "bokeh", "altair", "openpyxl", "xlrd"
        ]