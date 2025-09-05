import sqlite3
import json
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from datetime import datetime

class ConfigDatabaseService:
    """
    配置数据库服务类
    提供从SQLite数据库读取和管理配置数据的异步功能
    """
    
    def __init__(self, db_path=None):
        """
        修复：如果没有提供 db_path，则从配置文件读取
        """
        if db_path is None:
            from config import get_config
            config = get_config()
            db_path = config.config_db_path
        self.db_path = db_path
        # 创建专用的数据库操作线程池
        self.db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_ops")
        self._connection_lock = Lock()
        self._connection_pool_size = 5

    @contextmanager
    def get_connection(self):
        """使用连接池管理数据库连接"""
        with self._connection_lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    
    def _row_to_dict(self, row):
        """将 sqlite3.Row 对象转换为字典，提供 .get() 方法兼容性"""
        if row is None:
            return None
        return dict(row)
    
    def _safe_get(self, row, key, default=None):
        """安全地从 sqlite3.Row 对象获取值"""
        try:
            return row[key] if key in row.keys() else default
        except (KeyError, IndexError):
            return default

    # 在 ConfigDatabaseService 中优化查询
    # 优化数据库查询方法
    def _sync_get_all_data_sources(self) -> Dict:
        """优化：使用单个查询获取所有数据，避免 N+1 问题"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用单个优化查询
            cursor.execute('''
                SELECT ds.source_key, ds.table_name, ds.table_des, ds.table_order, ds.database_type,
                       dsc.column_name, dsc.column_display_name, dsc.column_order
                FROM data_sources ds
                LEFT JOIN data_source_columns dsc ON ds.id = dsc.source_id
                ORDER BY ds.source_key, dsc.column_order
            ''')
            
            sources = {}
            for row in cursor.fetchall():
                source_key = row['source_key']
                
                if source_key not in sources:
                    sources[source_key] = {
                        'table_name': row['table_name'],
                        'table_des': row['table_des'],
                        'table_order': row['table_order'],
                        'table_columns': [],
                        'table_columns_names': [],
                        'database_type': self._safe_get(row, 'database_type', 'unknown')
                    }
                
                if row['column_name']:  # 避免空列
                    sources[source_key]['table_columns'].append(row['column_name'])
                    sources[source_key]['table_columns_names'].append(row['column_display_name'])
            
            return sources
    
    async def get_all_data_sources(self) -> Dict:
        """异步获取所有数据源配置"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_get_all_data_sources)
    
    # 添加单个数据源查询方法
    def _sync_get_single_data_source(self, source_key: str) -> Optional[Dict]:
        """优化：使用JOIN查询避免多次数据库访问"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ds.source_key, ds.table_name, ds.table_des, ds.table_order, ds.database_type,
                       dsc.column_name, dsc.column_display_name, dsc.column_order
                FROM data_sources ds
                LEFT JOIN data_source_columns dsc ON ds.id = dsc.source_id
                WHERE ds.source_key = ?
                ORDER BY dsc.column_order
            ''', (source_key,))
            
            rows = cursor.fetchall()
            if not rows:
                return None
                
            # 构建结果
            first_row = rows[0]
            result = {
                'table_name': first_row['table_name'],
                'table_des': first_row['table_des'],
                'table_order': first_row['table_order'],
                'table_columns': [],
                'table_columns_names': [],
                'database_type': self._safe_get(first_row, 'database_type', 'unknown')
            }
            
            for row in rows:
                if row['column_name']:
                    result['table_columns'].append(row['column_name'])
                    result['table_columns_names'].append(row['column_display_name'])
            
            return result
    
    async def get_data_source(self, source_key: str) -> Optional[Dict]:
        """优化：直接查询单个数据源"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_get_single_data_source, source_key)
    
    # 修复删除方法，添加级联删除
    def _sync_delete_data_source(self, source_key: str) -> bool:
        """修复：添加级联删除"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取数据源ID
                cursor.execute('SELECT id FROM data_sources WHERE source_key = ?', (source_key,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                source_id = row['id']
                
                # 删除相关列配置
                cursor.execute('DELETE FROM data_source_columns WHERE source_id = ?', (source_id,))
                
                # 删除数据源
                cursor.execute('DELETE FROM data_sources WHERE source_key = ?', (source_key,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"删除数据源失败: {e}")
            return False

    async def delete_data_source(self, source_key: str) -> bool:
        """异步删除数据源配置"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_delete_data_source, source_key)
    
    async def get_data_sources_by_database_type(self, database_type: str) -> Dict:
        """异步根据数据库类型获取数据源"""
        all_sources = await self.get_all_data_sources()
        filtered_sources = {}
        
        for key, config in all_sources.items():
            if config.get('database_type', 'unknown') == database_type:
                filtered_sources[key] = config
        
        return filtered_sources
    
    def _sync_get_available_database_types(self) -> List[str]:
        """同步获取所有可用的数据库类型"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT database_type FROM data_sources WHERE database_type IS NOT NULL')
            return [row[0] for row in cursor.fetchall()]

    async def get_available_database_types(self) -> List[str]:
        """异步获取所有可用的数据库类型"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_get_available_database_types)

    def _sync_get_all_templates(self) -> Dict:
        """同步获取所有模板配置"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM analysis_templates ORDER BY template_id')
            templates = {}
            
            for template_row in cursor.fetchall():
                template_id = template_row['template_id']
                
                # 获取必需列
                cursor.execute('''
                    SELECT column_name as name, column_type as type, description 
                    FROM template_required_columns 
                    WHERE template_id = ?
                ''', (template_row['id'],))
                required_columns = [self._row_to_dict(row) for row in cursor.fetchall()]
                
                # 获取可选列
                cursor.execute('''
                    SELECT column_name as name, column_type as type, description 
                    FROM template_optional_columns 
                    WHERE template_id = ?
                ''', (template_row['id'],))
                optional_columns = [self._row_to_dict(row) for row in cursor.fetchall()]
                
                # 获取执行步骤
                cursor.execute('''
                    SELECT prompt, save_to_variable 
                    FROM template_execution_steps 
                    WHERE template_id = ? 
                    ORDER BY step_order
                ''', (template_row['id'],))
                steps = [self._row_to_dict(row) for row in cursor.fetchall()]
                
                # 获取输出文件
                cursor.execute('''
                    SELECT file_type as type, title, source_variable, tool 
                    FROM template_output_files 
                    WHERE template_id = ?
                ''', (template_row['id'],))
                files = [self._row_to_dict(row) for row in cursor.fetchall()]
                
                templates[template_id] = {
                    'template_metadata': {
                        'id': template_id,
                        'name': template_row['template_name'],
                        'summary': template_row['summary']
                    },
                    'data_schema': {
                        'required_columns': required_columns,
                        'optional_columns': optional_columns
                    },
                    'execution_plan': {
                        'analysis_goal': template_row['analysis_goal'],
                        'steps': steps
                    },
                    'output_specification': {
                        'insights_template': template_row['insights_template'],
                        'files': files
                    }
                }
            
            return templates

    async def get_all_templates(self) -> Dict:
        """异步获取所有模板配置"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_get_all_templates)
    
    async def get_template(self, template_id: str) -> Optional[Dict]:
        """异步获取单个模板配置"""
        templates = await self.get_all_templates()
        return templates.get(template_id)
    
    async def get_data_sources_list(self) -> List[Dict]:
        """异步获取数据源列表（用于API返回）"""
        sources = await self.get_all_data_sources()
        return [
            {
                'key': key,
                'name': key,
                'table_name': config['table_name'],
                'description': config['table_des'],
                'columns_count': len(config['table_columns']),
                'database_type': config.get('database_type', 'unknown')
            }
            for key, config in sources.items()
        ]
    
    async def get_templates_list(self) -> List[Dict]:
        """异步获取模板列表（用于API返回）"""
        templates = await self.get_all_templates()
        return [
            {
                'id': template_id,
                'name': config['template_metadata']['name'],
                'summary': config['template_metadata']['summary']
            }
            for template_id, config in templates.items()
        ]
    
    async def search_data_sources(self, keyword: str) -> Dict:
        """异步搜索数据源"""
        all_sources = await self.get_all_data_sources()
        filtered_sources = {}
        
        keyword_lower = keyword.lower()
        for key, config in all_sources.items():
            if (keyword_lower in key.lower() or 
                keyword_lower in config.get('table_name', '').lower() or
                keyword_lower in config.get('table_des', '').lower()):
                filtered_sources[key] = config
        
        return filtered_sources
    
    def _sync_get_database_stats(self) -> Dict:
        """同步获取数据库统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM data_sources')
            sources_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM analysis_templates')
            templates_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM data_source_columns')
            columns_count = cursor.fetchone()['count']
            
            # 获取按数据库类型分组的统计
            cursor.execute('SELECT database_type, COUNT(*) as count FROM data_sources GROUP BY database_type')
            db_type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'data_sources_count': sources_count,
                'templates_count': templates_count,
                'total_columns_count': columns_count,
                'database_path': self.db_path,
                'database_type_stats': db_type_stats
            }

    async def get_database_stats(self) -> Dict:
        """异步获取数据库统计信息"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.db_executor, self._sync_get_database_stats)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db_executor'):
            self.db_executor.shutdown(wait=False)

    def _sync_add_data_source(self, source_key: str, table_name: str, table_des: str, table_order: str, table_columns: List[str], table_columns_names: List[str], database_type: str = "unknown") -> bool:
        """同步添加数据源配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 插入数据源基本信息
                cursor.execute('''
                    INSERT INTO data_sources (source_key, table_name, table_des, table_order, database_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (source_key, table_name, table_des, table_order, database_type, datetime.now().isoformat()))
                
                source_id = cursor.lastrowid
                
                # 插入列信息
                for i, (column_name, column_display_name) in enumerate(zip(table_columns, table_columns_names)):
                    cursor.execute('''
                        INSERT INTO data_source_columns (source_id, column_name, column_display_name, column_order)
                        VALUES (?, ?, ?, ?)
                    ''', (source_id, column_name, column_display_name, i))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"添加数据源失败: {e}")
            return False

    async def add_data_source(self, source_key: str, table_name: str, table_des: str, table_order: str, table_columns: List[str], table_columns_names: List[str], database_type: str = "unknown") -> bool:
        """异步添加数据源配置"""
        loop = asyncio.get_event_loop()
        func = partial(self._sync_add_data_source, source_key, table_name, table_des, table_order, table_columns, table_columns_names, database_type)
        return await loop.run_in_executor(self.db_executor, func)

    def _sync_update_data_source(self, source_key: str, table_name: str = None, table_des: str = None, table_order: str = None, table_columns: List[str] = None, table_columns_names: List[str] = None, database_type: str = None) -> bool:
        """同步更新数据源配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查数据源是否存在
                cursor.execute('SELECT id FROM data_sources WHERE source_key = ?', (source_key,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                source_id = row['id']
                
                # 构建更新SQL
                update_fields = []
                update_values = []
                
                if table_name is not None:
                    update_fields.append('table_name = ?')
                    update_values.append(table_name)
                if table_des is not None:
                    update_fields.append('table_des = ?')
                    update_values.append(table_des)
                if table_order is not None:
                    update_fields.append('table_order = ?')
                    update_values.append(table_order)
                if database_type is not None:
                    update_fields.append('database_type = ?')
                    update_values.append(database_type)
                
                if update_fields:
                    cursor.execute(f'''
                        UPDATE data_sources 
                        SET {', '.join(update_fields)}, updated_at = ?
                        WHERE source_key = ?
                    ''', update_values + [datetime.now().isoformat(), source_key])
                
                # 更新列信息（如果提供）
                if table_columns is not None and table_columns_names is not None:
                    # 删除现有列配置
                    cursor.execute('DELETE FROM data_source_columns WHERE source_id = ?', (source_id,))
                    
                    # 插入新的列配置
                    for i, (column_name, column_display_name) in enumerate(zip(table_columns, table_columns_names)):
                        cursor.execute('''
                            INSERT INTO data_source_columns (source_id, column_name, column_display_name, column_order)
                            VALUES (?, ?, ?, ?)
                        ''', (source_id, column_name, column_display_name, i))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"更新数据源失败: {e}")
            return False

    async def update_data_source(self, source_key: str, **kwargs) -> bool:
        """异步更新数据源配置"""
        loop = asyncio.get_event_loop()
        func = partial(self._sync_update_data_source, source_key, **kwargs)
        return await loop.run_in_executor(self.db_executor, func)
