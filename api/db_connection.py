# 修复数据库连接函数名冲突
import py_opengauss
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

def create_db_connection():
    """创建数据库连接"""
    try:
        return py_opengauss.open(DB_CONFIG['connection_string'])
    except Exception as e:
        logger.error(f"数据库连接错误: {str(e)}")
        raise