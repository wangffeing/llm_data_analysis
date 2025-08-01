"""
创建.env文件的辅助脚本
"""
import os
import secrets
from pathlib import Path

def generate_secret_key(length: int = 32) -> str:
    """生成安全的密钥"""
    return secrets.token_urlsafe(length)

def create_env_file():
    """创建.env文件"""
    env_file = Path('.env')
    env_example_file = Path('.env.example')
    
    if env_file.exists():
        response = input(".env文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 读取.env.example作为模板
    if env_example_file.exists():
        with open(env_example_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        print(".env.example文件不存在")
        return
    
    # 生成新的密钥
    secret_key = generate_secret_key()
    
    # 替换默认值
    content = content.replace(
        'SECRET_KEY=your-secret-key-change-in-production-environment',
        f'SECRET_KEY={secret_key}'
    )
    
    # 提示用户输入必需的配置
    print("请输入以下必需的配置信息：")
    
    db_connection = input("数据库连接字符串 (DB_CONNECTION_STRING): ").strip()
    if db_connection:
        content = content.replace(
            'DB_CONNECTION_STRING=opengauss://username:password@host:port/database',
            f'DB_CONNECTION_STRING={db_connection}'
        )
    
    dashscope_key = input("DashScope API密钥 (DASHSCOPE_API_KEY): ").strip()
    if dashscope_key:
        content = content.replace(
            'DASHSCOPE_API_KEY=your-dashscope-api-key-here',
            f'DASHSCOPE_API_KEY={dashscope_key}'
        )
    
    lingyun_key = input("LingYun API密钥 (LINGYUN_API_KEY, 可选): ").strip()
    if lingyun_key:
        content = content.replace(
            'LINGYUN_API_KEY=your-lingyun-api-key-here',
            f'LINGYUN_API_KEY={lingyun_key}'
        )
    
    # 写入.env文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ .env文件已创建: {env_file.absolute()}")
    print("🔐 已生成新的SECRET_KEY")
    print("⚠️  请确保.env文件不要提交到版本控制系统")

if __name__ == "__main__":
    create_env_file()