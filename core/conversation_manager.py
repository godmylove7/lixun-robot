from typing import List, Dict, Any
from datetime import datetime
from loguru import logger


class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.conversations: Dict[str, List[Dict]] = {}
        self.max_history = max_history

    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None):
        """添加消息到对话历史"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[conversation_id].append(message)

        # 保持历史记录不超过最大值
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]

        logger.info(f"Added {role} message to conversation {conversation_id}")

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.conversations.get(conversation_id, [])

    def clear_conversation(self, conversation_id: str):
        """清空对话历史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")