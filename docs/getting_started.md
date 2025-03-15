# Getting Started with Fluent MCP

This guide will help you get started with Fluent MCP, a framework for building Model Context Protocol (MCP) servers with intelligent reasoning capabilities.

## What is MCP?

The Model Context Protocol (MCP) is a standard for communication between language models and the tools they can use. It allows models to choose from available tools and execute them programmatically, extending their capabilities beyond just text generation.

Fluent MCP provides a structured way to build servers that implement MCP, making it easier to create AI-powered applications with tool-using capabilities.

## Prerequisites

- Python 3.10 or newer
- Basic understanding of Python async programming
- An API key for your preferred LLM provider (Ollama, Groq, etc.)

## Installation

Install the package from PyPI:

```bash
pip install fluent_mcp
```

Or install directly from the GitHub repository:

```bash
pip install git+https://github.com/yourusername/fluent_mcp.git
```

## Creating Your First MCP Server

### Using the CLI

The quickest way to get started is using the CLI to scaffold a new server:

```bash
fluent-mcp new my_first_server
```

This will create a new directory called `my_first_server` with the basic structure of an MCP server.

### Manual Setup

Alternatively, you can set up a server programmatically:

```python
from fluent_mcp import scaffold_server

scaffold_server(
    output_dir=".",
    server_name="my_first_server",
    description="My first MCP server"
)
```

## Project Structure

After scaffolding, your project will have the following structure:

```
my_first_server/
├── my_first_server/
│   ├── __init__.py
│   ├── tools/
│   │   └── __init__.py
│   ├── prompts/
│   ├── llm/
│   │   └── __init__.py
│   └── tests/
│       └── __init__.py
├── main.py
└── .env.example
```

Key components:
- `main.py`: Entry point for your server
- `my_first_server/tools/`: Directory for your tool definitions
- `my_first_server/prompts/`: Directory for your prompt templates
- `.env.example`: Example environment configuration

## Configuration

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` with your LLM provider details:

```
# Server configuration
FLUENT_LOG_LEVEL=INFO

# LLM configuration
FLUENT_LLM_PROVIDER=ollama
FLUENT_LLM_MODEL=llama2
FLUENT_LLM_BASE_URL=http://localhost:11434
FLUENT_LLM_API_KEY=your_api_key_here
```

## Creating Your First Tool

Create a file in the tools directory:

```python
# my_first_server/tools/math_tools.py
from fluent_mcp.core.tool_registry import register_embedded_tool
from typing import List

@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)
```

## Running Your Server

1. Make sure to import and register your tools in `main.py`:

```python
from my_first_server.tools.math_tools import calculate_sum

# Register tools in the server creation
embedded_tools = [calculate_sum]
```

2. Run your server:

```bash
python main.py
```

## Next Steps

- [Learn how to create more sophisticated tools](creating_tools.md)
- [Explore embedded reasoning capabilities](embedded_reasoning.md)
- [Configure different LLM providers](llm_configuration.md)
- [Test your MCP server](testing.md)

## Troubleshooting

### Common Issues

- **LLM client not configured**: Make sure your `.env` file contains the right API key and provider details.
- **Tool not registered**: Ensure your tools are properly imported and registered with the server.
- **Connection errors**: Check that your LLM provider (e.g., Ollama) is running and accessible.

For more detailed help, see the [troubleshooting guide](troubleshooting.md).
