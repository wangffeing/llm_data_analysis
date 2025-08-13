import re
import html
from typing import Any, Dict, List, Union, Optional
from fastapi import HTTPException

class InputValidator:
    """输入验证和清理工具"""
    
    # 危险模式
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script标签
        r'javascript:',  # JavaScript协议
        r'vbscript:',   # VBScript协议
        r'on\w+\s*=',   # 事件处理器
        r'<iframe\b',   # iframe标签
        r'<object\b',   # object标签
        r'<embed\b',    # embed标签
        r'<link\b',     # link标签
        r'<meta\b',     # meta标签
        r'<style\b',    # style标签
        r'<form\b',     # form标签
        r'<input\b',    # input标签
        r'<textarea\b', # textarea标签
        r'<button\b',   # button标签
        r'<select\b',   # select标签
        r'<option\b',   # option标签
    ]
    
    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        r'\bunion\s+select\b',
        r'\bselect\s+.*\bfrom\b',
        r'\binsert\s+into\b',
        r'\bupdate\s+.*\bset\b',
        r'\bdelete\s+from\b',
        r'\bdrop\s+table\b',
        r'\balter\s+table\b',
        r'\bcreate\s+table\b',
        r'\bexec\s*\(',
        r'\bexecute\s*\(',
        r';.*--',
        r'\/\*.*\*\/',
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """清理字符串输入"""
        if not isinstance(value, str):
            return str(value)
        
        # 限制长度
        if len(value) > max_length:
            raise HTTPException(status_code=400, detail=f"输入长度超过限制 ({max_length} 字符)")
        
        # HTML编码
        sanitized = html.escape(value)
        
        # 检查危险模式
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise HTTPException(status_code=400, detail="输入包含不安全内容")
        
        # 检查SQL注入模式
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise HTTPException(status_code=400, detail="输入包含可疑的SQL内容")
        
        # 移除控制字符（保留换行和制表符）
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        return sanitized
    
    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """验证会话ID格式"""
        if not session_id:
            raise HTTPException(status_code=400, detail="会话ID不能为空")
        
        # 检查UUID格式
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, session_id, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="无效的会话ID格式")
        
        return session_id
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> str:
        """验证表名"""
        if not table_name:
            raise HTTPException(status_code=400, detail="表名不能为空")
        
        # 只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', table_name):
            raise HTTPException(status_code=400, detail="表名格式无效")
        
        if len(table_name) > 64:
            raise HTTPException(status_code=400, detail="表名过长")
        
        return table_name
    
    @classmethod
    def validate_column_name(cls, column_name: str) -> str:
        """验证列名"""
        if not column_name:
            raise HTTPException(status_code=400, detail="列名不能为空")
        
        # 只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', column_name):
            raise HTTPException(status_code=400, detail="列名格式无效")
        
        if len(column_name) > 64:
            raise HTTPException(status_code=400, detail="列名过长")
        
        return column_name
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
        """清理字典数据"""
        if max_depth <= 0:
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # 清理键名
            safe_key = cls.sanitize_string(str(key), 100)
            
            # 清理值
            if isinstance(value, str):
                sanitized[safe_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = cls.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = cls.sanitize_list(value, max_depth - 1)
            elif isinstance(value, (int, float, bool)):
                sanitized[safe_key] = value
            else:
                sanitized[safe_key] = cls.sanitize_string(str(value))
        
        return sanitized
    
    @classmethod
    def sanitize_list(cls, data: List[Any], max_depth: int = 5) -> List[Any]:
        """清理列表数据"""
        if max_depth <= 0:
            return []
        
        sanitized = []
        for item in data[:100]:  # 限制列表长度
            if isinstance(item, str):
                sanitized.append(cls.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, max_depth - 1))
            elif isinstance(item, (int, float, bool)):
                sanitized.append(item)
            else:
                sanitized.append(cls.sanitize_string(str(item)))
        
        return sanitized

# 创建装饰器用于自动验证输入
def validate_input(func):
    """输入验证装饰器"""
    def wrapper(*args, **kwargs):
        # 清理所有字符串参数
        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                clean_args.append(InputValidator.sanitize_string(arg))
            elif isinstance(arg, dict):
                clean_args.append(InputValidator.sanitize_dict(arg))
            elif isinstance(arg, list):
                clean_args.append(InputValidator.sanitize_list(arg))
            else:
                clean_args.append(arg)
        
        clean_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                clean_kwargs[key] = InputValidator.sanitize_string(value)
            elif isinstance(value, dict):
                clean_kwargs[key] = InputValidator.sanitize_dict(value)
            elif isinstance(value, list):
                clean_kwargs[key] = InputValidator.sanitize_list(value)
            else:
                clean_kwargs[key] = value
        
        return func(*clean_args, **clean_kwargs)
    
    return wrapper