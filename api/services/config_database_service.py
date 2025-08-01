import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime

class ConfigDatabaseService:
    """
    配置数据库服务类
    提供从SQLite数据库读取和管理配置数据的功能
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
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
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

    def get_all_data_sources(self) -> Dict:
        """获取所有数据源配置"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ds.*, 
                       GROUP_CONCAT(dsc.column_name ORDER BY dsc.column_order) as columns,
                       GROUP_CONCAT(dsc.column_display_name ORDER BY dsc.column_order) as column_names
                FROM data_sources ds
                LEFT JOIN data_source_columns dsc ON ds.id = dsc.source_id
                GROUP BY ds.id
                ORDER BY ds.source_key
            ''')
            
            sources = {}
            for row in cursor.fetchall():
                columns = row['columns'].split(',') if row['columns'] else []
                column_names = row['column_names'].split(',') if row['column_names'] else []
                
                sources[row['source_key']] = {
                    'table_name': row['table_name'],
                    'table_des': row['table_des'],
                    'table_order': row['table_order'],
                    'table_columns': columns,
                    'table_columns_names': column_names,
                    'database_type': self._safe_get(row, 'database_type', 'unknown')  # 修复兼容性问题
                }
            
            return sources
    
    def get_data_source(self, source_key: str) -> Optional[Dict]:
        """获取单个数据源配置"""
        sources = self.get_all_data_sources()
        return sources.get(source_key)
    
    def add_data_source(self, source_key: str, table_name: str, table_des: str = "", 
                       table_order: str = "", columns: List[str] = None, 
                       column_names: List[str] = None, database_type: str = "unknown") -> bool:
        """添加新的数据源配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 插入数据源基本信息，包含数据库类型
                cursor.execute('''
                    INSERT INTO data_sources 
                    (source_key, table_name, table_des, table_order, database_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (source_key, table_name, table_des, table_order, database_type, datetime.now(), datetime.now()))
                
                source_id = cursor.lastrowid
                
                # 插入列配置
                if columns:
                    for i, column_name in enumerate(columns):
                        display_name = column_names[i] if column_names and i < len(column_names) else column_name
                        cursor.execute('''
                            INSERT INTO data_source_columns 
                            (source_id, column_name, column_display_name, column_order)
                            VALUES (?, ?, ?, ?)
                        ''', (source_id, column_name, display_name, i + 1))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"添加数据源失败: {e}")
            return False
    
    def update_data_source(self, source_key: str, **kwargs) -> bool:
        """更新数据源配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取数据源ID
                cursor.execute('SELECT id FROM data_sources WHERE source_key = ?', (source_key,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                source_id = row['id']
                
                # 更新基本信息，包含数据库类型
                update_fields = []
                update_values = []
                
                for field in ['table_name', 'table_des', 'table_order', 'database_type']:
                    if field in kwargs:
                        update_fields.append(f"{field} = ?")
                        update_values.append(kwargs[field])
                
                if update_fields:
                    update_fields.append("updated_at = ?")
                    update_values.append(datetime.now())
                    update_values.append(source_key)
                    
                    cursor.execute(f'''
                        UPDATE data_sources 
                        SET {', '.join(update_fields)}
                        WHERE source_key = ?
                    ''', update_values)
                
                # 更新列配置
                if 'columns' in kwargs:
                    cursor.execute('DELETE FROM data_source_columns WHERE source_id = ?', (source_id,))
                    
                    columns = kwargs['columns']
                    column_names = kwargs.get('column_names', [])
                    
                    for i, column_name in enumerate(columns):
                        display_name = column_names[i] if i < len(column_names) else column_name
                        cursor.execute('''
                            INSERT INTO data_source_columns 
                            (source_id, column_name, column_display_name, column_order)
                            VALUES (?, ?, ?, ?)
                        ''', (source_id, column_name, display_name, i + 1))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"更新数据源失败: {e}")
            return False
    
    def delete_data_source(self, source_key: str) -> bool:
        """删除数据源配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM data_sources WHERE source_key = ?', (source_key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除数据源失败: {e}")
            return False
    
    def get_data_sources_by_database_type(self, database_type: str) -> Dict:
        """根据数据库类型获取数据源"""
        all_sources = self.get_all_data_sources()
        filtered_sources = {}
        
        for key, config in all_sources.items():
            if config.get('database_type', 'unknown') == database_type:
                filtered_sources[key] = config
        
        return filtered_sources
    
    def get_available_database_types(self) -> List[str]:
        """获取所有可用的数据库类型"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT database_type FROM data_sources WHERE database_type IS NOT NULL')
            return [row[0] for row in cursor.fetchall()]

    def get_all_templates(self) -> Dict:
        """获取所有模板配置"""
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
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """获取单个模板配置"""
        templates = self.get_all_templates()
        return templates.get(template_id)
    
    def get_data_sources_list(self) -> List[Dict]:
        """获取数据源列表（用于API返回）"""
        sources = self.get_all_data_sources()
        return [
            {
                'key': key,
                'name': key,
                'table_name': config['table_name'],
                'description': config['table_des'],
                'columns_count': len(config['table_columns']),
                'database_type': config.get('database_type', 'unknown')  # 这里使用普通字典的 .get() 方法
            }
            for key, config in sources.items()
        ]
    
    def get_templates_list(self) -> List[Dict]:
        """获取模板列表（用于API返回）"""
        templates = self.get_all_templates()
        return [
            {
                'id': template_id,
                'name': config['template_metadata']['name'],
                'summary': config['template_metadata']['summary']
            }
            for template_id, config in templates.items()
        ]
    
    def search_data_sources(self, keyword: str) -> Dict:
        """搜索数据源"""
        all_sources = self.get_all_data_sources()
        filtered_sources = {}
        
        keyword_lower = keyword.lower()
        for key, config in all_sources.items():
            if (keyword_lower in key.lower() or 
                keyword_lower in config.get('table_name', '').lower() or
                keyword_lower in config.get('table_des', '').lower()):
                filtered_sources[key] = config
        
        return filtered_sources
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
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