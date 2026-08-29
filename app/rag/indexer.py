from app.rag.embeddings import EmbeddingService
from app.rag.models import DocumentChunk
from app.rag.pinecone import PineconeService


class DocumentIndexer:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        pinecone_service: PineconeService,
    ) -> None:
        self._embedding_service = embedding_service
        self._pinecone_service = pinecone_service

    async def index_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> None:
        if not chunks:
            return

        texts = [chunk.content for chunk in chunks]

        embeddings = await self._embedding_service.embed_documents(
            texts
        )

        vectors = [
            (
                chunk.chunk_id,
                embedding,
                {
                    "document_id": chunk.document_id,
                    "document_type": chunk.document_type,
                    "department": chunk.department,
                    "access_level": chunk.access_level,
                    "created_date": chunk.created_date,
                    "text": chunk.content,
                },
            )
            for chunk, embedding in zip(
                chunks,
                embeddings,
                strict=True,
            )
        ]

        self._pinecone_service.upsert_chunks(vectors)