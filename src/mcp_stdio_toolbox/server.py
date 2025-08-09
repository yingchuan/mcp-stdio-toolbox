"""Main MCP server for stdio toolbox."""

import asyncio
import logging
from typing import Any

import click
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from .config_loader import load_config
from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# Global registry
registry = ToolRegistry()


@click.command()
@click.option(
    "--config", "-c", default="config/tools.yaml", help="Path to configuration file"
)
def main(config: str):
    """Start MCP stdio toolbox server."""
    asyncio.run(serve(config))


async def serve(config_path: str):
    """Serve the MCP server."""
    # Load configuration
    try:
        config = load_config(config_path)
        logger.info(f"Loaded configuration with {len(config.tools)} tools")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Register tools
    for tool_config in config.tools:
        registry.register_tool(tool_config)
        logger.info(f"Registered tool: {tool_config.name}")

    # Create server
    server = Server(config.server.name)

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List available tools."""
        tools = []
        for definition in registry.get_tool_definitions():
            tools.append(
                Tool(
                    name=definition["name"],
                    description=definition["description"],
                    inputSchema=definition["inputSchema"],
                )
            )
        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        """Call a tool with arguments."""
        if arguments is None:
            arguments = {}

        try:
            handler = registry.get_handler(name)
            result = await handler(arguments)

            # Convert to TextContent
            text_content = []
            for item in result:
                if item["type"] == "text":
                    text_content.append(TextContent(type="text", text=item["text"]))

            return text_content

        except Exception as e:
            logger.error(f"Tool execution failed for {name}: {e}")
            return [TextContent(type="text", text=f"Error: {e}")]

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=config.server.name,
                server_version=config.server.version,
                capabilities={},
            ),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
