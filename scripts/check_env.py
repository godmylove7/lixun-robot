#!/usr/bin/env python3
"""
环境检查和依赖安装脚本
"""
import sys
import os
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python版本: {sys.version}")
        return True
    else:
        print(f"❌ 需要Python 3.10+，当前版本: {sys.version}")
        return False


def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'langchain_core': 'langchain-core',
        'langchain_community': 'langchain-community',
        'langchain_openai': 'langchain-openai',
        'langchain_text_splitters': 'langchain-text-splitters',
        'langgraph': 'langgraph',
        'pypdf': 'pypdf',
        'docx': 'python-docx',
        'faiss': 'faiss-cpu',
        'pydantic': 'pydantic',
        'loguru': 'loguru',
        'dotenv': 'python-dotenv',
        'dashscope': 'dashscope',
        'fastapi': 'fastapi',  # 为将来Web版本保留
        'uvicorn': 'uvicorn',  # 为将来Web版本保留
    }

    missing = []
    for package_name, pip_name in required_packages.items():
        if importlib.util.find_spec(package_name) is None:
            missing.append(pip_name)
            print(f"❌ 缺少: {package_name} ({pip_name})")
        else:
            print(f"✅ 已安装: {package_name}")

    return missing


def check_environment_variables():
    """检查环境变量"""
    required_vars = ['DASHSCOPE_API_KEY']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ 环境变量未设置: {var}")
        else:
            print(f"✅ 环境变量已设置: {var}")

    return missing_vars


def install_dependencies(missing_packages):
    """安装缺失的依赖"""
    if not missing_packages:
        return True

    print(f"\n📦 正在安装缺失的依赖: {', '.join(missing_packages)}")
    try:
        # 使用uv安装
        subprocess.run([
                           sys.executable, "-m", "uv", "pip", "install",
                           "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
                       ] + missing_packages, check=True)
        print("✅ 依赖安装完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def setup_data_directories():
    """创建必要的数据目录"""
    directories = ['data/documents', 'data/vector_store', 'logs']

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")


def main():
    print("🔍 Lixun Robot 环境检查...")
    print("=" * 50)

    # 检查Python版本
    if not check_python_version():
        return False

    print("\n📦 检查依赖包...")
    missing_packages = check_dependencies()

    print("\n🔑 检查环境变量...")
    missing_vars = check_environment_variables()

    print("\n📁 创建数据目录...")
    setup_data_directories()

    # 安装缺失的依赖
    if missing_packages:
        if not install_dependencies(missing_packages):
            return False

    # 总结
    print("\n" + "=" * 50)
    if not missing_packages and not missing_vars:
        print("🎉 所有检查通过！可以运行 Lixun Robot 了!")
        print("💡 运行命令: uv run python run.py")
        return True
    else:
        if missing_vars:
            print(f"⚠️  请设置环境变量: {', '.join(missing_vars)}")
            print("💡 创建 .env 文件或设置系统环境变量")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)