from pathlib import Path

from app.rag.chunker import chunk_document
from app.rag.loader import load_markdown_documents
from app.rag.models import DocumentChunk
from app.rag.sparse import BM25Retriever


class KnowledgeBase:
    def __init__(self, data_dir: Path) -> None:
        documents = load_markdown_documents(data_dir)

        self.chunks: list[DocumentChunk] = [
            chunk
            for document in documents
            for chunk in chunk_document(document)
        ]

        self.sparse_retriever = BM25Retriever(self.chunks)