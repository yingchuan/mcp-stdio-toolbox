"""Tests for tool registry."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_stdio_toolbox.config_loader import ToolConfig
from mcp_stdio_toolbox.tool_registry import ToolRegistry


@pytest.fixture
def sample_tool_config():
    return ToolConfig(
        name="echo_test",
        description="Test echo tool",
        command="echo",
        args=[],
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "arg_mapping": [["text"]],
        },
    )


def test_register_tool(sample_tool_config):
    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)

    assert "echo_test" in registry.tools
    assert "echo_test" in registry.handlers
    assert registry.tools["echo_test"] == sample_tool_config


def test_get_tool_definitions(sample_tool_config):
    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)

    definitions = registry.get_tool_definitions()

    assert len(definitions) == 1
    definition = definitions[0]
    assert definition["name"] == "echo_test"
    assert definition["description"] == "Test echo tool"
    assert definition["inputSchema"] == sample_tool_config.input_schema


def test_get_handler(sample_tool_config):
    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)

    handler = registry.get_handler("echo_test")
    assert callable(handler)


def test_get_handler_not_found():
    registry = ToolRegistry()

    with pytest.raises(ValueError, match="Tool not found: nonexistent"):
        registry.get_handler("nonexistent")


@pytest.mark.asyncio
@patch("mcp_stdio_toolbox.tool_registry.run_command")
async def test_tool_handler_success(mock_run_command, sample_tool_config):
    mock_result = AsyncMock()
    mock_result.exit_code = 0
    mock_result.stdout = "hello world"
    mock_result.truncated = False
    mock_run_command.return_value = mock_result

    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)
    handler = registry.get_handler("echo_test")

    result = await handler({"text": "hello world"})

    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["text"] == "hello world"

    mock_run_command.assert_called_once_with(
        "echo", ["hello world"], sample_tool_config.timeout_sec
    )


@pytest.mark.asyncio
@patch("mcp_stdio_toolbox.tool_registry.run_command")
async def test_tool_handler_with_truncation(mock_run_command, sample_tool_config):
    mock_result = AsyncMock()
    mock_result.exit_code = 0
    mock_result.stdout = "output"
    mock_result.truncated = True
    mock_run_command.return_value = mock_result

    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)
    handler = registry.get_handler("echo_test")

    result = await handler({"text": "test"})

    assert len(result) == 2
    assert result[0]["text"] == "output"
    assert result[1]["text"] == "[Output was truncated due to size limit]"


@pytest.mark.asyncio
@patch("mcp_stdio_toolbox.tool_registry.run_command")
async def test_tool_handler_command_failure(mock_run_command, sample_tool_config):
    mock_result = AsyncMock()
    mock_result.exit_code = 1
    mock_result.stderr = "error message"
    mock_run_command.return_value = mock_result

    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)
    handler = registry.get_handler("echo_test")

    with pytest.raises(
        RuntimeError, match="Command failed.*exit code 1.*error message"
    ):
        await handler({"text": "test"})


@pytest.mark.asyncio
async def test_tool_handler_invalid_input(sample_tool_config):
    registry = ToolRegistry()
    registry.register_tool(sample_tool_config)
    handler = registry.get_handler("echo_test")

    # Missing required field
    with pytest.raises(ValueError, match="Invalid arguments"):
        await handler({})

    # Wrong type
    with pytest.raises(ValueError, match="Invalid arguments"):
        await handler({"text": 123})
