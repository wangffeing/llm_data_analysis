import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def get_env_or_default(key: str, default: Any = None) -> Any:
    """从环境变量获取配置，如果不存在则使用默认值"""
    return os.getenv(key, default)

def get_env_required(key: str) -> str:
    """从环境变量获取必需的配置，如果不存在则抛出异常"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"必需的环境变量 {key} 未设置")
    return value

class Config:
    """应用配置类 - 所有敏感信息从环境变量读取"""
    
    def __init__(self):
        # 数据库配置 - 从环境变量读取
        self.db_connection_string = get_env_required('DB_CONNECTION_STRING')
        
        # 配置数据库模式开关
        self.use_database_config = get_env_or_default('USE_DATABASE_CONFIG', 'true').lower() == 'true'
        self.config_db_path = get_env_or_default('CONFIG_DB_PATH', 'config_database.db')
        
        # API密钥配置 - 从环境变量读取
        self.dashscope_api_key = get_env_or_default('DASHSCOPE_API_KEY', '')
        self.lingyun_api_key = get_env_or_default('LINGYUN_API_KEY', '')
        
        # 权限管理配置
        self.enable_auth = get_env_or_default('ENABLE_AUTH', 'false').lower() == 'true'
        self.admin_api_key = get_env_or_default('ADMIN_API_KEY', '')
        
        # 用户验证配置
        self.enable_user_verification = get_env_or_default('ENABLE_USER_VERIFICATION', 'false').lower() == 'true'
        self.user_verification_api_url = get_env_or_default('USER_VERIFICATION_API_URL', '')
        self.user_verification_api_timeout = int(get_env_or_default('USER_VERIFICATION_API_TIMEOUT', '30'))
        self.user_verification_api_token = get_env_or_default('USER_VERIFICATION_API_TOKEN', '')
        
        # SSE相关配置
        self.sse_batch_interval = float(get_env_or_default('SSE_BATCH_INTERVAL', '0.3'))
        self.sse_max_batch_size = int(get_env_or_default('SSE_MAX_BATCH_SIZE', '8'))
        self.sse_max_buffer_size = int(get_env_or_default('SSE_MAX_BUFFER_SIZE', '100'))
        self.sse_heartbeat_interval = int(get_env_or_default('SSE_HEARTBEAT_INTERVAL', '30'))
        
        # 服务器配置
        self.host = get_env_or_default('HOST', '0.0.0.0')
        self.port = int(get_env_or_default('PORT', '8000'))
        self.debug = get_env_or_default('DEBUG', 'false').lower() == 'true'
        
        # 数据库连接池配置
        self.db_pool_max_connections = int(get_env_or_default('DB_POOL_MAX_CONNECTIONS', '10'))
        self.db_pool_min_connections = int(get_env_or_default('DB_POOL_MIN_CONNECTIONS', '3'))
        
        # TaskWeaver配置
        self.taskweaver_project_path = get_env_or_default(
            'TASKWEAVER_PROJECT_PATH', 
            os.path.join(os.path.dirname(__file__), "project")
        )
        
        # 日志配置
        self.log_level = get_env_or_default('LOG_LEVEL', 'INFO')
        self.log_file = get_env_or_default('LOG_FILE', None)
        
        # 安全配置
        self.secret_key = get_env_or_default('SECRET_KEY', 'your-secret-key-change-in-production')
        self.allowed_hosts = get_env_or_default('ALLOWED_HOSTS', '*').split(',')
        
        # 文件上传配置
        self.max_upload_size = int(get_env_or_default('MAX_UPLOAD_SIZE', str(50 * 1024 * 1024)))  # 50MB
        self.upload_dir = get_env_or_default('UPLOAD_DIR', 'uploads')
        
    def get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'connection_string': self.db_connection_string
        }
        
    def get_data_sources(self) -> Dict[str, Any]:
        """获取数据源配置 - 从SQLite数据库读取"""
        import asyncio
        from services.config_database_service import ConfigDatabaseService
        config_service = ConfigDatabaseService(self.config_db_path)
        # 修复：使用 asyncio.run 来运行异步方法
        return asyncio.run(config_service.get_all_data_sources())
        
    def get_api_keys(self) -> Dict[str, str]:
        """获取API密钥配置"""
        return {
            'dashscope': self.dashscope_api_key,
            'lingyun': self.lingyun_api_key
        }
    
    def get_db_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return self.db_connection_string
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证数据库连接字符串
        if not self.db_connection_string:
            errors.append("数据库连接字符串未配置")
        
        # 验证API密钥
        if not self.dashscope_api_key:
            errors.append("DASHSCOPE_API_KEY 未配置")
        
        # 验证权限管理配置
        if self.enable_auth and not self.admin_api_key:
            errors.append("启用权限管理时必须设置 ADMIN_API_KEY")
        
        # 验证配置数据库文件
        if not os.path.exists(self.config_db_path):
            errors.append(f"配置数据库文件不存在: {self.config_db_path}")
        
        # 验证TaskWeaver项目路径
        if not os.path.exists(self.taskweaver_project_path):
            errors.append(f"TaskWeaver项目路径不存在: {self.taskweaver_project_path}")
        
        # 验证端口号
        if not (1 <= self.port <= 65535):
            errors.append(f"端口号无效: {self.port}")
        
        # 验证上传目录
        if not os.path.exists(self.upload_dir):
            try:
                os.makedirs(self.upload_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建上传目录 {self.upload_dir}: {e}")
        
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
        
        return True
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return get_env_or_default('ENVIRONMENT', 'development').lower() == 'production'
    
    def get_cors_origins(self) -> list:
        """获取CORS允许的源"""
        origins = get_env_or_default('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
        return [origin.strip() for origin in origins.split(',')]

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
