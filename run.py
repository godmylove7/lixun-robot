#!/usr/bin/env python3
"""
Lixun Robot - 问答过程完全无日志干扰的命令行版本
"""
import sys
import os
import subprocess
import importlib.util
from typing import List, Dict, Any
import logging
import warnings


def setup_selective_logging():
    """设置选择性日志，只在初始化阶段显示日志"""
    # 设置日志级别，但不完全禁用
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langsmith").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # 禁用pydantic的特定警告
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
    warnings.filterwarnings("ignore", category=FutureWarning)


def check_dependencies():
    """检查并安装缺失的依赖"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'langchain_core': 'langchain-core',
        'langchain_community': 'langchain-community',
        'langchain_openai': 'langchain-openai',
        'langchain_text_splitters': 'langchain-text-splitters',
        'langgraph': 'langgraph',
        'openai': 'openai',
        'faiss': 'faiss-cpu',
        'pypdf': 'pypdf',
        'docx': 'python-docx',
        'pydantic': 'pydantic',
        'loguru': 'loguru',
        'dotenv': 'python-dotenv',
        'dashscope': 'dashscope'
    }

    missing_packages = []
    for package_name, pip_name in required_packages.items():
        if importlib.util.find_spec(package_name) is None:
            missing_packages.append(pip_name)

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("正在安装依赖...")
        try:
            subprocess.run([
                               sys.executable, "-m", "uv", "pip", "install",
                               "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"
                           ] + missing_packages, check=True)
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    else:
        print("✅ 所有依赖已安装")

    return True


def setup_environment():
    """设置环境"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    os.environ["PYTHONPATH"] = current_dir
    print(f"📁 项目路径: {current_dir}")


def check_environment_variables():
    """检查必要的环境变量"""
    from dotenv import load_dotenv
    import os

    # 重新加载环境变量
    load_dotenv(override=True)

    required_vars = {
        'DASHSCOPE_API_KEY': 'DashScope API密钥',
    }

    missing_vars = []
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"{var_name} ({description})")
        else:
            print(f"✅ {var_name}: 已设置")

    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        return False

    print("✅ 环境变量检查通过")
    return True


