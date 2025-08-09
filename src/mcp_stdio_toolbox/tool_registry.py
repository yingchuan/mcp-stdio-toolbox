"""Dynamic tool registry for MCP server."""

from collections.abc import Callable
from typing import Any

from jsonschema import ValidationError, validate

from .config_loader import ToolConfig
from .subprocess_runner import build_command_args, run_command


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, ToolConfig] = {}
        self.handlers: dict[str, Callable] = {}

    def register_tool(self, tool_config: ToolConfig):
        """Register a tool from configuration."""
        self.tools[tool_config.name] = tool_config
        self.handlers[tool_config.name] = self._create_handler(tool_config)

    def _create_handler(self, tool_config: ToolConfig):
        """Create an async handler for a tool."""

        async def handler(arguments: dict[str, Any]) -> list[dict[str, Any]]:
            # Validate input against schema
            try:
                validate(instance=arguments, schema=tool_config.input_schema)
            except ValidationError as e:
                raise ValueError(f"Invalid arguments: {e.message}") from e

            # Build command arguments
            arg_mapping = tool_config.input_schema.get("arg_mapping", [])
            final_args = build_command_args(tool_config.args, arguments, arg_mapping)

            # Execute command
            try:
                result = await run_command(
                    tool_config.command, final_args, tool_config.timeout_sec
                )

                if result.exit_code != 0:
                    error_msg = f"Command failed (exit code {result.exit_code})"
                    if result.stderr:
                        error_msg += f": {result.stderr}"
                    raise RuntimeError(error_msg)

                content = [{"type": "text", "text": result.stdout}]
                if result.truncated:
                    content.append(
                        {
                            "type": "text",
                            "text": "[Output was truncated due to size limit]",
                        }
                    )

                return content

            except Exception as e:
                raise RuntimeError(f"Tool execution failed: {e}") from e

        return handler

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get MCP tool definitions for all registered tools."""
        definitions = []
        for name, config in self.tools.items():
            definitions.append(
                {
                    "name": name,
                    "description": config.description,
                    "inputSchema": config.input_schema,
                }
            )
        return definitions

    def get_handler(self, tool_name: str) -> Callable:
        """Get handler for a specific tool."""
        if tool_name not in self.handlers:
            raise ValueError(f"Tool not found: {tool_name}")
        return self.handlers[tool_name]
