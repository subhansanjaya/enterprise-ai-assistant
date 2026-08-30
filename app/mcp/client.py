import asyncio

from langsmith import traceable
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config import settings


class MCPClient:
    def __init__(self) -> None:
        self._url = settings.mcp_server_url
        self._timeout_seconds = settings.mcp_timeout_seconds

    @traceable(
        name="MCP search_documents",
        run_type="tool",
    )
    async def search_documents(
        self,
        query: str,
        roles: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        print(
            "MCP CLIENT SEARCH:",
            {
                "query": query,
                "roles": roles,
                "top_k": top_k,
            },
        )

        try:
            async with asyncio.timeout(
                self._timeout_seconds
            ):
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

                    documents = result.structured_content.get(
                        "result",
                        [],
                    )

                    print(
                        "MCP CLIENT RESULTS:",
                        len(documents),
                    )

                    return documents

        except TimeoutError as exc:
            print("MCP CLIENT TIMEOUT")
            raise RuntimeError(
                "The MCP search service timed out."
            ) from exc

        except Exception as exc:
            print(
                "MCP CLIENT ERROR:",
                type(exc).__name__,
            )
            raise RuntimeError(
                "The MCP search service is currently unavailable."
            ) from exc