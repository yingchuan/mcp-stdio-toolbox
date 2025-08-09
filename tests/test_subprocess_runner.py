"""Tests for subprocess runner."""

import pytest

from mcp_stdio_toolbox.subprocess_runner import (
    SubprocessResult,
    build_command_args,
    run_command,
)


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
    result = await run_command(
        "python3", ["-c", "import sys; sys.stderr.write('warning\\n'); print('ok')"]
    )

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
    result = await run_command(
        "python3", ["-c", f"print('{large_text}' * 1000)"], max_output_bytes=500
    )

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


@pytest.mark.asyncio
async def test_stderr_truncation():
    # Test stderr truncation separately
    result = await run_command(
        "python3",
        ["-c", "import sys; sys.stderr.write('e' * 100); sys.stderr.write('\\n')"],
        max_output_bytes=50,
    )

    assert result.truncated
    assert "[OUTPUT TRUNCATED]" in result.stderr
    assert len(result.stderr) <= 50 + len("\n[OUTPUT TRUNCATED]")


@pytest.mark.asyncio
async def test_both_outputs_truncation():
    # Test both stdout and stderr truncation
    script = "import sys; print('o' * 100); sys.stderr.write('e' * 100)"
    result = await run_command("python3", ["-c", script], max_output_bytes=50)

    assert result.truncated
    assert "[OUTPUT TRUNCATED]" in result.stdout
    assert "[OUTPUT TRUNCATED]" in result.stderr


@pytest.mark.asyncio
async def test_unicode_handling():
    # Test unicode characters are handled correctly
    result = await run_command("python3", ["-c", "print('你好世界 🌍')"])

    assert result.exit_code == 0
    assert "你好世界 🌍" in result.stdout


@pytest.mark.asyncio
async def test_large_argument_list():
    # Test with many arguments
    large_args = ["arg" + str(i) for i in range(50)]
    result = await run_command("echo", large_args)

    assert result.exit_code == 0
    assert all(f"arg{i}" in result.stdout for i in range(0, 5, 10))  # Sample check


@pytest.mark.asyncio
async def test_empty_command_args():
    # Test command with no arguments
    result = await run_command("pwd", [])

    assert result.exit_code == 0
    assert len(result.stdout.strip()) > 0


@pytest.mark.asyncio
async def test_command_with_special_chars():
    # Test command arguments with special characters
    result = await run_command("echo", ["test with spaces", "special!@#$%"])

    assert result.exit_code == 0
    assert "test with spaces" in result.stdout
    assert "special!@#$%" in result.stdout


def test_build_command_args_with_multiple_values():
    # Test mapping multiple values from same input
    args_template = ["-f"]
    inputs = {"files": ["file1.txt", "file2.txt"], "verbose": True}
    arg_mapping = [["files"], ["verbose"]]

    result = build_command_args(args_template, inputs, arg_mapping)

    # Each list in arg_mapping should map to string representation
    expected = ["-f", "['file1.txt', 'file2.txt']", "True"]
    assert result == expected


def test_build_command_args_numeric_values():
    # Test with numeric inputs
    args_template = ["-n"]
    inputs = {"count": 42, "ratio": 3.14}
    arg_mapping = [["count"], ["ratio"]]

    result = build_command_args(args_template, inputs, arg_mapping)

    assert result == ["-n", "42", "3.14"]


def test_subprocess_result_initialization():
    # Test SubprocessResult class directly
    result = SubprocessResult("output", "error", 1, True)

    assert result.stdout == "output"
    assert result.stderr == "error"
    assert result.exit_code == 1
    assert result.truncated is True


def test_subprocess_result_defaults():
    # Test SubprocessResult with defaults
    result = SubprocessResult("output", "error", 0)

    assert result.stdout == "output"
    assert result.stderr == "error"
    assert result.exit_code == 0
    assert result.truncated is False
