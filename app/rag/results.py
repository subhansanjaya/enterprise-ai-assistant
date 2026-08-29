from dataclasses import dataclass

from app.rag.models import DocumentChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    dense_score: float
    sparse_score: float
    hybrid_score: float