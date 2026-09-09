"""MNEMOS MCP Server package."""
import asyncio
from .server import run_mcp_stdio


def run_mcp_cli():
    """CLI entry point for mnemos-mcp command."""
    asyncio.run(run_mcp_stdio())


__all__ = ["run_mcp_stdio", "run_mcp_cli"]
