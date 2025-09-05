import logging
from typing import Dict, Any, List, Optional
from services.config_database_service import ConfigDatabaseService
from config import get_config
from database.database_factory import DatabaseFactory

logger = logging.getLogger(__name__)

# 移除不必要的中间层方法，直接暴露 config_service 的方法
class DataSourceService:
    def __init__(self, db_path: str = None):
        if db_path is None:
            config = get_config()
            db_path = config.config_db_path
            
        self.config_service = ConfigDatabaseService(db_path)
        self.config = get_config()
        self._cache = {}
        self._cache_timeout = 600  
        
    def get_current_database_type(self) -> str:
        """获取当前配置的数据库类型"""
        try:
            connection_string = self.config.get_db_connection_string()
            db_type, _ = DatabaseFactory.parse_connection_string(connection_string)
            return db_type
        except Exception as e:
            logger.error(f"获取数据库类型失败: {e}")
            return "unknown"
    
    # 直接代理到 config_service，移除不必要的异常处理
    async def get_all_data_sources(self) -> Dict[str, Any]:
        return await self.config_service.get_all_data_sources()
    
    async def get_data_source(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.config_service.get_data_source(name)
    
    async def add_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        return await self.config_service.add_data_source(
            name, 
            config["table_name"], 
            config["table_des"], 
            config["table_order"], 
            config["table_columns"], 
            config["table_columns_names"], 
            config.get("database_type", "unknown")
        )
    
    async def update_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        return await self.config_service.update_data_source(name, **config)
    
    async def delete_data_source(self, name: str) -> bool:
        return await self.config_service.delete_data_source(name)
    
    async def get_data_sources_by_current_db_type(self) -> Dict[str, Any]:
        current_db_type = self.get_current_database_type()
        return await self.config_service.get_data_sources_by_database_type(current_db_type)
    
    async def get_available_database_types(self) -> List[str]:
        return await self.config_service.get_available_database_types()
    
    async def get_database_stats(self) -> Dict:
        return await self.config_service.get_database_stats()