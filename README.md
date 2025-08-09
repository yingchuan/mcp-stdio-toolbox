# MCP Stdio Toolbox

A universal MCP (Model Context Protocol) server that wraps CLI tools as MCP tools through simple YAML configuration.

## Features

- 🔧 **Universal CLI Wrapper**: Convert any CLI tool to an MCP tool via configuration
- ⚡ **Async Execution**: Non-blocking command execution with timeout support
- 📝 **YAML Configuration**: Simple, declarative tool definitions
- 🛡️ **Input Validation**: JSON Schema validation for tool inputs
- 📊 **Output Management**: Automatic truncation and error handling
- 🧪 **Well Tested**: Comprehensive test coverage with pytest

## Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install mcp-stdio-toolbox

# Using pip
pip install mcp-stdio-toolbox
```

### Configuration

Create a `tools.yaml` configuration file:

```yaml
server:
  name: "my-toolbox"
  version: "1.0.0"
  default_timeout_sec: 30
  max_output_bytes: 1048576

tools:
  - name: "echo"
    description: "Echo text to stdout"
    command: "echo"
    args: []
    input_schema:
      type: object
      properties:
        text:
          type: string
          description: "Text to echo"
      required: ["text"]
      arg_mapping:
        - ["text"]

  - name: "grep_file"
    description: "Search patterns in files"
    command: "grep"
    args: ["-n"]
    timeout_sec: 60
    input_schema:
      type: object
      properties:
        pattern:
          type: string
          description: "Pattern to search for"
        file:
          type: string
          description: "File to search in"
      required: ["pattern", "file"]
      arg_mapping:
        - ["pattern"]
        - ["file"]
```

### Usage

#### Standalone Server

```bash
mcp-stdio-toolbox --config tools.yaml
```

#### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "stdio-toolbox": {
      "command": "mcp-stdio-toolbox",
      "args": ["--config", "/path/to/tools.yaml"]
    }
  }
}
```

#### With Claude Code

```bash
claude mcp add stdio-toolbox "mcp-stdio-toolbox --config tools.yaml"
```

## Configuration Reference

### Server Configuration

```yaml
server:
  name: string              # Server name (default: "mcp-stdio-toolbox")
  version: string           # Server version (default: "0.1.0")
  default_timeout_sec: int  # Default timeout in seconds (default: 30)
  max_output_bytes: int     # Max output size in bytes (default: 1048576)
```

### Tool Configuration

```yaml
tools:
  - name: string              # Tool name (required)
    description: string       # Tool description (required)
    command: string          # Command to execute (required)
    args: list               # Default command arguments (default: [])
    timeout_sec: int         # Tool-specific timeout (default: server default)
    input_schema:            # JSON Schema for input validation (required)
      type: object
      properties:
        param_name:
          type: string
          description: "Parameter description"
      required: ["param_name"]
      arg_mapping:           # Maps input parameters to command arguments
        - ["param_name"]     # Each list item becomes a command argument
```

## Examples

### File Operations

```yaml
tools:
  - name: "cat_file"
    description: "Display file contents"
    command: "cat"
    input_schema:
      type: object
      properties:
        file:
          type: string
          description: "File to display"
      required: ["file"]
      arg_mapping:
        - ["file"]

  - name: "find_files"
    description: "Find files by name pattern"
    command: "find"
    args: ["."]
    input_schema:
      type: object
      properties:
        name:
          type: string
          description: "Name pattern to search for"
        type:
          type: string
          enum: ["f", "d"]
          description: "File type (f=file, d=directory)"
          default: "f"
      required: ["name"]
      arg_mapping:
        - ["-name"]
        - ["name"]
        - ["-type"]
        - ["type"]
```

### HTTP Requests

```yaml
tools:
  - name: "curl_get"
    description: "Make HTTP GET request"
    command: "curl"
    args: ["-s", "-L"]
    timeout_sec: 120
    input_schema:
      type: object
      properties:
        url:
          type: string
          description: "URL to fetch"
        headers:
          type: array
          items:
            type: string
          description: "HTTP headers (format: 'Header: Value')"
      required: ["url"]
      arg_mapping:
        - ["url"]
        - ["headers"]
```

### Git Operations

```yaml
tools:
  - name: "git_log"
    description: "Show git commit history"
    command: "git"
    args: ["log", "--oneline"]
    input_schema:
      type: object
      properties:
        max_count:
          type: integer
          description: "Maximum number of commits"
          default: 10
        directory:
          type: string
          description: "Repository directory"
          default: "."
      arg_mapping:
        - ["-C"]
        - ["directory"]
        - ["-n"]
        - ["max_count"]
```

## Development

### Setup

```bash
git clone <repository>
cd mcp-stdio-toolbox
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Lint and format
ruff check src tests
ruff format src tests
```

### Project Structure

```
mcp-stdio-toolbox/
├── src/mcp_stdio_toolbox/
│   ├── __init__.py
│   ├── server.py           # Main MCP server
│   ├── config_loader.py    # YAML configuration loading
│   ├── tool_registry.py    # Dynamic tool registration
│   └── subprocess_runner.py # Async command execution
├── tests/                  # Test suite
├── config/
│   └── tools.example.yaml  # Example configuration
├── pyproject.toml          # Project configuration
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.