"""
数据库连接管理器 - 支持多种数据库类型
"""
import logging
from typing import Optional, Dict, Any
from database.database_factory import DatabaseFactory
from database.base_adapter import DatabaseAdapter
from config import get_config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.adapter: Optional[DatabaseAdapter] = None
        self.config = get_config()
    
    def get_adapter(self) -> DatabaseAdapter:
        """获取数据库适配器"""
        if self.adapter is None:
            self.connect()
        return self.adapter
    
    def connect(self):
        """建立数据库连接"""
        try:
            connection_string = self.config.get_db_connection_string()
            db_type, connection_config = DatabaseFactory.parse_connection_string(connection_string)
            
            self.adapter = DatabaseFactory.create_adapter(db_type, connection_config)
            self.adapter.connect()
            
            logger.info(f"数据库连接成功: {db_type}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.adapter:
            self.adapter.disconnect()
            self.adapter = None
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            adapter = self.get_adapter()
            return adapter.test_connection()
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def execute_query(self, query: str, params=None):
        """执行查询"""
        adapter = self.get_adapter()
        return adapter.execute_query(query, params)
    
    def execute_query_to_dataframe(self, query: str, params=None):
        """执行查询并返回DataFrame"""
        adapter = self.get_adapter()
        return adapter.execute_query_to_dataframe(query, params)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例（单例模式）"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def create_db_connection():
    """创建数据库连接（兼容旧接口）"""
    db_manager = get_db_manager()
    return db_manager.get_adapter().connection