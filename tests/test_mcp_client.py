import pytest

from app.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_mcp_client_search_documents() -> None:
    client = MCPClient()

    results = await client.search_documents(
        query="payment database incident",
        roles=["viewer"],
        top_k=3,
    )

    assert results
    assert len(results) <= 3

    assert all(
        result["access_level"] == "internal"
        for result in results
    )


@pytest.mark.asyncio
async def test_mcp_client_respects_admin_role() -> None:
    client = MCPClient()

    results = await client.search_documents(
        query="payment database incident",
        roles=["admin"],
        top_k=5,
    )

    assert results

    assert all(
        result["access_level"]
        in {"internal", "restricted", "confidential"}
        for result in results
    )
