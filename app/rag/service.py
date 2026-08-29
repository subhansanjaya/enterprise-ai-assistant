from pathlib import Path

from app.rag.embeddings import EmbeddingService
from app.rag.hybrid import HybridRanker
from app.rag.knowledge_base import KnowledgeBase
from app.rag.pinecone import PineconeService
from app.rag.retrieval import RetrievalService


def create_retrieval_service() -> RetrievalService:
    knowledge_base = KnowledgeBase(
        Path("data")
    )

    return RetrievalService(
        embedding_service=EmbeddingService(),
        pinecone_service=PineconeService(),
        sparse_retriever=knowledge_base.sparse_retriever,
        hybrid_ranker=HybridRanker(
            dense_weight=0.7,
            sparse_weight=0.3,
        ),
    )