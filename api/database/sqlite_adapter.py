"""
SQLite数据库适配器
"""
import sqlite3
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from .base_adapter import DatabaseAdapter
import logging

logger = logging.getLogger(__name__)

class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""
    
    def connect(self) -> Any:
        """建立SQLite连接"""
        try:
            db_path = self.connection_config.get('database', ':memory:')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row  # 返回字典格式
            logger.info(f"SQLite连接成功: {db_path}")
            return self.connection
        except Exception as e:
            logger.error(f"SQLite连接失败: {e}")
            raise
    
    def disconnect(self):
        """关闭SQLite连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("SQLite连接已关闭")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行查询并返回结果"""
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
    
    def execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """执行查询并返回DataFrame"""
        try:
            return pd.read_sql_query(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"SQLite查询转DataFrame失败: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行非查询语句"""
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
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
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
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名"""
        try:
            query = f"PRAGMA table_info({table_name})"
            cursor = self.connection.cursor()
            cursor.execute(query)
            return [row[1] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取SQLite表列名失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试SQLite连接"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite连接测试失败: {e}")
            return False