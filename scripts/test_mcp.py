import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    async with streamable_http_client(
        "http://127.0.0.1:8001/mcp"
    ) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("Available tools:")

            for tool in tools.tools:
                print(f"- {tool.name}")

            result = await session.call_tool(
                "search_documents",
                {
                    "query": "payment database incident",
                    "roles": ["viewer"],
                    "top_k": 3,
                },
            )

            print("\nSearch result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
