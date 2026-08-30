from pinecone import Pinecone

from app.config import settings


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
        try:
            self._index.upsert(
                vectors=vectors,
                namespace=settings.pinecone_namespace,
            )
        except Exception as exc:
            raise RuntimeError(
                "The vector database is currently unavailable."
            ) from exc

    def search(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict | None = None,
    ) -> list[dict]:
        try:
            response = self._index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                namespace=settings.pinecone_namespace,
                filter=filter,
            )

            return response.matches

        except Exception as exc:
            raise RuntimeError(
                "The vector database search is currently unavailable."
            ) from exc

    def describe_index_stats(self) -> dict:
        try:
            return self._index.describe_index_stats()
        except Exception as exc:
            raise RuntimeError(
                "The vector database is currently unavailable."
            ) from exc