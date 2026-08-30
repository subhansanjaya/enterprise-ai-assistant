import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config import settings


class MCPClient:
    def __init__(self) -> None:
        self._url = settings.mcp_server_url
        self._timeout_seconds = settings.mcp_timeout_seconds

    async def search_documents(
        self,
        query: str,
        roles: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with streamable_http_client(
                    self._url
                ) as (
                    read_stream,
                    write_stream,
                ), ClientSession(
                    read_stream,
                    write_stream,
                ) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        "search_documents",
                        {
                            "query": query,
                            "roles": roles,
                            "top_k": top_k,
                        },
                    )

                    if result.is_error:
                        raise RuntimeError(
                            "MCP search_documents tool returned an error."
                        )

                    return result.structured_content.get(
                        "result",
                        [],
                    )

        except TimeoutError as exc:
            raise RuntimeError(
                "The MCP search service timed out."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "The MCP search service is currently unavailable."
            ) from exc

    async def analyze_documents(
        self,
        documents: list[dict],
        operation: str,
        field: str = "document_id",
    ) -> dict:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with streamable_http_client(
                    self._url
                ) as (
                    read_stream,
                    write_stream,
                ), ClientSession(
                    read_stream,
                    write_stream,
                ) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        "analyze_documents",
                        {
                            "documents": documents,
                            "operation": operation,
                            "field": field,
                        },
                    )

                    if result.is_error:
                        raise RuntimeError(
                            "MCP analyze_documents tool returned an error."
                        )

                    return result.structured_content.get(
                        "result",
                        {},
                    )

        except TimeoutError as exc:
            raise RuntimeError(
                "The MCP analysis service timed out."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "The MCP analysis service is currently unavailable."
            ) from exc