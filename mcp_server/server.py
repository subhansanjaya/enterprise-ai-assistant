import asyncio
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from app.auth.policy import (
    ROLE_ACCESS_LEVELS,
    build_access_filter,
)
from app.rag.knowledge_base import KnowledgeBase


MAX_TOP_K = 10
VALID_ROLES = set(ROLE_ACCESS_LEVELS)


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


async def main() -> None:
    await mcp.run_streamable_http_async(
        host="127.0.0.1",
        port=8001,
    )


if __name__ == "__main__":
    asyncio.run(main())
