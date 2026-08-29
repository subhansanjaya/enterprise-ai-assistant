from pathlib import Path

from app.rag.chunker import chunk_document
from app.rag.loader import load_markdown_documents


DATA_DIR = Path("data")


def test_load_markdown_documents() -> None:
    documents = load_markdown_documents(DATA_DIR)

    assert len(documents) == 5

    document_ids = {
        document.document_id
        for document in documents
    }

    assert "INC-2025-001" in document_ids
    assert "INC-2025-017" in document_ids
    assert "ARCH-2025-003" in document_ids
    assert "RUN-2025-004" in document_ids
    assert "PROD-2025-002" in document_ids


def test_document_chunking() -> None:
    documents = load_markdown_documents(DATA_DIR)

    incident = next(
        document
        for document in documents
        if document.document_id == "INC-2025-001"
    )

    chunks = chunk_document(
        incident,
        chunk_size=200,
        overlap=50,
    )

    assert len(chunks) > 1
    assert all(
        chunk.document_id == "INC-2025-001"
        for chunk in chunks
    )