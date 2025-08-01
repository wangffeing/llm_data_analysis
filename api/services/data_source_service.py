import logging
from typing import Dict, Any, List, Optional
from services.config_database_service import ConfigDatabaseService
from config import get_config
from database.database_factory import DatabaseFactory

logger = logging.getLogger(__name__)

class DataSourceService:
    def __init__(self, db_path: str = None):
        """
        数据源服务类 - 从SQLite数据库读取配置
        修复：如果没有提供 db_path，则从配置文件读取
        """
        if db_path is None:
            config = get_config()
            db_path = config.config_db_path
            
        self.config_service = ConfigDatabaseService(db_path)
        self.config = get_config()
        
    def get_current_database_type(self) -> str:
        """获取当前配置的数据库类型"""
        try:
            connection_string = self.config.get_db_connection_string()
            db_type, _ = DatabaseFactory.parse_connection_string(connection_string)
            return db_type
        except Exception as e:
            logger.error(f"获取数据库类型失败: {e}")
            return "unknown"
        
    def get_all_data_sources(self) -> Dict[str, Any]:
        """获取所有数据源"""
        try:
            return self.config_service.get_all_data_sources()
        except Exception as e:
            logger.error(f"获取数据源失败: {e}")
            return {}
    
    def get_data_sources_by_current_db_type(self) -> Dict[str, Any]:
        """获取当前数据库类型的数据源"""
        try:
            current_db_type = self.get_current_database_type()
            return self.config_service.get_data_sources_by_database_type(current_db_type)
        except Exception as e:
            logger.error(f"获取当前数据库类型的数据源失败: {e}")
            return {}
    
    def get_data_source(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个数据源"""
        try:
            return self.config_service.get_data_source(name)
        except Exception as e:
            logger.error(f"获取数据源失败: {e}")
            return None
    
    def add_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        """添加数据源"""
        try:
            # 获取当前数据库类型
            current_db_type = self.get_current_database_type()
            
            return self.config_service.add_data_source(
                source_key=name,
                table_name=config.get('table_name', ''),
                table_des=config.get('table_des', ''),
                table_order=config.get('table_order', ''),
                table_columns=config.get('table_columns', []),
                table_columns_names=config.get('table_columns_names', []),
                database_type=config.get('database_type', current_db_type)  # 使用当前数据库类型作为默认值
            )
        except Exception as e:
            logger.error(f"添加数据源失败: {e}")
            return False
    
    def update_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        """更新数据源"""
        try:
            return self.config_service.update_data_source(
                source_key=name,
                table_name=config.get('table_name'),
                table_des=config.get('table_des'),
                table_order=config.get('table_order'),
                table_columns=config.get('table_columns'),
                table_columns_names=config.get('table_columns_names'),
                database_type=config.get('database_type')  # 支持更新数据库类型
            )
        except Exception as e:
            logger.error(f"更新数据源失败: {e}")
            return False
    
    def delete_data_source(self, name: str) -> bool:
        """删除数据源"""
        try:
            return self.config_service.delete_data_source(name)
        except Exception as e:
            logger.error(f"删除数据源失败: {e}")
            return False
    
    def get_data_sources_list(self) -> List[Dict[str, Any]]:
        """获取数据源列表"""
        try:
            return self.config_service.get_data_sources_list()
        except Exception as e:
            logger.error(f"获取数据源列表失败: {e}")
            return []
    
    def search_data_sources(self, keyword: str) -> Dict[str, Any]:
        """搜索数据源"""
        try:
            return self.config_service.search_data_sources(keyword)
        except Exception as e:
            logger.error(f"搜索数据源失败: {e}")
            return {}
    
    def get_available_database_types(self) -> List[str]:
        """获取所有可用的数据库类型"""
        try:
            return self.config_service.get_available_database_types()
        except Exception as e:
            logger.error(f"获取数据库类型列表失败: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        try:
            stats = self.config_service.get_database_stats()
            stats['current_database_type'] = self.get_current_database_type()
            return stats
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")