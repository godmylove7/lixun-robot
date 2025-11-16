import os
from typing import List
from loguru import logger

try:
    from langchain_community.embeddings import DashScopeEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise


class VectorStoreManager:
    def __init__(self, embeddings_model: str = "text-embedding-v1"):
        # 直接从环境变量获取 API Key
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable is not set")

        # 使用 DashScope 嵌入模型
        self.embeddings = DashScopeEmbeddings(
            model=embeddings_model,
            dashscope_api_key=dashscope_api_key
        )
        self.vector_store = None

    def create_vector_store(self, documents: List[Document]) -> None:
        """创建向量存储"""
        logger.info(f"Creating vector store with {len(documents)} documents")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        logger.info("Vector store created successfully")

    def save_vector_store(self, path: str) -> None:
        """保存向量存储到磁盘"""
        if self.vector_store:
            self.vector_store.save_local(path)
            logger.info(f"Vector store saved to {path}")

    def load_vector_store(self, path: str) -> None:
        """从磁盘加载向量存储"""
        self.vector_store = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
        logger.info(f"Vector store loaded from {path}")

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """相似度搜索"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        results = self.vector_store.similarity_search(query, k=k)
        logger.info(f"Found {len(results)} relevant documents for query: {query}")
        return results