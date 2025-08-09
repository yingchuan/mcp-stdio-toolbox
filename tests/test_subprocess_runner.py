"""Tests for subprocess runner."""

import pytest

from mcp_stdio_toolbox.subprocess_runner import run_command, build_command_args


@pytest.mark.asyncio
async def test_successful_command():
    result = await run_command("echo", ["hello", "world"])
    
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello world"
    assert result.stderr == ""
    assert not result.truncated


@pytest.mark.asyncio
async def test_command_with_stderr():
    # Using a command that writes to stderr but exits successfully
    result = await run_command("python3", ["-c", "import sys; sys.stderr.write('warning\\n'); print('ok')"])
    
    assert result.exit_code == 0
    assert "ok" in result.stdout
    assert "warning" in result.stderr


@pytest.mark.asyncio
async def test_command_failure():
    result = await run_command("false", [])
    assert result.exit_code != 0


@pytest.mark.asyncio
async def test_command_not_found():
    with pytest.raises(FileNotFoundError):
        await run_command("nonexistent_command_xyz", [])


@pytest.mark.asyncio
async def test_command_timeout():
    with pytest.raises(TimeoutError):
        await run_command("sleep", ["10"], timeout_sec=1)


@pytest.mark.asyncio
async def test_output_truncation():
    # Generate large output
    large_text = "x" * 100
    result = await run_command("python3", ["-c", f"print('{large_text}' * 1000)"], max_output_bytes=500)
    
    assert result.truncated
    assert "[OUTPUT TRUNCATED]" in result.stdout
    assert len(result.stdout) <= 500 + len("\n[OUTPUT TRUNCATED]")


def test_build_command_args():
    args_template = ["-n", "--verbose"]
    inputs = {"pattern": "test", "file": "example.txt", "unused": "ignored"}
    arg_mapping = [["pattern"], ["file"]]
    
    result = build_command_args(args_template, inputs, arg_mapping)
    
    assert result == ["-n", "--verbose", "test", "example.txt"]


def test_build_command_args_empty():
    result = build_command_args([], {}, [])
    assert result == []


def test_build_command_args_missing_input():
    args_template = []
    inputs = {"pattern": "test"}
    arg_mapping = [["pattern"], ["missing_key"]]
    
    result = build_command_args(args_template, inputs, arg_mapping)
    
    # Should only include the available key
    assert result == ["test"]