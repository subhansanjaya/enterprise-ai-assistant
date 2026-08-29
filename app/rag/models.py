from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    document_id: str
    document_type: str
    department: str
    access_level: str
    created_date: str
    title: str
    content: str


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_type: str
    department: str
    access_level: str
    created_date: str
    content: str