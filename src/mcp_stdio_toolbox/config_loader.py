"""Configuration loader for MCP stdio toolbox."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ToolConfig:
    name: str
    description: str
    command: str
    args: list[str]
    input_schema: dict[str, Any]
    timeout_sec: int = 30


@dataclass
class ServerConfig:
    name: str = "mcp-stdio-toolbox"
    version: str = "0.1.0"
    default_timeout_sec: int = 30
    max_output_bytes: int = 1048576


@dataclass
class Config:
    server: ServerConfig
    tools: list[ToolConfig]


def load_config(config_path: str | Path) -> Config:
    """Load configuration from YAML file."""
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if "tools" not in data:
        raise ValueError("Config must contain 'tools' section")

    server_data = data.get("server", {})
    server = ServerConfig(
        name=server_data.get("name", "mcp-stdio-toolbox"),
        version=server_data.get("version", "0.1.0"),
        default_timeout_sec=server_data.get("default_timeout_sec", 30),
        max_output_bytes=server_data.get("max_output_bytes", 1048576),
    )

    tools = []
    for tool_data in data["tools"]:
        required_fields = ["name", "description", "command", "input_schema"]
        if not all(k in tool_data for k in required_fields):
            raise ValueError(
                f"Tool missing required fields {required_fields}: {tool_data}"
            )

        tools.append(
            ToolConfig(
                name=tool_data["name"],
                description=tool_data["description"],
                command=tool_data["command"],
                args=tool_data.get("args", []),
                input_schema=tool_data["input_schema"],
                timeout_sec=tool_data.get("timeout_sec", server.default_timeout_sec),
            )
        )

    return Config(server=server, tools=tools)
