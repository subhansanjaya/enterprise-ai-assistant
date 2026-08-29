import re

from rank_bm25 import BM25Okapi

from app.rag.models import DocumentChunk


class BM25Retriever:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self._chunks = chunks

        tokenized_documents = [
            self._tokenize(chunk.content)
            for chunk in chunks
        ]

        self._bm25 = BM25Okapi(tokenized_documents)

    def search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        query_tokens = self._tokenize(query)

        scores = self._bm25.get_scores(query_tokens)

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        results: list[tuple[DocumentChunk, float]] = []

        for index in ranked_indexes:
            chunk = self._chunks[index]

            if metadata_filter and not self._matches_filter(
                chunk,
                metadata_filter,
            ):
                continue

            results.append(
                (chunk, float(scores[index]))
            )

            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
        )

    @staticmethod
    def _matches_filter(
        chunk: DocumentChunk,
        metadata_filter: dict,
    ) -> bool:
        for key, expected_value in metadata_filter.items():
            actual_value = getattr(chunk, key, None)

            if actual_value != expected_value:
                return False

        return True