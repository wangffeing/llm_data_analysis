import os
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from data_sources_config import DATA_SOURCES  # 导入独立的数据源配置

# 从环境变量读取敏感配置
def get_env_or_default(key: str, default: Any = None) -> Any:
    """从环境变量获取配置，如果不存在则使用默认值"""
    return os.getenv(key, default)

# 数据库连接配置
DB_CONFIG = {
    'connection_string': get_env_or_default(
        'DB_CONNECTION_STRING',
        'opengauss://og_fenxi:henz5u4wTqfR%Cu6@10.126.246.168:25400/fenxi'
    )
}

# API密钥配置
DASHSCOPE_API_KEY = get_env_or_default('DASHSCOPE_API_KEY', "sk-042607990c9942ca8865717388d109f2")
LINGYUN_API_KEY = get_env_or_default('LINGYUN_API_KEY', "")

class Config:
    """应用配置类"""
    
    def __init__(self):
        # 数据库配置
        self.db_config = DB_CONFIG
        self.data_sources = DATA_SOURCES
        
        # API密钥配置
        self.dashscope_api_key = DASHSCOPE_API_KEY
        self.lingyun_api_key = LINGYUN_API_KEY
        
        # SSE相关配置
        self.sse_batch_interval = float(get_env_or_default('SSE_BATCH_INTERVAL', 0.3))
        self.sse_max_batch_size = int(get_env_or_default('SSE_MAX_BATCH_SIZE', 8))
        self.sse_max_buffer_size = int(get_env_or_default('SSE_MAX_BUFFER_SIZE', 100))
        self.sse_heartbeat_interval = int(get_env_or_default('SSE_HEARTBEAT_INTERVAL', 30))
        
        # 服务器配置
        self.host = get_env_or_default('HOST', "0.0.0.0")
        self.port = int(get_env_or_default('PORT', 8000))
        self.debug = get_env_or_default('DEBUG', 'true').lower() == 'true'
        
        # 数据库连接池配置
        self.db_pool_max_connections = int(get_env_or_default('DB_POOL_MAX_CONNECTIONS', 10))
        self.db_pool_min_connections = int(get_env_or_default('DB_POOL_MIN_CONNECTIONS', 3))
        
        # TaskWeaver配置
        self.taskweaver_project_path = get_env_or_default(
            'TASKWEAVER_PROJECT_PATH', 
            os.path.join(os.path.dirname(__file__), "project")
        )
        
        # 日志配置
        self.log_level = get_env_or_default('LOG_LEVEL', 'INFO')
        self.log_file = get_env_or_default('LOG_FILE', None)
        
    def get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.db_config
        
    def get_data_sources(self) -> Dict[str, Any]:
        """获取数据源配置"""
        return self.data_sources
        
    def get_api_keys(self) -> Dict[str, str]:
        """获取API密钥配置"""
        return {
            'dashscope': self.dashscope_api_key,
            'lingyun': self.lingyun_api_key
        }
    
    def get_db_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return self.db_config['connection_string']
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证数据库连接字符串
        if not self.db_config.get('connection_string'):
            errors.append("数据库连接字符串未配置")
        
        # 验证TaskWeaver项目路径
        if not os.path.exists(self.taskweaver_project_path):
            errors.append(f"TaskWeaver项目路径不存在: {self.taskweaver_project_path}")
        
        # 验证端口号
        if not (1 <= self.port <= 65535):
            errors.append(f"端口号无效: {self.port}")
        
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
        
        return True

# 全局配置实例
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """获取配置实例（单例模式）"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate_config()  # 验证配置
    return _config_instance

def reload_config() -> Config:
    """重新加载配置"""
    global _config_instance
    _config_instance = None
    return get_config()
