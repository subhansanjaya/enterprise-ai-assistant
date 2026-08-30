import json
from pathlib import Path

import pytest

from app.rag.embeddings import EmbeddingService
from app.rag.hybrid import HybridRanker
from app.rag.knowledge_base import KnowledgeBase
from app.rag.pinecone import PineconeService
from app.rag.retrieval import RetrievalService

DATASET_PATH = Path(__file__).parent / "dataset.json"
DATA_PATH = Path("data")
TOP_K = 5


def load_dataset() -> list[dict]:
    return json.loads(
        DATASET_PATH.read_text(encoding="utf-8")
    )


@pytest.fixture
def retrieval_service() -> RetrievalService:
    knowledge_base = KnowledgeBase(DATA_PATH)

    embedding_service = EmbeddingService()
    pinecone_service = PineconeService()

    return RetrievalService(
        embedding_service=embedding_service,
        pinecone_service=pinecone_service,
        sparse_retriever=knowledge_base.sparse_retriever,
        hybrid_ranker=HybridRanker(
            dense_weight=0.7,
            sparse_weight=0.3,
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "evaluation_case",
    load_dataset(),
    ids=lambda case: case["id"],
)
async def test_retrieval_recall(
    retrieval_service: RetrievalService,
    evaluation_case: dict,
) -> None:
    results = await retrieval_service.search(
        query=evaluation_case["question"],
        top_k=TOP_K,
        roles=["admin"],
    )

    retrieved_document_ids = {
        result.chunk.document_id
        for result in results
    }

    expected_documents = set(
        evaluation_case["expected_documents"]
    )

    matched_documents = (
        expected_documents
        & retrieved_document_ids
    )

    recall = (
        len(matched_documents)
        / len(expected_documents)
    )

    print(
        "\n"
        f"{evaluation_case['id']}: "
        f"Recall@{TOP_K} = {recall:.2%}"
    )

    print(
        f"Expected: {sorted(expected_documents)}"
    )

    print(
        f"Retrieved: {sorted(retrieved_document_ids)}"
    )

    assert recall == 1.0