import asyncio
from collections import Counter
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from app.auth.policy import (
    ROLE_ACCESS_LEVELS,
    build_access_filter,
)
from app.rag.knowledge_base import KnowledgeBase

MAX_TOP_K = 10
VALID_ROLES = set(ROLE_ACCESS_LEVELS)
ALLOWED_ANALYSIS_OPERATIONS = {
    "count",
    "group_by",
    "percentage",
    "latest",
    "earliest",
}


mcp = MCPServer(
    name="enterprise-ai-assistant",
    description="Enterprise AI Assistant MCP server",
)

knowledge_base = KnowledgeBase(
    Path("data")
)


@mcp.tool(
    name="search_documents",
    description="Search enterprise documents accessible to the user's roles.",
)
def search_documents(
    query: str,
    roles: list[str],
    top_k: int = 5,
) -> list[dict]:
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if not roles:
        raise ValueError("At least one role is required.")

    unknown_roles = set(roles) - VALID_ROLES

    if unknown_roles:
        raise ValueError(
            "Unknown role(s): "
            + ", ".join(sorted(unknown_roles))
        )

    if not 1 <= top_k <= MAX_TOP_K:
        raise ValueError(
            f"top_k must be between 1 and {MAX_TOP_K}."
        )

    metadata_filter = build_access_filter(roles)

    results = knowledge_base.sparse_retriever.search(
        query=query,
        top_k=top_k,
        metadata_filter=metadata_filter,
    )

    return [
        {
            "chunk_id": result[0].chunk_id,
            "document_id": result[0].document_id,
            "document_type": result[0].document_type,
            "department": result[0].department,
            "access_level": result[0].access_level,
            "created_date": result[0].created_date,
            "content": result[0].content,
            "score": result[1],
        }
        for result in results
    ]


@mcp.tool(
    name="analyze_documents",
    description=(
        "Perform safe structured analysis on documents already retrieved "
        "from the enterprise knowledge base."
    ),
)
def analyze_documents(
    documents: list[dict],
    operation: str,
    field: str = "document_id",
) -> dict:
    operation = operation.strip().lower()
    field = field.strip()

    if operation not in ALLOWED_ANALYSIS_OPERATIONS:
        raise ValueError(
            "Unsupported analysis operation. "
            f"Allowed operations: {', '.join(sorted(ALLOWED_ANALYSIS_OPERATIONS))}."
        )

    if not documents:
        return {
            "operation": operation,
            "result": 0,
        }

    values = [
        document.get(field)
        for document in documents
        if document.get(field) is not None
    ]

    if operation == "count":
        return {
            "operation": "count",
            "field": field,
            "result": len(documents),
        }

    if not values:
        raise ValueError(
            f"No documents contain the requested field: {field}."
        )

    if operation == "group_by":
        counts = Counter(str(value) for value in values)

        return {
            "operation": "group_by",
            "field": field,
            "result": dict(counts),
        }

    if operation == "percentage":
        counts = Counter(str(value) for value in values)
        total = len(values)

        percentages = {
            key: round(
                (count / total) * 100,
                2,
            )
            for key, count in counts.items()
        }

        return {
            "operation": "percentage",
            "field": field,
            "total": total,
            "result": percentages,
        }

    dates = [
        document.get("created_date")
        for document in documents
        if document.get("created_date")
    ]

    if not dates:
        raise ValueError(
            "No created_date values are available for date analysis."
        )

    selected_date = (
        max(dates)
        if operation == "latest"
        else min(dates)
    )

    matching_documents = [
        document
        for document in documents
        if document.get("created_date") == selected_date
    ]

    return {
        "operation": operation,
        "field": "created_date",
        "date": selected_date,
        "documents": [
            document.get("document_id")
            for document in matching_documents
        ],
    }


async def main() -> None:
    await mcp.run_streamable_http_async(
        host="127.0.0.1",
        port=8001,
    )


if __name__ == "__main__":
    asyncio.run(main())