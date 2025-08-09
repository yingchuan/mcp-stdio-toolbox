"""Tests for config loader."""

import tempfile
from pathlib import Path

import pytest

from mcp_stdio_toolbox.config_loader import load_config


def test_load_valid_config():
    config_yaml = """
server:
  name: "test-server"
  version: "1.0.0"
  default_timeout_sec: 60
  max_output_bytes: 2097152

tools:
  - name: "echo"
    description: "Echo text"
    command: "echo"
    args: []
    input_schema:
      type: object
      properties:
        text: { type: string }
      required: ["text"]
      arg_mapping:
        - ["text"]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.server.name == "test-server"
        assert config.server.version == "1.0.0"
        assert config.server.default_timeout_sec == 60
        assert config.server.max_output_bytes == 2097152

        assert len(config.tools) == 1
        tool = config.tools[0]
        assert tool.name == "echo"
        assert tool.description == "Echo text"
        assert tool.command == "echo"
        assert tool.args == []
        assert tool.timeout_sec == 60  # inherited from server default

    finally:
        Path(config_path).unlink()


def test_load_minimal_config():
    config_yaml = """
tools:
  - name: "simple"
    description: "Simple tool"
    command: "date"
    input_schema:
      type: object
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        config_path = f.name

    try:
        config = load_config(config_path)

        # Check defaults
        assert config.server.name == "mcp-stdio-toolbox"
        assert config.server.version == "0.1.0"
        assert config.server.default_timeout_sec == 30

        tool = config.tools[0]
        assert tool.name == "simple"
        assert tool.args == []
        assert tool.timeout_sec == 30

    finally:
        Path(config_path).unlink()


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path.yaml")


def test_missing_tools_section():
    config_yaml = """
server:
  name: "test"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Config must contain 'tools' section"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_invalid_tool_config():
    config_yaml = """
tools:
  - name: "incomplete"
    description: "Missing required fields"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Tool missing required fields"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()
