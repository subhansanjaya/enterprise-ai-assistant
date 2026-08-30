from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.embeddings import EmbeddingService
from app.rag.hybrid import HybridRanker
from app.rag.knowledge_base import KnowledgeBase
from app.rag.models import DocumentChunk
from app.rag.pinecone import PineconeService
from app.rag.retrieval import RetrievalService
from app.rag.sparse import BM25Retriever


def test_knowledge_base_loads_chunks() -> None:
    knowledge_base = KnowledgeBase(Path("data"))

    assert len(knowledge_base.chunks) == 12
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
    
@pytest.mark.asyncio
async def test_viewer_cannot_retrieve_restricted_document() -> None:
    internal_chunk = DocumentChunk(
        chunk_id="internal-1",
        document_id="DOC-INTERNAL",
        document_type="incident",
        department="payments",
        access_level="internal",
        created_date="2025-01-01",
        content="Payment database incident",
    )

    restricted_chunk = DocumentChunk(
        chunk_id="restricted-1",
        document_id="DOC-RESTRICTED",
        document_type="incident",
        department="payments",
        access_level="restricted",
        created_date="2025-01-01",
        content="Payment database restricted incident",
    )

    sparse_retriever = BM25Retriever(
        [internal_chunk, restricted_chunk]
    )

    embedding_service = MagicMock(spec=EmbeddingService)
    embedding_service.embed_query = AsyncMock(
        return_value=[0.1, 0.2, 0.3]
    )

    pinecone_service = MagicMock(spec=PineconeService)
    pinecone_service.search.return_value = []

    hybrid_ranker = HybridRanker(
        dense_weight=0.7,
        sparse_weight=0.3,
    )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        pinecone_service=pinecone_service,
        sparse_retriever=sparse_retriever,
        hybrid_ranker=hybrid_ranker,
    )

    results = await retrieval_service.search(
        query="payment database incident",
        top_k=5,
        roles=["viewer"],
    )

    assert results
    assert all(
        result.chunk.access_level == "internal"
        for result in results
    )
    
@pytest.mark.asyncio
async def test_analyst_can_retrieve_restricted_document() -> None:
    internal_chunk = DocumentChunk(
        chunk_id="internal-1",
        document_id="DOC-INTERNAL",
        document_type="incident",
        department="payments",
        access_level="internal",
        created_date="2025-01-01",
        content="Payment database incident",
    )

    restricted_chunk = DocumentChunk(
        chunk_id="restricted-1",
        document_id="DOC-RESTRICTED",
        document_type="incident",
        department="payments",
        access_level="restricted",
        created_date="2025-01-01",
        content="Payment database restricted incident",
    )

    sparse_retriever = BM25Retriever(
        [internal_chunk, restricted_chunk]
    )

    embedding_service = MagicMock(spec=EmbeddingService)
    embedding_service.embed_query = AsyncMock(
        return_value=[0.1, 0.2, 0.3]
    )

    pinecone_service = MagicMock(spec=PineconeService)
    pinecone_service.search.return_value = []

    hybrid_ranker = HybridRanker(
        dense_weight=0.7,
        sparse_weight=0.3,
    )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        pinecone_service=pinecone_service,
        sparse_retriever=sparse_retriever,
        hybrid_ranker=hybrid_ranker,
    )

    results = await retrieval_service.search(
        query="payment database incident",
        top_k=5,
        roles=["analyst"],
    )

    document_ids = {
        result.chunk.document_id
        for result in results
    }

    assert "DOC-INTERNAL" in document_ids
    assert "DOC-RESTRICTED" in document_ids
    
    @pytest.mark.asyncio
    async def test_viewer_access_filter_is_applied_to_pinecone() -> None:
        sparse_retriever = BM25Retriever(
            [
                DocumentChunk(
                    chunk_id="internal-1",
                    document_id="DOC-INTERNAL",
                    document_type="incident",
                    department="payments",
                    access_level="internal",
                    created_date="2025-01-01",
                    content="Payment database incident",
                )
            ]
        )

        embedding_service = MagicMock(spec=EmbeddingService)
        embedding_service.embed_query = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )

        pinecone_service = MagicMock(spec=PineconeService)
        pinecone_service.search.return_value = []

        retrieval_service = RetrievalService(
            embedding_service=embedding_service,
            pinecone_service=pinecone_service,
            sparse_retriever=sparse_retriever,
            hybrid_ranker=HybridRanker(
                dense_weight=0.7,
                sparse_weight=0.3,
            ),
        )

        await retrieval_service.search(
            query="payment database incident",
            top_k=5,
            roles=["viewer"],
        )

        pinecone_service.search.assert_called_once()

        call_kwargs = pinecone_service.search.call_args.kwargs

        assert call_kwargs["filter"] == {
            "access_level": {
                "$in": ["internal"],
            }
        }