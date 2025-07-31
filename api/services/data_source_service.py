import json
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DataSourceService:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "../data_sources_config.py")
        self.config_path = Path(config_path)
        
    def get_all_data_sources(self) -> Dict[str, Any]:
        """获取所有数据源"""
        try:
            # 动态导入数据源配置
            import importlib.util
            spec = importlib.util.spec_from_file_location("data_sources_config", self.config_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.DATA_SOURCES
        except Exception as e:
            logger.error(f"读取数据源配置失败: {e}")
            return {}
    
    def get_data_source(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个数据源"""
        data_sources = self.get_all_data_sources()
        return data_sources.get(name)
    
    def add_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        """添加数据源"""
        try:
            data_sources = self.get_all_data_sources()
            data_sources[name] = config
            return self._save_data_sources(data_sources)
        except Exception as e:
            logger.error(f"添加数据源失败: {e}")
            return False
    
    def update_data_source(self, name: str, config: Dict[str, Any]) -> bool:
        """更新数据源"""
        try:
            data_sources = self.get_all_data_sources()
            if name not in data_sources:
                return False
            data_sources[name] = config
            return self._save_data_sources(data_sources)
        except Exception as e:
            logger.error(f"更新数据源失败: {e}")
            return False
    
    def delete_data_source(self, name: str) -> bool:
        """删除数据源"""
        try:
            data_sources = self.get_all_data_sources()
            if name not in data_sources:
                return False
            del data_sources[name]
            return self._save_data_sources(data_sources)
        except Exception as e:
            logger.error(f"删除数据源失败: {e}")
            return False
    
    def _save_data_sources(self, data_sources: Dict[str, Any]) -> bool:
        """保存数据源配置到文件"""
        try:
            # 生成Python代码
            content = "# 数据源配置文件\nDATA_SOURCES = " + self._dict_to_python_code(data_sources)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"保存数据源配置失败: {e}")
            return False
    
    def _dict_to_python_code(self, obj: Any, indent: int = 0) -> str:
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            
            items = []
            for key, value in obj.items():
                key_str = repr(key)
                value_str = self._dict_to_python_code(value, indent + 1)
                items.append(f"{'    ' * (indent + 1)}{key_str}: {value_str}")
            
            return "{\n" + ",\n".join(items) + "\n" + "    " * indent + "}"
        
        elif isinstance(obj, list):
            if not obj:
                return "[]"
            
            items = []
            for item in obj:
                item_str = self._dict_to_python_code(item, indent + 1)
                items.append(f"{'    ' * (indent + 1)}{item_str}")
            
            return "[\n" + ",\n".join(items) + "\n" + "    " * indent + "]"
        else:
            return repr(obj)