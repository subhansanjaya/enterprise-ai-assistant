import asyncio
from pathlib import Path

from app.rag.embeddings import EmbeddingService
from app.rag.hybrid import HybridRanker
from app.rag.knowledge_base import KnowledgeBase
from app.rag.pinecone import PineconeService
from app.rag.retrieval import RetrievalService


async def main() -> None:
    knowledge_base = KnowledgeBase(Path("data"))

    service = RetrievalService(
        embedding_service=EmbeddingService(),
        pinecone_service=PineconeService(),
        sparse_retriever=knowledge_base.sparse_retriever,
        hybrid_ranker=HybridRanker(
            dense_weight=0.7,
            sparse_weight=0.3,
        ),
    )

    results = await service.search(
        "What caused the payment gateway failures?",
        top_k=5,
        metadata_filter={
            "department": "payments",
        },
    )

    for result in results:
        print("=" * 80)
        print(f"Chunk: {result.chunk.chunk_id}")
        print(f"Document: {result.chunk.document_id}")
        print(f"Dense: {result.dense_score:.4f}")
        print(f"Sparse: {result.sparse_score:.4f}")
        print(f"Hybrid: {result.hybrid_score:.4f}")
        print()
        print(result.chunk.content)


if __name__ == "__main__":
    asyncio.run(main())