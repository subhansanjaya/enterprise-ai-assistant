from app.rag.models import Document, DocumentChunk


def chunk_document(
    document: Document,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[DocumentChunk]:
    text = document.content

    if not text:
        return []

    chunks: list[DocumentChunk] = []

    start = 0
    chunk_number = 0

    while start < len(text):
        end = start + chunk_size

        chunk_text = text[start:end]

        chunks.append(
            DocumentChunk(
                chunk_id=f"{document.document_id}-chunk-{chunk_number:03d}",
                document_id=document.document_id,
                document_type=document.document_type,
                department=document.department,
                access_level=document.access_level,
                created_date=document.created_date,
                content=chunk_text,
            )
        )

        chunk_number += 1

        if end >= len(text):
            break

        start = end - overlap

    return chunks