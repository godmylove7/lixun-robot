import os
from typing import List, Dict, Any
from loguru import logger

try:
    from pypdf import PdfReader
    from docx import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document as LangDocument
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def extract_text(self, file_path: str, file_type: str) -> str:
        """提取文档文本内容"""
        try:
            if file_type == 'pdf':
                return self._extract_pdf(file_path)
            elif file_type == 'docx':
                return self._extract_docx(file_path)
            elif file_type in ['md', 'txt']:
                return self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

    def _extract_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def _extract_docx(self, file_path: str) -> str:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def _extract_text_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def split_documents(self, text: str, metadata: Dict[str, Any] = None) -> List[LangDocument]:
        """将文本分割成块"""
        if metadata is None:
            metadata = {}

        documents = self.text_splitter.create_documents([text], [metadata])
        logger.info(f"Split text into {len(documents)} chunks")
        return documents