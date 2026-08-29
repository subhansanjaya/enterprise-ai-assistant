from app.auth.policy import build_access_filter
from app.rag.embeddings import EmbeddingService
from app.rag.hybrid import HybridRanker
from app.rag.models import DocumentChunk
from app.rag.pinecone import PineconeService
from app.rag.results import RetrievalResult
from app.rag.sparse import BM25Retriever


def _merge_metadata_filters(
    metadata_filter: dict | None,
    access_filter: dict,
) -> dict:
    if metadata_filter is None:
        return access_filter

    return {
        "$and": [
            metadata_filter,
            access_filter,
        ]
    }


class RetrievalService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        pinecone_service: PineconeService,
        sparse_retriever: BM25Retriever,
        hybrid_ranker: HybridRanker,
    ) -> None:
        self._embedding_service = embedding_service
        self._pinecone_service = pinecone_service
        self._sparse_retriever = sparse_retriever
        self._hybrid_ranker = hybrid_ranker

    async def search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict | None = None,
        roles: list[str] | None = None,
    ) -> list[RetrievalResult]:
        query_vector = await self._embedding_service.embed_query(
            query
        )

        access_filter = build_access_filter(
            roles or []
        )

        effective_filter = _merge_metadata_filters(
            metadata_filter,
            access_filter,
        )

        dense_matches = self._pinecone_service.search(
            vector=query_vector,
            top_k=top_k,
            filter=effective_filter,
        )

        dense_results = [
            (
                DocumentChunk(
                    chunk_id=match.id,
                    document_id=match.metadata["document_id"],
                    document_type=match.metadata["document_type"],
                    department=match.metadata["department"],
                    access_level=match.metadata["access_level"],
                    created_date=match.metadata["created_date"],
                    content=match.metadata["text"],
                ),
                float(match.score),
            )
            for match in dense_matches
        ]

        sparse_results = self._sparse_retriever.search(
            query=query,
            top_k=top_k,
            metadata_filter=effective_filter,
        )

        return self._hybrid_ranker.rank(
            dense_results=dense_results,
            sparse_results=sparse_results,
            top_k=top_k,
        )