from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
import asyncio

async def main():
    async with streamable_http_client("http://127.0.0.1:8000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool("greet", {"name": "Мир"})
            print("Result:", result.content[0].text)

            resources = await session.list_resources()
            print("Resources:", [r.uri for r in resources.resources])

            prompts = await session.list_prompts()
            print("Prompts:", [p.name for p in prompts.prompts])

asyncio.run(main())