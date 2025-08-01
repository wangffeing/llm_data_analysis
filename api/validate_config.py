"""
配置验证脚本
用于检查环境变量配置是否正确
"""
import os
from dotenv import load_dotenv

def validate_environment():
    """验证环境配置"""
    load_dotenv()
    
    print("🔍 正在验证环境配置...")
    
    # 必需的环境变量
    required_vars = [
        'DB_CONNECTION_STRING',
        'DASHSCOPE_API_KEY',
    ]
    
    # 可选的环境变量
    optional_vars = [
        'LINGYUN_API_KEY',
        'SECRET_KEY',
        'HOST',
        'PORT',
        'DEBUG',
        'USE_DATABASE_CONFIG',
        'CONFIG_DB_PATH',
    ]
    
    errors = []
    warnings = []
    
    # 检查必需变量
    print("\n📋 检查必需的环境变量:")
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            errors.append(f"❌ {var} 未设置")
            print(f"  ❌ {var}: 未设置")
        else:
            # 隐藏敏感信息
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
    
    # 检查可选变量
    print("\n📋 检查可选的环境变量:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            warnings.append(f"⚠️  {var} 未设置，将使用默认值")
            print(f"  ⚠️  {var}: 未设置 (将使用默认值)")
    
    # 特殊检查
    print("\n🔍 特殊检查:")
    
    # 检查数据库连接字符串格式
    db_conn = os.getenv('DB_CONNECTION_STRING')
    if db_conn:
        if '://' in db_conn and '@' in db_conn:
            print("  ✅ 数据库连接字符串格式正确")
        else:
            errors.append("❌ 数据库连接字符串格式可能不正确")
            print("  ❌ 数据库连接字符串格式可能不正确")
    
    # 检查端口号
    port = os.getenv('PORT', '8000')
    try:
        port_num = int(port)
        if 1 <= port_num <= 65535:
            print(f"  ✅ 端口号有效: {port_num}")
        else:
            errors.append(f"❌ 端口号无效: {port_num}")
            print(f"  ❌ 端口号无效: {port_num}")
    except ValueError:
        errors.append(f"❌ 端口号不是有效数字: {port}")
        print(f"  ❌ 端口号不是有效数字: {port}")
    
    # 检查配置数据库文件
    config_db_path = os.getenv('CONFIG_DB_PATH', 'config_database.db')
    if os.path.exists(config_db_path):
        print(f"  ✅ 配置数据库文件存在: {config_db_path}")
    else:
        warnings.append(f"⚠️  配置数据库文件不存在: {config_db_path}")
        print(f"  ⚠️  配置数据库文件不存在: {config_db_path}")
    
    # 输出结果
    print("\n" + "="*50)
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ 配置验证通过!")
        if warnings:
            print("\n⚠️  警告:")
            for warning in warnings:
                print(f"  {warning}")
        return True

if __name__ == "__main__":
    success = validate_environment()
    exit(0 if success else 1)