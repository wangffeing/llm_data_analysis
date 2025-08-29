"""
数据库适配器基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

class DatabaseAdapter(ABC):
    """数据库适配器基类"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self.connection = None
    
    @abstractmethod
    async def connect(self) -> Any:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行查询并返回结果"""
        pass
    
    @abstractmethod
    async def execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """执行查询并返回DataFrame"""
        pass
    
    @abstractmethod
    async def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行非查询语句（INSERT, UPDATE, DELETE）"""
        pass
    
    @abstractmethod
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
        pass
    
    @abstractmethod
    async def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        pass
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()