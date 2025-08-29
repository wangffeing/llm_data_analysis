"""
SQLite数据库适配器 - 异步版本
"""
import asyncio
import sqlite3
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from .base_adapter import DatabaseAdapter
import logging
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器 - 异步版本"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.connection_timeout = connection_config.get('connection_timeout', 30)
        self.query_timeout = connection_config.get('query_timeout', 300)
    
    def _sync_connect(self) -> Any:
        """同步连接的内部方法"""
        try:
            db_path = self.connection_config.get('database', ':memory:')
            self.connection = sqlite3.connect(db_path, timeout=self.connection_timeout)
            self.connection.row_factory = sqlite3.Row  # 返回字典格式
            logger.info(f"SQLite连接成功: {db_path}")
            return self.connection
        except Exception as e:
            logger.error(f"SQLite连接失败: {e}")
            raise
    
    async def connect(self) -> Any:
        """建立SQLite连接"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_connect
        )
    
    async def disconnect(self):
        """关闭SQLite连接"""
        def _sync_disconnect():
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("SQLite连接已关闭")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_disconnect)
    
    def _sync_execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """同步执行查询的内部方法"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQLite查询执行失败: {e}")
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
            return pd.read_sql_query(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"SQLite查询转DataFrame失败: {e}")
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
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"SQLite非查询执行失败: {e}")
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
            query = f"PRAGMA table_info({table_name})"
            cursor = self.connection.cursor()
            cursor.execute(query)
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'COLUMN_NAME': row[1],
                    'DATA_TYPE': row[2],
                    'IS_NULLABLE': 'YES' if row[3] == 0 else 'NO',
                    'COLUMN_DEFAULT': row[4],
                    'COLUMN_COMMENT': ''
                })
            
            return {
                'table_name': table_name,
                'columns': columns,
                'database_type': 'sqlite'
            }
        except Exception as e:
            logger.error(f"获取SQLite表信息失败: {e}")
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
            query = f"PRAGMA table_info({table_name})"
            cursor = self.connection.cursor()
            cursor.execute(query)
            return [row[1] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取SQLite表列名失败: {e}")
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
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite连接测试失败: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_test_connection
        )