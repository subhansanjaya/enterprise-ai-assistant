from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config import settings


class MCPClient:
    def __init__(self) -> None:
        self._url = settings.mcp_server_url

    async def search_documents(
        self,
        query: str,
        roles: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        async with streamable_http_client(
            self._url
        ) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(
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