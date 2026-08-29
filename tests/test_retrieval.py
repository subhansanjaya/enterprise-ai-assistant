from pathlib import Path

import pytest

from app.rag.hybrid import HybridRanker
from app.rag.knowledge_base import KnowledgeBase
from app.rag.sparse import BM25Retriever


def test_knowledge_base_loads_chunks() -> None:
    knowledge_base = KnowledgeBase(Path("data"))

    assert len(knowledge_base.chunks) == 10
    assert isinstance(
        knowledge_base.sparse_retriever,
        BM25Retriever,
    )


def test_bm25_finds_payment_incident() -> None:
    knowledge_base = KnowledgeBase(Path("data"))

    results = knowledge_base.sparse_retriever.search(
        "payment database connection incident",
        top_k=3,
        metadata_filter={
            "department": "payments",
        },
    )

    assert results
    assert any(
        "payment" in result[0].content.lower()
        for result in results
    )