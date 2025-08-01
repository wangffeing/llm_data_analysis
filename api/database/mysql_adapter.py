"""
MySQL数据库适配器
"""
import pymysql
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from .base_adapter import DatabaseAdapter
import logging

logger = logging.getLogger(__name__)

class MySQLAdapter(DatabaseAdapter):
    """MySQL数据库适配器"""
    
    def connect(self) -> Any:
        """建立MySQL连接"""
        try:
            self.connection = pymysql.connect(
                host=self.connection_config.get('host', 'localhost'),
                port=self.connection_config.get('port', 3306),
                user=self.connection_config.get('user'),
                password=self.connection_config.get('password'),
                database=self.connection_config.get('database'),
                charset=self.connection_config.get('charset', 'utf8mb4'),
                autocommit=True
            )
            logger.info("MySQL连接成功")
            return self.connection
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise
    
    def disconnect(self):
        """关闭MySQL连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("MySQL连接已关闭")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行查询并返回结果"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"MySQL查询执行失败: {e}")
            raise
    
    def execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """执行查询并返回DataFrame"""
        try:
            return pd.read_sql(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"MySQL查询转DataFrame失败: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行非查询语句"""
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                self.connection.commit()
                return affected_rows
        except Exception as e:
            logger.error(f"MySQL非查询执行失败: {e}")
            self.connection.rollback()
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
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
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名"""
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
    
    def test_connection(self) -> bool:
        """测试MySQL连接"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"MySQL连接测试失败: {e}")
            return False