import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class TemplateDatabaseService:
    """
    模板数据库服务类
    提供从SQLite数据库读取和管理模板配置的功能
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
                required_columns = [dict(row) for row in cursor.fetchall()]
                
                # 获取可选列
                cursor.execute('''
                    SELECT column_name as name, column_type as type, description 
                    FROM template_optional_columns 
                    WHERE template_id = ?
                ''', (template_row['id'],))
                optional_columns = [dict(row) for row in cursor.fetchall()]
                
                # 获取执行步骤
                cursor.execute('''
                    SELECT prompt, save_to_variable 
                    FROM template_execution_steps 
                    WHERE template_id = ? 
                    ORDER BY step_order
                ''', (template_row['id'],))
                steps = [dict(row) for row in cursor.fetchall()]
                
                # 获取输出文件
                cursor.execute('''
                    SELECT file_type as type, title, source_variable, tool 
                    FROM template_output_files 
                    WHERE template_id = ?
                ''', (template_row['id'],))
                files = [dict(row) for row in cursor.fetchall()]
                
                templates[template_id] = {
                    "template_metadata": {
                        "id": template_id,
                        "name": template_row['template_name'],
                        "summary": template_row['summary']
                    },
                    "data_schema": {
                        "required_columns": required_columns,
                        "optional_columns": optional_columns
                    },
                    "execution_plan": {
                        "analysis_goal": template_row['analysis_goal'],
                        "steps": steps
                    },
                    "output_specification": {
                        "insights_template": template_row['insights_template'],
                        "files": files
                    }
                }
            
            return templates
    
    def add_template(self, template_id: str, template_config: Dict) -> bool:
        """添加新模板"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                metadata = template_config.get('template_metadata', {})
                execution_plan = template_config.get('execution_plan', {})
                output_spec = template_config.get('output_specification', {})
                data_schema = template_config.get('data_schema', {})
                
                # 插入模板基本信息
                cursor.execute('''
                    INSERT INTO analysis_templates 
                    (template_id, template_name, summary, analysis_goal, insights_template, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_id,
                    metadata.get('name'),
                    metadata.get('summary'),
                    execution_plan.get('analysis_goal'),
                    output_spec.get('insights_template'),
                    datetime.now(),
                    datetime.now()
                ))
                
                db_template_id = cursor.lastrowid
                
                # 插入必需列
                for col in data_schema.get('required_columns', []):
                    cursor.execute('''
                        INSERT INTO template_required_columns 
                        (template_id, column_name, column_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, col['name'], col['type'], col['description']))
                
                # 插入可选列
                for col in data_schema.get('optional_columns', []):
                    cursor.execute('''
                        INSERT INTO template_optional_columns 
                        (template_id, column_name, column_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, col['name'], col['type'], col['description']))
                
                # 插入执行步骤
                for i, step in enumerate(execution_plan.get('steps', []), 1):
                    cursor.execute('''
                        INSERT INTO template_execution_steps 
                        (template_id, step_order, prompt, save_to_variable)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, i, step['prompt'], step.get('save_to_variable')))
                
                # 插入输出文件
                for file_spec in output_spec.get('files', []):
                    cursor.execute('''
                        INSERT INTO template_output_files 
                        (template_id, file_type, title, source_variable, tool)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (db_template_id, file_spec['type'], file_spec['title'], 
                          file_spec.get('source_variable'), file_spec.get('tool')))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"添加模板失败: {e}")
            return False
    
    def update_template(self, template_id: str, template_config: Dict) -> bool:
        """更新模板"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取模板ID
                cursor.execute('SELECT id FROM analysis_templates WHERE template_id = ?', (template_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                db_template_id = row['id']
                
                # 删除旧的关联数据
                cursor.execute('DELETE FROM template_required_columns WHERE template_id = ?', (db_template_id,))
                cursor.execute('DELETE FROM template_optional_columns WHERE template_id = ?', (db_template_id,))
                cursor.execute('DELETE FROM template_execution_steps WHERE template_id = ?', (db_template_id,))
                cursor.execute('DELETE FROM template_output_files WHERE template_id = ?', (db_template_id,))
                
                # 更新基本信息
                metadata = template_config.get('template_metadata', {})
                execution_plan = template_config.get('execution_plan', {})
                output_spec = template_config.get('output_specification', {})
                
                cursor.execute('''
                    UPDATE analysis_templates 
                    SET template_name = ?, summary = ?, analysis_goal = ?, 
                        insights_template = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    metadata.get('name'),
                    metadata.get('summary'),
                    execution_plan.get('analysis_goal'),
                    output_spec.get('insights_template'),
                    datetime.now(),
                    db_template_id
                ))
                
                # 重新插入关联数据（使用add_template中的逻辑）
                data_schema = template_config.get('data_schema', {})
                
                # 插入必需列
                for col in data_schema.get('required_columns', []):
                    cursor.execute('''
                        INSERT INTO template_required_columns 
                        (template_id, column_name, column_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, col['name'], col['type'], col['description']))
                
                # 插入可选列
                for col in data_schema.get('optional_columns', []):
                    cursor.execute('''
                        INSERT INTO template_optional_columns 
                        (template_id, column_name, column_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, col['name'], col['type'], col['description']))
                
                # 插入执行步骤
                for i, step in enumerate(execution_plan.get('steps', []), 1):
                    cursor.execute('''
                        INSERT INTO template_execution_steps 
                        (template_id, step_order, prompt, save_to_variable)
                        VALUES (?, ?, ?, ?)
                    ''', (db_template_id, i, step['prompt'], step.get('save_to_variable')))
                
                # 插入输出文件
                for file_spec in output_spec.get('files', []):
                    cursor.execute('''
                        INSERT INTO template_output_files 
                        (template_id, file_type, title, source_variable, tool)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (db_template_id, file_spec['type'], file_spec['title'], 
                          file_spec.get('source_variable'), file_spec.get('tool')))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"更新模板失败: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM analysis_templates WHERE template_id = ?', (template_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False