class DocumentLoader:
    """文档加载器 - 自动加载data/documents中的所有文件"""

    def __init__(self):
        # 在方法内部导入，避免循环导入问题
        from core.document_processor import DocumentProcessor
        from core.vector_store import VectorStoreManager
        from core.conversation_manager import ConversationManager

        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager()
        self.conversation_manager = ConversationManager()
        self.chat_agent = None

    def load_all_documents(self):
        """加载data/documents中的所有文档"""
        # 在方法内部导入ChatAgent，确保所有依赖已加载
        from chains.chat_agent import ChatAgent

        documents_dir = "data/documents"
        if not os.path.exists(documents_dir):
            print(f"❌ 文档目录不存在: {documents_dir}")
            return False

        supported_extensions = {'.pdf', '.docx', '.md', '.txt'}
        document_files = []

        # 扫描文档目录
        for filename in os.listdir(documents_dir):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_extensions:
                document_files.append(filename)

        if not document_files:
            print("❌ 在data/documents目录中未找到支持的文档文件")
            return False

        print(f"📚 找到 {len(document_files)} 个文档文件:")
        for doc in document_files:
            print(f"   - {doc}")

        all_documents = []
        total_chunks = 0

        # 处理每个文档
        for filename in document_files:
            try:
                file_path = os.path.join(documents_dir, filename)
                file_ext = os.path.splitext(filename)[1].lower()[1:]  # 去掉点号

                print(f"🔍 处理文档: {filename}")

                # 提取文本
                text = self.document_processor.extract_text(file_path, file_ext)

                # 分割文档
                documents = self.document_processor.split_documents(text, {
                    "filename": filename,
                    "file_type": file_ext
                })

                all_documents.extend(documents)
                total_chunks += len(documents)
                print(f"   ✅ 成功处理，分割为 {len(documents)} 个片段")

            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                continue

        if not all_documents:
            print("❌ 所有文档处理失败")
            return False

        # 创建向量存储
        print(f"\n📊 创建向量索引...")
        self.vector_store.create_vector_store(all_documents)
        self.vector_store.save_vector_store("data/vector_store")

        # 初始化聊天代理
        self.chat_agent = ChatAgent(self.vector_store, self.conversation_manager)

        print(f"✅ 文档加载完成! 共处理 {len(document_files)} 个文件，{total_chunks} 个文本片段")
        return True

    def chat_loop(self):
        """命令行聊天循环"""
        if not self.chat_agent:
            print("❌ 聊天代理未初始化")
            return

        conversation_id = "cli_session"

        print("\n" + "=" * 50)
        print("🤖 Lixun Robot 聊天机器人已就绪!")
        print("💡 支持的指令:")
        print("  • 输入问题开始对话")
        print("  • 输入 'history' 查看对话历史")
        print("  • 输入 'clear' 清空对话历史")
        print("  • 输入 'quit' 或 'exit' 退出")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n💬 你的问题: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见!")
                    break
                elif user_input.lower() == 'history':
                    self._show_conversation_history(conversation_id)
                elif user_input.lower() == 'clear':
                    self.conversation_manager.clear_conversation(conversation_id)
                    print("🗑️  对话历史已清空")
                elif user_input:
                    self._process_chat(user_input, conversation_id)
                else:
                    print("❌ 请输入有效的问题")

            except KeyboardInterrupt:
                print("\n👋 用户中断，再见!")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")

    def _show_conversation_history(self, conversation_id: str):
        """显示格式化的对话历史"""
        history = self.conversation_manager.get_conversation_history(conversation_id)
        if not history:
            print("📝 暂无对话历史")
            return

        print("\n" + "📋 对话历史 ".ljust(50, "="))

        round_number = 1
        i = 0
        while i < len(history):
            # 用户提问
            if i < len(history) and history[i]["role"] == "user":
                print(f"\n👤 第{round_number}轮提问:")
                print(f"   {history[i]['content']}")
                i += 1

            # AI回答
            if i < len(history) and history[i]["role"] == "assistant":
                print(f"🤖 回答:")
                answer = history[i]['content']
                print(f"   {answer}")

                # 显示引用信息
                if history[i].get("metadata", {}).get("citations"):
                    citations = history[i]["metadata"]["citations"]
                    print(f"   📚 引用 {len(citations)} 个文档片段")
                i += 1

            round_number += 1

        print("=" * 50)

    def _process_chat(self, question: str, conversation_id: str):
        """处理聊天请求并美化输出"""
        print("💭 思考中...", end="", flush=True)

        try:
            # 临时禁用所有日志输出
            import logging
            import loguru

            # 保存原始日志状态
            original_logging_level = logging.getLogger().level
            original_loguru_sinks = []

            # 禁用标准logging
            logging.disable(logging.CRITICAL)

            # 禁用loguru的所有sink
            for handler_id in list(loguru.logger._core.handlers):
                original_loguru_sinks.append(handler_id)
                loguru.logger.remove(handler_id)

            result = self.chat_agent.chat(question, conversation_id)

            # 恢复日志输出
            logging.disable(logging.NOTSET)
            logging.getLogger().setLevel(original_logging_level)

            # 重新添加loguru sink（使用默认配置）
            if not loguru.logger._core.handlers:
                loguru.logger.add(sys.stderr, level="INFO")

            print("\r✅ 回答生成完成!" + " " * 20)  # 清除"思考中"提示

            # 显示回答
            print(f"\n🤖 {result['answer']}")

            # 显示引用信息 - 确保这部分存在
            if result.get('citations'):
                print(f"\n📖 引用来源:")
                for citation in result['citations']:
                    filename = citation.get('metadata', {}).get('filename', '未知文件')
                    doc_content = citation['content'].strip()

                    # 显示完整内容，不截断
                    print(f"   📄 来自《{filename}》:")
                    print(f"      {doc_content}")
                    print()  # 空行分隔

            # 显示检索统计
            if result.get('retrieved_docs'):
                print(f"🔍 本次检索参考了 {len(result['retrieved_docs'])} 个相关文档片段")

        except Exception as e:
            # 恢复日志输出
            import logging
            import loguru

            logging.disable(logging.NOTSET)
            if not loguru.logger._core.handlers:
                loguru.logger.add(sys.stderr, level="INFO")

            print(f"\r❌ 回答生成失败!" + " " * 20)
            print(f"错误详情: {e}")

def main():
    """主启动函数"""
    print("🚀 启动 Lixun Robot...")

    # 设置选择性日志
    setup_selective_logging()

    if not check_dependencies():
        print("❌ 依赖检查失败，无法启动服务")
        input("按回车键退出...")
        return

    setup_environment()

    # 添加环境变量检查
    if not check_environment_variables():
        print("❌ 环境变量配置失败")
        input("按回车键退出...")
        return

    try:
        # 初始化文档加载器
        loader = DocumentLoader()

        print("\n📥 开始加载文档...")
        if not loader.load_all_documents():
            print("❌ 文档加载失败，无法启动聊天功能")
            input("按回车键退出...")
            return

        # 启动命令行聊天
        loader.chat_loop()

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()