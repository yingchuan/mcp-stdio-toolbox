"""Async subprocess runner for executing CLI tools."""

import asyncio
from typing import Any


class SubprocessResult:
    def __init__(
        self, stdout: str, stderr: str, exit_code: int, truncated: bool = False
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.truncated = truncated


async def run_command(
    command: str,
    args: list[str],
    timeout_sec: int = 30,
    max_output_bytes: int = 1048576,
) -> SubprocessResult:
    """Run a command with arguments and return the result."""
    try:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=timeout_sec
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Truncate output if too large
        truncated = False
        if len(stdout) > max_output_bytes:
            stdout = stdout[:max_output_bytes] + "\n[OUTPUT TRUNCATED]"
            truncated = True

        if len(stderr) > max_output_bytes:
            stderr = stderr[:max_output_bytes] + "\n[OUTPUT TRUNCATED]"
            truncated = True

        return SubprocessResult(stdout, stderr, process.returncode or 0, truncated)

    except TimeoutError:
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        raise TimeoutError(f"Command timed out after {timeout_sec} seconds") from None

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Command not found: {command}") from e

    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}") from e


def build_command_args(
    args_template: list[str], inputs: dict[str, Any], arg_mapping: list[list[str]]
) -> list[str]:
    """Build command arguments from input mapping."""
    final_args = args_template.copy()

    for mapping in arg_mapping:
        for key in mapping:
            if key in inputs:
                final_args.append(str(inputs[key]))

    return final_args
