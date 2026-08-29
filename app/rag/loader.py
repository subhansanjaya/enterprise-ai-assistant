from pathlib import Path

from app.rag.models import Document


def load_markdown_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []

    for path in sorted(data_dir.rglob("*.md")):
        content = path.read_text(encoding="utf-8")

        metadata = _extract_metadata(content)

        title = _extract_title(content)

        documents.append(
            Document(
                document_id=metadata["document_id"],
                document_type=metadata["document_type"],
                department=metadata["department"],
                access_level=metadata["access_level"],
                created_date=metadata["created_date"],
                title=title,
                content=content,
            )
        )

    return documents


def _extract_title(content: str) -> str:
    first_line = content.splitlines()[0]

    if first_line.startswith("# "):
        return first_line[2:].strip()

    return "Untitled Document"


def _extract_metadata(content: str) -> dict[str, str]:
    metadata: dict[str, str] = {}

    for line in content.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", maxsplit=1)

        normalized_key = key.strip().lower().replace(" ", "_")

        if normalized_key in {
            "document_id",
            "document_type",
            "department",
            "access_level",
            "created_date",
        }:
            metadata[normalized_key] = value.strip()

    required_fields = {
        "document_id",
        "document_type",
        "department",
        "access_level",
        "created_date",
    }

    missing_fields = required_fields - metadata.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required metadata: {sorted(missing_fields)}"
        )

    return metadata