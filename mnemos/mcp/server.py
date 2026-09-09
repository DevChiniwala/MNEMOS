import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
from pydantic import BaseModel
import json

from mnemos.server.deps import get_memory_agent, get_research_agent, get_memory_store, init_services

# Initialize services
init_services()

# Create MCP server
app = Server("mnemos")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for MNEMOS memory."""
    return [
        Tool(
            name="memorize",
            description="Store a new fact or observation in long-term memory. Automatically handles contradiction and versioning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The fact or text to memorize"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Optional user or namespace ID"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="research",
            description="Perform a deep, iterative research loop across memory to answer a complex question.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to research"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Optional user or namespace ID"
                    }
                },
                "required": ["question"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    if name == "memorize":
        text = arguments.get("text")
        user_id = arguments.get("user_id", "default")
        
        agent = get_memory_agent()
        result = agent.memorize(text, user_id=user_id)
        
        return [TextContent(
            type="text",
            text=f"Memorized successfully. Memory ID: {getattr(result, 'id', 'unknown')}"
        )]
        
    elif name == "research":
        question = arguments.get("question")
        user_id = arguments.get("user_id", "default")
        
        agent = get_research_agent()
        out = agent.research(request=question, user_id=user_id)
        
        return [TextContent(
            type="text",
            text=f"Research Result:\n{out.integrated_memory}\n\nSources used: {len(out.raw_memory)}"
        )]
    
    raise ValueError(f"Unknown tool: {name}")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """Expose memory stats as a resource."""
    return [
        Resource(
            uri="mnemos://system/stats",
            name="Memory System Stats",
            description="Active memories in the store",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read specific memory resource."""
    if uri == "mnemos://system/stats":
        store = get_memory_store()
        active = store.get_entries(include_inactive=False)
        return json.dumps({
            "total_active_memories": len(active),
            "memories": [m.content for m in active[:10]] # Limit preview
        })
    raise ValueError(f"Resource not found: {uri}")

async def run_mcp_stdio():
    """Run the MCP server over stdio."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_mcp_stdio())
