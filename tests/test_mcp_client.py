from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.client import MCPClient


def create_tool_result(documents: list[dict]) -> MagicMock:
    result = MagicMock()
    result.is_error = False
    result.structured_content = {
        "result": documents,
    }
    return result


@pytest.mark.asyncio
async def test_mcp_client_search_documents() -> None:
    documents = [
        {
            "chunk_id": "chunk-1",
            "document_id": "INC-2025-001",
            "document_type": "incident",
            "department": "payments",
            "access_level": "internal",
            "created_date": "2025-02-14",
            "content": "Payment gateway incident.",
            "score": 0.95,
        }
    ]

    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(
        return_value=create_tool_result(documents)
    )

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(
        return_value=mock_session
    )
    mock_session_context.__aexit__ = AsyncMock(
        return_value=None
    )

    mock_http_context = MagicMock()
    mock_http_context.__aenter__ = AsyncMock(
        return_value=("read", "write")
    )
    mock_http_context.__aexit__ = AsyncMock(
        return_value=None
    )

    client = MCPClient()

    with patch(
        "app.mcp.client.streamable_http_client",
        return_value=mock_http_context,
    ), patch(
        "app.mcp.client.ClientSession",
        return_value=mock_session_context,
    ):
        results = await client.search_documents(
            query="payment database incident",
            roles=["viewer"],
            top_k=3,
        )

    assert results == documents

    mock_session.initialize.assert_awaited_once()

    mock_session.call_tool.assert_awaited_once_with(
        "search_documents",
        {
            "query": "payment database incident",
            "roles": ["viewer"],
            "top_k": 3,
        },
    )


@pytest.mark.asyncio
async def test_mcp_client_respects_admin_role() -> None:
    documents = [
        {
            "chunk_id": "chunk-1",
            "document_id": "INC-2025-001",
            "document_type": "incident",
            "department": "payments",
            "access_level": "internal",
            "created_date": "2025-02-14",
            "content": "Payment gateway incident.",
            "score": 0.95,
        },
        {
            "chunk_id": "chunk-2",
            "document_id": "INC-2025-017",
            "document_type": "incident",
            "department": "payments",
            "access_level": "confidential",
            "created_date": "2025-05-22",
            "content": "Payment API database incident.",
            "score": 0.90,
        },
    ]

    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(
        return_value=create_tool_result(documents)
    )

    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(
        return_value=mock_session
    )
    mock_session_context.__aexit__ = AsyncMock(
        return_value=None
    )

    mock_http_context = MagicMock()
    mock_http_context.__aenter__ = AsyncMock(
        return_value=("read", "write")
    )
    mock_http_context.__aexit__ = AsyncMock(
        return_value=None
    )

    client = MCPClient()

    with patch(
        "app.mcp.client.streamable_http_client",
        return_value=mock_http_context,
    ), patch(
        "app.mcp.client.ClientSession",
        return_value=mock_session_context,
    ):
        results = await client.search_documents(
            query="payment database incident",
            roles=["admin"],
            top_k=5,
        )

    assert results == documents

    mock_session.call_tool.assert_awaited_once_with(
        "search_documents",
        {
            "query": "payment database incident",
            "roles": ["admin"],
            "top_k": 5,
        },
    )

    assert all(
        result["access_level"]
        in {"internal", "restricted", "confidential"}
        for result in results
    )