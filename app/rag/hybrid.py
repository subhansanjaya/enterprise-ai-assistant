from app.rag.results import RetrievalResult


class HybridRanker:
    def __init__(
        self,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ) -> None:
        if not 0 <= dense_weight <= 1:
            raise ValueError("dense_weight must be between 0 and 1.")

        if not 0 <= sparse_weight <= 1:
            raise ValueError("sparse_weight must be between 0 and 1.")

        if dense_weight + sparse_weight == 0:
            raise ValueError("At least one retrieval weight must be positive.")

        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight

    def rank(
        self,
        dense_results: list[tuple],
        sparse_results: list[tuple],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        dense_scores = {
            result[0].chunk_id: result[1]
            for result in dense_results
        }

        sparse_scores = {
            result[0].chunk_id: result[1]
            for result in sparse_results
        }

        all_chunks = {
            result[0].chunk_id: result[0]
            for result in dense_results + sparse_results
        }

        normalized_dense = self._normalize(dense_scores)
        normalized_sparse = self._normalize(sparse_scores)

        results: list[RetrievalResult] = []

        for document_id, chunk in all_chunks.items():
            dense_score = normalized_dense.get(document_id, 0.0)
            sparse_score = normalized_sparse.get(document_id, 0.0)

            hybrid_score = (
                self._dense_weight * dense_score
                + self._sparse_weight * sparse_score
            )

            results.append(
                RetrievalResult(
                    chunk=chunk,
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    hybrid_score=hybrid_score,
                )
            )

        results.sort(
            key=lambda result: result.hybrid_score,
            reverse=True,
        )

        return results[:top_k]

    @staticmethod
    def _normalize(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}

        minimum = min(scores.values())
        maximum = max(scores.values())

        if minimum == maximum:
            return {
                key: 1.0
                for key in scores
            }

        return {
            key: (value - minimum) / (maximum - minimum)
            for key, value in scores.items()
        }