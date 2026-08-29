import asyncio
from pathlib import Path

from app.rag.chunker import chunk_document
from app.rag.embeddings import EmbeddingService
from app.rag.indexer import DocumentIndexer
from app.rag.loader import load_markdown_documents
from app.rag.pinecone import PineconeService


async def main() -> None:
    data_dir = Path("data")

    documents = load_markdown_documents(data_dir)

    chunks = [
        chunk
        for document in documents
        for chunk in chunk_document(document)
    ]

    print(f"Loaded {len(documents)} documents.")
    print(f"Created {len(chunks)} chunks.")

    indexer = DocumentIndexer(
        embedding_service=EmbeddingService(),
        pinecone_service=PineconeService(),
    )

    await indexer.index_chunks(chunks)

    print("Documents indexed successfully.")


if __name__ == "__main__":
    asyncio.run(main())