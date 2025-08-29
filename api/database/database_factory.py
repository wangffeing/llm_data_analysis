"""
数据库工厂类
"""
from typing import Dict, Any
from .base_adapter import DatabaseAdapter
from .mysql_adapter import MySQLAdapter
from .sqlite_adapter import SQLiteAdapter
from .openguass_adapter import OpenGaussAdapter
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseFactory:
    """数据库工厂类"""
    
    @staticmethod
    def create_adapter(db_type: str, connection_config: Dict[str, Any]) -> DatabaseAdapter:
        """
        创建数据库适配器
        
        Args:
            db_type: 数据库类型 ('mysql', 'sqlite', 'opengauss')
            connection_config: 连接配置
            
        Returns:
            DatabaseAdapter: 数据库适配器实例
        """
        db_type = db_type.lower()
        
        if db_type == 'mysql':
            return MySQLAdapter(connection_config)
        elif db_type == 'sqlite':
            return SQLiteAdapter(connection_config)
        elif db_type == 'opengauss':
            return OpenGaussAdapter(connection_config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    @staticmethod
    def parse_connection_string(connection_string: str) -> tuple[str, Dict[str, Any]]:
        """
        解析连接字符串
        
        Args:
            connection_string: 数据库连接字符串
            
        Returns:
            tuple: (数据库类型, 连接配置)
        """
        try:
            # 解析连接字符串格式: protocol://user:password@host:port/database
            if '://' not in connection_string:
                raise ValueError("连接字符串格式错误")
            
            protocol, rest = connection_string.split('://', 1)
            
            # 特殊处理SQLite
            if protocol == 'sqlite':
                # 处理SQLite路径格式
                # sqlite:///path/to/file.db -> path/to/file.db (相对路径)
                # sqlite:///C:/path/to/file.db -> C:/path/to/file.db (绝对路径)
                db_path = rest
                
                # 移除多余的斜杠并正确处理路径
                if db_path.startswith('///'):
                    # 三个斜杠的情况
                    db_path = db_path[3:]  # 移除 ///
                    
                    # 在Windows上，检查是否是绝对路径格式 (如 C:/path)
                    if os.name == 'nt' and not (len(db_path) > 1 and db_path[1] == ':'):
                        # 不是 C: 格式，当作相对路径处理
                        pass
                    elif os.name != 'nt':
                        # Unix-like系统，添加根路径
                        db_path = '/' + db_path
                        
                elif db_path.startswith('//'):
                    # 两个斜杠的情况，移除多余的斜杠
                    db_path = db_path[2:]
                elif db_path.startswith('/'):
                    # 一个斜杠的情况，移除斜杠作为相对路径
                    db_path = db_path[1:]
                
                return 'sqlite', {'database': db_path}
            
            # 解析用户信息和主机信息
            if '@' in rest:
                user_info, host_info = rest.rsplit('@', 1)
                if ':' in user_info:
                    user, password = user_info.split(':', 1)
                else:
                    user, password = user_info, ''
            else:
                raise ValueError("连接字符串缺少用户信息")
            
            # 解析主机和数据库
            if '/' in host_info:
                host_port, database = host_info.split('/', 1)
            else:
                host_port, database = host_info, ''
            
            # 解析主机和端口
            if ':' in host_port:
                host, port = host_port.rsplit(':', 1)
                port = int(port)
            else:
                host = host_port
                # 默认端口
                if protocol == 'mysql':
                    port = 3306
                elif protocol == 'opengauss':
                    port = 5432
                else:
                    port = 5432
            
            config = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database,
                'connection_string': connection_string
            }
            
            # 映射协议名称
            if protocol in ['opengauss', 'postgresql', 'postgres']:
                db_type = 'opengauss'
            elif protocol == 'mysql':
                db_type = 'mysql'
            else:
                db_type = protocol
            
            return db_type, config
            
        except Exception as e:
            logger.error(f"解析连接字符串失败: {e}")
            raise ValueError(f"连接字符串解析错误: {e}")