from pinecone import Pinecone

from app.config import settings
from app.rag.models import DocumentChunk


class PineconeService:
    def __init__(self) -> None:
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is not configured.")

        self._client = Pinecone(
            api_key=settings.pinecone_api_key,
        )

        self._index = self._client.Index(
            settings.pinecone_index_name,
        )

    def upsert_chunks(
        self,
        vectors: list[tuple[str, list[float], dict]],
    ) -> None:
        self._index.upsert(
            vectors=vectors,
            namespace=settings.pinecone_namespace,
        )

    def search(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict | None = None,
    ) -> list[dict]:
        response = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=settings.pinecone_namespace,
            filter=filter,
        )

        return response.matches
    
    def describe_index_stats(self) -> dict:
        return self._index.describe_index_stats()