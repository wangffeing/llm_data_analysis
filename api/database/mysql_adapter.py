"""
MySQL数据库适配器 - 异步版本
"""
import asyncio
import pymysql
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from .base_adapter import DatabaseAdapter
import logging
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

class MySQLAdapter(DatabaseAdapter):
    """MySQL数据库适配器 - 异步版本"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.connection_timeout = connection_config.get('connection_timeout', 30)
        self.query_timeout = connection_config.get('query_timeout', 300)
    
    def _sync_connect(self) -> Any:
        """同步连接的内部方法"""
        try:
            self.connection = pymysql.connect(
                host=self.connection_config.get('host', 'localhost'),
                port=self.connection_config.get('port', 3306),
                user=self.connection_config.get('user'),
                password=self.connection_config.get('password'),
                database=self.connection_config.get('database'),
                charset=self.connection_config.get('charset', 'utf8mb4'),
                autocommit=True,
                connect_timeout=self.connection_timeout
            )
            logger.info("MySQL连接成功")
            return self.connection
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise
    
    async def connect(self) -> Any:
        """建立MySQL连接"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_connect
        )
    
    async def disconnect(self):
        """关闭MySQL连接"""
        def _sync_disconnect():
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("MySQL连接已关闭")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_disconnect)
    
    def _sync_execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """同步执行查询的内部方法"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"MySQL查询执行失败: {e}")
            raise
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行查询并返回结果"""
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_execute_query, query, params)
            ),
            timeout=self.query_timeout
        )
    
    def _sync_execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """同步执行查询转DataFrame的内部方法"""
        try:
            return pd.read_sql(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"MySQL查询转DataFrame失败: {e}")
            raise
    
    async def execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """执行查询并返回DataFrame"""
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_execute_query_to_dataframe, query, params)
            ),
            timeout=self.query_timeout
        )
    
    def _sync_execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """同步执行非查询的内部方法"""
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                self.connection.commit()
                return affected_rows
        except Exception as e:
            logger.error(f"MySQL非查询执行失败: {e}")
            self.connection.rollback()
            raise
    
    async def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行非查询语句"""
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_execute_non_query, query, params)
            ),
            timeout=self.query_timeout
        )
    
    def _sync_get_table_info(self, table_name: str) -> Dict[str, Any]:
        """同步获取表信息的内部方法"""
        try:
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, (self.connection_config['database'], table_name))
                columns = cursor.fetchall()
            
            return {
                'table_name': table_name,
                'columns': columns,
                'database_type': 'mysql'
            }
        except Exception as e:
            logger.error(f"获取MySQL表信息失败: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_get_table_info, table_name)
            ),
            timeout=self.query_timeout
        )
    
    def _sync_get_table_columns(self, table_name: str) -> List[str]:
        """同步获取表列名的内部方法"""
        try:
            query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.connection_config['database'], table_name))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取MySQL表列名失败: {e}")
            raise
    
    async def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名"""
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                self.executor,
                functools.partial(self._sync_get_table_columns, table_name)
            ),
            timeout=self.query_timeout
        )
    
    def _sync_test_connection(self) -> bool:
        """同步测试连接的内部方法"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"MySQL连接测试失败: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_test_connection
        )