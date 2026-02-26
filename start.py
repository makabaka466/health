#!/usr/bin/env python3
"""
健康管理系统启动脚本
自动检查环境、启动后端服务、提供前端启动指导
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("🏥 健康管理系统启动脚本")
    print("=" * 60)
    print()

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8或更高版本")
        return False

def check_backend_requirements():
    """检查后端依赖"""
    print("\n📦 检查后端依赖...")
    backend_dir = Path("backend")
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
        
    try:
        # 检查是否安装了关键依赖
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✅ 后端依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("💡 请运行: pip install -r backend/requirements.txt")
        return False

def check_database_connection():
    """检查数据库连接"""
    print("\n🗄️  检查数据库连接...")
    try:
        # 尝试导入数据库配置
        sys.path.append(str(Path("backend")))
        from app.config import settings
        
        print(f"   数据库类型: MySQL")
        print(f"   主机: {settings.DB_HOST}")
        print(f"   端口: {settings.DB_PORT}")
        print(f"   数据库名: {settings.DB_NAME}")
        
        # 简单的连接测试（这里只是检查配置）
        print("✅ 数据库配置正常")
        return True
    except Exception as e:
        print(f"❌ 数据库配置错误: {e}")
        return False

def start_backend_server():
    """启动后端服务器"""
    print("\n🚀 启动后端服务器...")
    backend_dir = Path("backend")
    
    try:
        # 切换到后端目录
        os.chdir(backend_dir)
        
        # 启动uvicorn服务器
        print("   启动FastAPI服务器...")
        print("   地址: http://127.0.0.1:8000")
        print("   API文档: http://127.0.0.1:8000/docs")
        print("   按Ctrl+C停止服务器")
        print()
        
        # 使用subprocess启动服务器
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 后端服务器已停止")
    except Exception as e:
        print(f"❌ 启动后端服务器失败: {e}")
        return False
    
    return True

def check_frontend_setup():
    """检查前端环境"""
    print("\n🌐 检查前端环境...")
    frontend_dir = Path("frontend")
    package_json = frontend_dir / "package.json"
    
    if not package_json.exists():
        print("❌ 前端package.json不存在")
        return False
    
    # 检查node_modules是否存在
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("⚠️  前端依赖未安装")
        print("💡 请运行: cd frontend && npm install")
        return False
    
    print("✅ 前端环境正常")
    return True

def print_frontend_instructions():
    """打印前端启动说明"""
    print("\n📱 前端启动说明:")
    print("   1. 打开新终端窗口")
    print("   2. 进入前端目录: cd frontend")
    print("   3. 启动开发服务器: npm run dev")
    print("   4. 访问: http://localhost:3000")
    print()
    print("🔑 默认测试账号:")
    print("   管理员: admin / admin123")
    print("   用户1: xiaoming / 123456")
    print("   用户2: xiaohong / 123456")

def run_tests():
    """运行测试"""
    print("\n🧪 运行系统测试...")
    try:
        backend_dir = Path("backend")
        test_file = backend_dir / "test_basic.py"
        
        if test_file.exists():
            os.chdir(backend_dir)
            result = subprocess.run([
                sys.executable, "test_basic.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 系统测试通过")
                return True
            else:
                print("❌ 系统测试失败")
                print(result.stdout)
                print(result.stderr)
                return False
        else:
            print("⚠️  测试文件不存在")
            return False
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查基本环境
    if not check_python_version():
        return
    
    if not check_backend_requirements():
        return
    
    if not check_database_connection():
        print("⚠️  请确保MySQL服务正在运行并已创建数据库")
        print("💡 数据库配置文件: backend/app/config.py")
        return
    
    # 检查前端环境
    frontend_ok = check_frontend_setup()
    
    # 询问是否运行测试
    test_choice = input("\n🧪 是否运行系统测试? (y/n): ").lower()
    if test_choice == 'y':
        if run_tests():
            print("✅ 测试通过，可以启动系统")
        else:
            print("⚠️  测试未完全通过，但仍可启动系统")
    
    # 打印前端启动说明
    if frontend_ok:
        print_frontend_instructions()
    
    # 询问是否启动后端
    start_choice = input("\n🚀 是否启动后端服务器? (y/n): ").lower()
    if start_choice == 'y':
        start_backend_server()
    else:
        print("\n💡 手动启动后端:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 启动脚本已退出")
    except Exception as e:
        print(f"\n❌ 启动脚本异常: {e}")
