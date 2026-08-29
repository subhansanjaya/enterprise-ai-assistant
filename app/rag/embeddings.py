from langchain_openai import OpenAIEmbeddings

from app.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await self._embeddings.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)