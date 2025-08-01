import os
import shutil
from datetime import datetime

def backup_env_file():
    """备份当前的 .env 文件"""
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ 已备份当前 .env 文件为: {backup_name}")
        return backup_name
    return None

def switch_to_sqlite():
    """切换到 SQLite 数据库"""
    print("🔄 切换到 SQLite 测试数据库...")
    
    # 备份当前配置
    backup_file = backup_env_file()
    
    # 读取当前 .env 文件
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.readlines()
    
    # 修改数据库连接字符串
    new_content = []
    db_connection_updated = False
    
    for line in env_content:
        if line.startswith('DB_CONNECTION_STRING='):
            new_content.append('DB_CONNECTION_STRING=sqlite:///test_database.db\n')
            db_connection_updated = True
            print("  ✅ 已更新 DB_CONNECTION_STRING 为 SQLite")
        else:
            new_content.append(line)
    
    # 如果没有找到 DB_CONNECTION_STRING，添加它
    if not db_connection_updated:
        new_content.append('DB_CONNECTION_STRING=sqlite:///test_database.db\n')
        print("  ✅ 已添加 DB_CONNECTION_STRING 为 SQLite")
    
    # 写入新的 .env 文件
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    
    print("✅ 成功切换到 SQLite 数据库!")
    return backup_file

def switch_to_opengauss():
    """切换回 OpenGauss 数据库"""
    print("🔄 切换回 OpenGauss 数据库...")
    
    # 备份当前配置
    backup_file = backup_env_file()
    
    # 读取当前 .env 文件
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.readlines()
    
    # 修改数据库连接字符串（使用示例 OpenGauss 连接）
    new_content = []
    db_connection_updated = False
    
    for line in env_content:
        if line.startswith('DB_CONNECTION_STRING='):
            # 这里使用一个示例 OpenGauss 连接字符串，您需要根据实际情况修改
            new_content.append('DB_CONNECTION_STRING=opengauss://username:password@localhost:5432/database_name\n')
            db_connection_updated = True
            print("  ✅ 已更新 DB_CONNECTION_STRING 为 OpenGauss")
        else:
            new_content.append(line)
    
    # 如果没有找到 DB_CONNECTION_STRING，添加它
    if not db_connection_updated:
        new_content.append('DB_CONNECTION_STRING=opengauss://username:password@localhost:5432/database_name\n')
        print("  ✅ 已添加 DB_CONNECTION_STRING 为 OpenGauss")
    
    # 写入新的 .env 文件
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    
    print("✅ 成功切换回 OpenGauss 数据库!")
    print("⚠️  请根据实际情况修改 OpenGauss 连接字符串")
    return backup_file

def show_current_config():
    """显示当前数据库配置"""
    print("📋 当前数据库配置:")
    
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('DB_CONNECTION_STRING='):
                    connection_string = line.strip().split('=', 1)[1]
                    if connection_string.startswith('sqlite:'):
                        print(f"  数据库类型: SQLite")
                        print(f"  连接字符串: {connection_string}")
                    elif connection_string.startswith('opengauss:'):
                        print(f"  数据库类型: OpenGauss")
                        print(f"  连接字符串: {connection_string}")
                    else:
                        print(f"  数据库类型: 未知")
                        print(f"  连接字符串: {connection_string}")
                    return
        print("  ❌ 未找到 DB_CONNECTION_STRING 配置")
    else:
        print("  ❌ 未找到 .env 文件")

def restore_backup(backup_file):
    """恢复备份的 .env 文件"""
    if backup_file and os.path.exists(backup_file):
        shutil.copy(backup_file, '.env')
        print(f"✅ 已恢复备份文件: {backup_file}")
        return True
    else:
        print("❌ 备份文件不存在")
        return False

def main():
    """主函数"""
    print("🗄️  数据库切换工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 切换到 SQLite 测试数据库")
        print("2. 切换回 OpenGauss 数据库")
        print("3. 显示当前数据库配置")
        print("4. 恢复备份文件")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == '1':
            # 检查测试数据库是否存在
            if not os.path.exists('test_database.db'):
                print("❌ 测试数据库不存在，请先运行 create_enhanced_sqlite_test_database.py")
                continue
            switch_to_sqlite()
            
        elif choice == '2':
            switch_to_opengauss()
            
        elif choice == '3':
            show_current_config()
            
        elif choice == '4':
            # 列出可用的备份文件
            backup_files = [f for f in os.listdir('.') if f.startswith('.env.backup.')]
            if backup_files:
                print("\n可用的备份文件:")
                for i, backup in enumerate(backup_files, 1):
                    print(f"  {i}. {backup}")
                
                try:
                    backup_choice = int(input("\n请选择要恢复的备份文件编号: ")) - 1
                    if 0 <= backup_choice < len(backup_files):
                        restore_backup(backup_files[backup_choice])
                    else:
                        print("❌ 无效的选择")
                except ValueError:
                    print("❌ 请输入有效的数字")
            else:
                print("❌ 没有找到备份文件")
                
        elif choice == '5':
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效的选择，请重新输入")

if __name__ == "__main__":
    main()