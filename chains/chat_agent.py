from typing import Dict, Any, List
from loguru import logger
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from core.llm_config import LLMConfig


class ChatState(BaseModel):
    question: str
    conversation_history: List[Dict[str, Any]]
    retrieved_docs: List[Document] = []
    answer: str = ""
    citations: List[Dict[str, Any]] = []


class ChatAgent:
    def __init__(self, vector_store_manager, conversation_manager):
        self.llm_config = LLMConfig()
        self.llm = self.llm_config.get_chat_model()
        self.vector_store = vector_store_manager
        self.conversation_manager = conversation_manager

        # 构建工作流
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(ChatState)

        # 添加节点
        workflow.add_node("retrieve", self.retrieve_documents)
        workflow.add_node("generate_answer", self.generate_answer)

        # 设置边
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    def retrieve_documents(self, state: ChatState) -> Dict[str, Any]:
        """检索相关文档"""
        logger.info(f"Retrieving documents for question: {state.question}")

        # 构建增强的查询（包含对话历史）
        enhanced_query = self._enhance_query(state.question, state.conversation_history)

        # 检索相关文档
        retrieved_docs = self.vector_store.similarity_search(enhanced_query, k=4)

        return {"retrieved_docs": retrieved_docs}

    def _enhance_query(self, question: str, history: List[Dict]) -> str:
        """基于对话历史增强查询"""
        if not history:
            return question

        # 获取最近的几个用户问题作为上下文
        recent_questions = [
            msg["content"] for msg in history[-3:]
            if msg["role"] == "user"
        ]

        if recent_questions:
            context = " ".join(recent_questions[-2:])
            return f"{context} {question}"

        return question

    def generate_answer(self, state: ChatState) -> Dict[str, Any]:
        """生成回答"""
        logger.info("Generating answer with retrieved documents")

        # 准备上下文
        context_parts = []
        for i, doc in enumerate(state.retrieved_docs):
            filename = doc.metadata.get('filename', '未知文件')
            content_preview = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            context_parts.append(f"【文档{i + 1} - 来自《{filename}》】\n{content_preview}")

        context = "\n\n".join(context_parts)

        # 构建更人性化的提示词
        prompt = ChatPromptTemplate.from_template("""
# 角色设定
你是Lixun Robot，一个专业且友好的知识库助手。你的风格应该：
- 自然亲切，像在和朋友聊天
- 专业但不生硬
- 乐于助人且有耐心
- 根据上下文适当发挥，让回答更完整

# 可用信息
以下是相关的知识库内容：
{context}

# 对话背景
之前的对话：
{history}

# 当前问题
用户问：{question}

# 回答要求
1. 基于知识库内容，用自然的中文回答
2. 如果知识库信息充分，请自信地回答并注明来源【文档X】
3. 如果信息不完整，可以结合常识补充，但要说明哪些是知识库内容，哪些是你的补充
4. 回答要流畅，避免机械地复制粘贴
5. 适当使用表情符号让对话更生动（但不要过度）

# 引用记录（这部分不会显示给用户）
请在回答后记录实际引用的内容：

【实际引用内容】
文档X: 具体引用的文本

现在请开始回答：
""")

        # 格式化对话历史
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in state.conversation_history[-5:]
        ])

        # 调用LLM生成回答
        chain = prompt | self.llm | StrOutputParser()
        full_response = chain.invoke({
            "context": context,
            "history": history_text,
            "question": state.question
        })

        print(f"🔍 LLM原始响应: {full_response}")  # 调试用

        # 分离回答和实际引用内容
        answer, actual_citations = self._parse_response(full_response)

        # 如果没有解析到引用，使用回退方法
        if not actual_citations:
            actual_citations = self._fallback_extract_citations(answer, state.retrieved_docs, state.question)

        # 构建引用信息
        citations = self._build_citations_from_actual_usage(actual_citations, state.retrieved_docs)

        return {
            "answer": answer,
            "citations": citations
        }

    def _parse_response(self, full_response: str) -> tuple[str, List[Dict]]:
        """解析LLM的完整响应，分离回答和实际引用内容"""
        # 查找实际引用内容标记
        citation_marker = "【实际引用内容】"
        if citation_marker in full_response:
            parts = full_response.split(citation_marker)
            answer = parts[0].strip()
            citation_text = parts[1].strip()

            # 解析引用内容
            actual_citations = []
            lines = citation_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('文档') and ':' in line:
                    try:
                        doc_part, content = line.split(':', 1)
                        doc_id = int(doc_part.replace('文档', '').strip())
                        actual_citations.append({
                            'doc_id': doc_id,
                            'content': content.strip()
                        })
                    except ValueError:
                        continue  # 跳过解析失败的行

            return answer, actual_citations
        else:
            # 如果没有明确标记，返回整个响应作为回答
            return full_response, []

    def _fallback_extract_citations(self, answer: str, documents: List[Document], question: str) -> List[Dict]:
        """回退方法：从回答中提取引用信息"""
        citations = []

        for i, doc in enumerate(documents):
            if f"【文档{i + 1}】" in answer:
                # 在文档内容中查找与问题最相关的内容
                relevant_content = self._find_relevant_content(doc.page_content, question)

                citations.append({
                    'doc_id': i + 1,
                    'content': relevant_content
                })

        return citations

    def _find_relevant_content(self, content: str, question: str) -> str:
        """在文档内容中找到与问题最相关的内容"""
        import re

        # 提取问题关键词
        question_clean = re.sub(r'[^\w\s]', '', question.lower())
        keywords = [word for word in question_clean.split() if len(word) > 1]

        if not keywords:
            return content[:200] + ('...' if len(content) > 200 else '')

        # 按句子分割
        sentences = [s.strip() for s in content.split('。') if s.strip()]

        # 找到包含关键词的句子
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence)
                if len('。'.join(relevant_sentences)) > 150:
                    break

        if relevant_sentences:
            return '。'.join(relevant_sentences) + '。'
        else:
            # 返回内容开头
            return content[:150] + ('...' if len(content) > 150 else '')

    def _build_citations_from_actual_usage(self, actual_citations: List[Dict], documents: List[Document]) -> List[Dict]:
        """根据LLM实际使用的内容构建引用信息"""
        citations = []

        for citation in actual_citations:
            doc_id = citation['doc_id']
            if 1 <= doc_id <= len(documents):
                doc = documents[doc_id - 1]
                citations.append({
                    "doc_id": doc_id,
                    "content": citation['content'],
                    "metadata": doc.metadata
                })

        return citations

    def chat(self, question: str, conversation_id: str = "default") -> Dict[str, Any]:
        """处理用户问题"""
        # 获取对话历史
        history = self.conversation_manager.get_conversation_history(conversation_id)

        # 初始化状态
        initial_state = ChatState(
            question=question,
            conversation_history=history
        )

        # 执行工作流
        result = self.workflow.invoke(initial_state)

        # 更新对话历史
        self.conversation_manager.add_message(conversation_id, "user", question)
        self.conversation_manager.add_message(
            conversation_id,
            "assistant",
            result["answer"],
            {"citations": result["citations"]}
        )

        return {
            "answer": result["answer"],
            "citations": result["citations"],
            "retrieved_docs": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["retrieved_docs"]
            ]
        }"" 
