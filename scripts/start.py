#!/usr/bin/env python3
"""
启动脚本 - 自动检查环境并启动机器人
"""
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def main():
    # 先运行环境检查
    from scripts.check_env import main as check_env

    print("🚀 启动 Lixun Robot...")

    if check_env():
        print("\n" + "=" * 50)
        print("🤖 启动聊天机器人...")
        print("=" * 50)

        # 导入并运行主程序
        try:
            from run import main as run_main
            run_main()
        except KeyboardInterrupt:
            print("\n👋 再见!")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            sys.exit(1)
    else:
        print("❌ 环境检查失败，无法启动")
        sys.exit(1)


if __name__ == "__main__":
    main()