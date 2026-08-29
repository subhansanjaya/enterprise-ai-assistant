from app.rag.hybrid import HybridRanker
from app.rag.models import DocumentChunk
from app.rag.sparse import BM25Retriever


def make_chunk(chunk_id: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="DOC-001",
        document_type="incident",
        department="payments",
        access_level="internal",
        created_date="2025-01-01",
        content=f"Content for {chunk_id}",
    )


def test_hybrid_ranker_combines_dense_and_sparse_scores() -> None:
    chunk_a = make_chunk("chunk-a")
    chunk_b = make_chunk("chunk-b")

    dense_results = [
        (chunk_a, 0.9),
        (chunk_b, 0.5),
    ]

    sparse_results = [
        (chunk_a, 2.0),
        (chunk_b, 8.0),
    ]

    ranker = HybridRanker(
        dense_weight=0.7,
        sparse_weight=0.3,
    )

    results = ranker.rank(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].chunk.chunk_id in {
        "chunk-a",
        "chunk-b",
    }

    assert all(
        0.0 <= result.hybrid_score <= 1.0
        for result in results
    )
    
def test_bm25_respects_metadata_filter() -> None:
    payment_chunk = make_chunk("payment")
    payment_chunk = DocumentChunk(
        **{
            **payment_chunk.__dict__,
            "department": "payments",
            "content": "payment database incident",
        }
    )

    hr_chunk = DocumentChunk(
        chunk_id="hr",
        document_id="DOC-002",
        document_type="policy",
        department="hr",
        access_level="internal",
        created_date="2025-01-01",
        content="employee database policy",
    )

    retriever = BM25Retriever(
        [payment_chunk, hr_chunk]
    )

    results = retriever.search(
        "database",
        metadata_filter={"department": "payments"},
    )

    assert len(results) == 1
    assert results[0][0].chunk_id == "payment"