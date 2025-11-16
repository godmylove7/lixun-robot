import os
from loguru import logger
from langchain_openai import ChatOpenAI  # 使用新的导入方式


class LLMConfig:
    def __init__(self):
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("LLM_MODEL", "qwen-turbo")

    def get_chat_model(self):
        """获取配置好的LLM模型"""
        try:
            # 配置DashScope（通义千问）
            llm = ChatOpenAI(
                model_name=self.llm_model,
                openai_api_key=self.dashscope_api_key,
                openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                temperature=0.1
            )
            logger.info(f"LLM model configured: {self.llm_model}")
            return llm
        except Exception as e:
            logger.error(f"Error configuring LLM: {e}")
            raise