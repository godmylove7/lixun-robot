import os
from typing import List
from loguru import logger
import time

try:
    from langchain_community.embeddings import DashScopeEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise


class VectorStoreManager:
    def __init__(self, embeddings_model: str = "text-embedding-v1"):
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable is not set")

        # 移除 timeout 参数
        self.embeddings = DashScopeEmbeddings(
            model=embeddings_model,
            dashscope_api_key=dashscope_api_key
        )
        self.vector_store = None

    def create_vector_store(self, documents: List[Document]) -> None:
        """分批创建向量存储，避免超时"""
        logger.info(f"Creating vector store with {len(documents)} documents")

        # 分批处理，每批50个文档（更小的批次）
        batch_size = 50
        total_batches = (len(documents) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(documents))
            batch = documents[start_idx:end_idx]

            print(f"🔧 向量化进度: {batch_num + 1}/{total_batches} ({len(batch)} 个文档)")

            try:
                if not self.vector_store:
                    # 第一批创建新的向量存储
                    self.vector_store = FAISS.from_documents(batch, self.embeddings)
                    print(f"   ✅ 第一批向量化完成")
                else:
                    # 后续批次添加到现有存储
                    self.vector_store.add_documents(batch)
                    print(f"   ✅ 第{batch_num + 1}批向量化完成")

                # 批次间延迟，避免API限制
                if batch_num < total_batches - 1:  # 不是最后一批
                    time.sleep(3)  # 3秒延迟，给API更多休息时间

            except Exception as e:
                print(f"   ❌ 第{batch_num + 1}批处理失败: {e}")
                # 继续处理下一批，不中断
                continue

        print("✅ 向量存储创建完成")
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