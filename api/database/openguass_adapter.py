"""
OpenGauss数据库适配器 - 异步版本
"""
import asyncio
import py_opengauss
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from .base_adapter import DatabaseAdapter
import logging
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

class OpenGaussAdapter(DatabaseAdapter):
    """OpenGauss数据库适配器 - 异步版本"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.executor = ThreadPoolExecutor(max_workers=5)  # 线程池
        self.connection_timeout = connection_config.get('connection_timeout', 30)
        self.query_timeout = connection_config.get('query_timeout', 300)  # 5分钟查询超时
    
    async def connect(self) -> Any:
        """建立OpenGauss连接"""
        def _sync_connect():
            try:
                # 如果connection_config包含完整的连接字符串
                if 'connection_string' in self.connection_config:
                    return py_opengauss.open(self.connection_config['connection_string'])
                else:
                    # 构建连接字符串
                    conn_str = f"opengauss://{self.connection_config['user']}:{self.connection_config['password']}@{self.connection_config['host']}:{self.connection_config['port']}/{self.connection_config['database']}"
                    return py_opengauss.open(conn_str)
            except Exception as e:
                logger.error(f"OpenGauss连接失败: {e}")
                raise
        
        try:
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                self.executor, 
                _sync_connect
            )
            logger.info("OpenGauss连接成功")
            return self.connection
        except Exception as e:
            logger.error(f"OpenGauss异步连接失败: {e}")
            raise
    
    async def disconnect(self):
        """关闭OpenGauss连接"""
        def _sync_disconnect():
            if self.connection:
                self.connection.close()
                logger.info("OpenGauss连接已关闭")
        
        if self.connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, _sync_disconnect)
            self.connection = None
        
        if self.executor:
            self.executor.shutdown(wait=False)
    
    def _sync_execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """同步执行查询的内部方法"""
        try:
            # 使用prepare方法准备查询
            if params:
                # 将参数占位符从%s转换为$1, $2, ...
                param_query = self._convert_params_format(query, len(params))
                prepared_stmt = self.connection.prepare(param_query)
                rows = prepared_stmt(*params)
            else:
                prepared_stmt = self.connection.prepare(query)
                rows = prepared_stmt()
            
            # 转换为字典列表
            result = []
            if rows:
                # 获取列名
                columns = rows.columns if hasattr(rows, 'columns') else []
                if not columns and len(rows) > 0:
                    # 如果没有columns属性，尝试从第一行推断
                    first_row = rows[0] if isinstance(rows, list) else next(iter(rows))
                    if isinstance(first_row, (list, tuple)):
                        columns = [f"column_{i}" for i in range(len(first_row))]
                    elif isinstance(first_row, dict):
                        columns = list(first_row.keys())
                
                for row in rows:
                    if isinstance(row, dict):
                        result.append(row)
                    elif isinstance(row, (list, tuple)):
                        result.append(dict(zip(columns, row)))
                    else:
                        # 单值结果
                        result.append({columns[0] if columns else 'result': row})
            
            return result
        except Exception as e:
            logger.error(f"OpenGauss查询执行失败: {e}")
            raise
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """异步执行查询并返回结果"""
        loop = asyncio.get_event_loop()
        try:
            # 在线程池中执行同步数据库操作
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    functools.partial(self._sync_execute_query, query, params)
                ),
                timeout=self.query_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"查询超时: {query[:100]}...")
            raise Exception(f"查询超时 ({self.query_timeout}秒)")
        except Exception as e:
            logger.error(f"异步查询执行失败: {e}")
            raise
    
    def _sync_execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """同步执行查询转DataFrame的内部方法"""
        try:
            # 使用prepare方法准备查询
            if params:
                # 将参数占位符从%s转换为$1, $2, ...
                param_query = self._convert_params_format(query, len(params))
                prepared_stmt = self.connection.prepare(param_query)
                rows = prepared_stmt(*params)
            else:
                prepared_stmt = self.connection.prepare(query)
                rows = prepared_stmt()
            
            # 转换为DataFrame
            if not rows:
                return pd.DataFrame()
            
            # 获取列名
            columns = rows.columns if hasattr(rows, 'columns') else []
            if not columns and len(rows) > 0:
                # 如果没有columns属性，尝试从第一行推断
                first_row = rows[0] if isinstance(rows, list) else next(iter(rows))
                if isinstance(first_row, (list, tuple)):
                    columns = [f"column_{i}" for i in range(len(first_row))]
                elif isinstance(first_row, dict):
                    columns = list(first_row.keys())
            
            # 转换数据
            data = []
            for row in rows:
                if isinstance(row, dict):
                    data.append(list(row.values()))
                elif isinstance(row, (list, tuple)):
                    data.append(list(row))
                else:
                    data.append([row])
            
            return pd.DataFrame(data, columns=columns)
        except Exception as e:
            logger.error(f"OpenGauss查询转DataFrame失败: {e}")
            raise
    
    async def execute_query_to_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """异步执行查询并返回DataFrame"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    functools.partial(self._sync_execute_query_to_dataframe, query, params)
                ),
                timeout=self.query_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"查询超时: {query[:100]}...")
            raise Exception(f"查询超时 ({self.query_timeout}秒)")
        except Exception as e:
            logger.error(f"异步查询转DataFrame失败: {e}")
            raise
    
    def _sync_execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """同步执行非查询语句的内部方法"""
        try:
            # 使用prepare方法准备查询
            if params:
                # 将参数占位符从%s转换为$1, $2, ...
                param_query = self._convert_params_format(query, len(params))
                prepared_stmt = self.connection.prepare(param_query)
                result = prepared_stmt(*params)
            else:
                prepared_stmt = self.connection.prepare(query)
                result = prepared_stmt()
            
            # 对于非查询语句，通常返回影响的行数
            # py_opengauss可能返回不同的结果格式
            if hasattr(result, 'rowcount'):
                return result.rowcount
            elif isinstance(result, int):
                return result
            else:
                # 如果无法确定影响的行数，返回1表示执行成功
                return 1
        except Exception as e:
            logger.error(f"OpenGauss非查询执行失败: {e}")
            raise
    
    async def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """异步执行非查询语句"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    functools.partial(self._sync_execute_non_query, query, params)
                ),
                timeout=self.query_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"非查询操作超时: {query[:100]}...")
            raise Exception(f"操作超时 ({self.query_timeout}秒)")
        except Exception as e:
            logger.error(f"异步非查询执行失败: {e}")
            raise
    
    def _sync_get_table_info(self, table_name: str) -> Dict[str, Any]:
        """同步获取表信息的内部方法"""
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                '' as column_comment
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
            """
            prepared_stmt = self.connection.prepare(query)
            rows = prepared_stmt(table_name)
            
            columns = []
            for row in rows:
                if isinstance(row, (list, tuple)):
                    columns.append({
                        'COLUMN_NAME': row[0],
                        'DATA_TYPE': row[1],
                        'IS_NULLABLE': row[2],
                        'COLUMN_DEFAULT': row[3],
                        'COLUMN_COMMENT': row[4]
                    })
                elif isinstance(row, dict):
                    columns.append({
                        'COLUMN_NAME': row.get('column_name'),
                        'DATA_TYPE': row.get('data_type'),
                        'IS_NULLABLE': row.get('is_nullable'),
                        'COLUMN_DEFAULT': row.get('column_default'),
                        'COLUMN_COMMENT': row.get('column_comment', '')
                    })
            
            return {
                'table_name': table_name,
                'columns': columns,
                'database_type': 'opengauss'
            }
        except Exception as e:
            logger.error(f"获取OpenGauss表信息失败: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """异步获取表信息"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    functools.partial(self._sync_get_table_info, table_name)
                ),
                timeout=self.query_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取表信息超时: {table_name}")
            raise Exception(f"获取表信息超时 ({self.query_timeout}秒)")
        except Exception as e:
            logger.error(f"异步获取表信息失败: {e}")
            raise
    
    def _sync_get_table_columns(self, table_name: str) -> List[str]:
        """同步获取表列名的内部方法"""
        try:
            query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
            """
            prepared_stmt = self.connection.prepare(query)
            rows = prepared_stmt(table_name)
            
            columns = []
            for row in rows:
                if isinstance(row, (list, tuple)):
                    columns.append(row[0])
                elif isinstance(row, dict):
                    columns.append(row.get('column_name'))
                else:
                    columns.append(str(row))
            
            return columns
        except Exception as e:
            logger.error(f"获取OpenGauss表列名失败: {e}")
            raise
    
    async def get_table_columns(self, table_name: str) -> List[str]:
        """异步获取表的列名"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    functools.partial(self._sync_get_table_columns, table_name)
                ),
                timeout=self.query_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取表列名超时: {table_name}")
            raise Exception(f"获取表列名超时 ({self.query_timeout}秒)")
        except Exception as e:
            logger.error(f"异步获取表列名失败: {e}")
            raise
    
    def _sync_test_connection(self) -> bool:
        """同步测试连接的内部方法"""
        try:
            prepared_stmt = self.connection.prepare("SELECT 1")
            result = prepared_stmt()
            return True
        except Exception as e:
            logger.error(f"OpenGauss连接测试失败: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """异步测试OpenGauss连接"""
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    self._sync_test_connection
                ),
                timeout=30  # 连接测试30秒超时
            )
            return result
        except asyncio.TimeoutError:
            logger.error("连接测试超时")
            return False
        except Exception as e:
            logger.error(f"异步连接测试失败: {e}")
            return False
    
    def _convert_params_format(self, query: str, param_count: int) -> str:
        """将%s参数占位符转换为$1, $2, ...格式"""
        result = query
        for i in range(param_count):
            result = result.replace('%s', f'${i+1}', 1)
        return result
