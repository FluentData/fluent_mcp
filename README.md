# Fluent MCP

A modern framework for building Model Context Protocol (MCP) servers with intelligent reasoning capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

Fluent MCP is a toolkit for scaffolding and managing MCP servers with a focus on AI integration. It provides a structured approach to building servers that can perform embedded reasoning with language models, register and execute tools, and manage prompts and configurations.

The framework is designed to be extensible, allowing LLMs to build and register their own tools, supporting the development of self-improving AI systems.

## Core Architecture Pattern

Fluent MCP implements a powerful architectural pattern that fundamentally changes how AI systems interact:

### Two-Tier LLM Architecture
- **Embedded LLM**: An internal LLM that performs complex reasoning and multi-step tasks
- **Consuming LLM**: The external LLM (like Claude) that interacts with your MCP server

### Tool Separation
- **Embedded Tools**: Internal tools that are ONLY available to the embedded LLM, not exposed externally
- **External Tools**: Tools that are exposed to consuming LLMs through the MCP protocol

### Reasoning Offloading
- Complex multi-step reasoning is offloaded from the consuming LLM to the embedded LLM
- External tools can leverage embedded reasoning internally while presenting a simple interface
- This creates a "reasoning sandwich" where complex logic happens in the middle layer

### Benefits
- **Token Efficiency**: Consuming LLMs use fewer tokens by offloading reasoning to embedded LLMs
- **Cost Reduction**: Smaller, specialized models can handle specific reasoning tasks at lower cost
- **Complexity Hiding**: Complex multi-step processes are hidden behind simple interfaces
- **Separation of Concerns**: Clear boundaries between what's exposed and what's internal

![Fluent MCP Architecture](docs/images/architecture_diagram.png)

## Features

- **Reasoning Offloading**: Offload complex reasoning from consuming LLMs to embedded LLMs for token and cost efficiency
- **Tool Separation**: Clear distinction between embedded tools (internal) and external tools (exposed)
- **Server Scaffolding**: Generate new MCP server projects with the proper structure
- **LLM Integration**: Seamlessly connect to language models from different providers
- **Tool Registry**: Register both embedded tools (used internally) and external tools (exposed to consuming LLMs)
- **Embedded Reasoning**: Run reasoning with LLMs and execute their tool calls
- **Prompt Management**: Load and manage prompts from files with support for tool definitions in frontmatter
- **Error Handling**: Robust error handling for LLM integration and tool execution

## Installation

```bash
pip install fluent_mcp
```

For development:

```bash
# Clone the repository
git clone https://github.com/yourusername/fluent_mcp.git
cd fluent_mcp

# Install in development mode with extra dependencies
pip install -e ".[dev]"
```

## Quick Start

### Creating a New Server

Use the CLI to scaffold a new server:

```bash
fluent-mcp new my_server
```

Or create a server programmatically:

```python
from fluent_mcp import scaffold_server

scaffold_server(
    output_dir=".",
    server_name="my_server",
    description="My MCP server with AI capabilities"
)
```

### Implementing the Core Architecture Pattern

```python
from fluent_mcp.core.tool_registry import register_embedded_tool, register_external_tool
from fluent_mcp.core.llm_client import run_embedded_reasoning
import asyncio

# 1. Define embedded tools (ONLY available to the embedded LLM)
@register_embedded_tool()
def search_database(query: str) -> list:
    """Search the database for information (only used internally)."""
    # Implementation...
    return ["result1", "result2"]

@register_embedded_tool()
def analyze_data(data: list) -> dict:
    """Analyze data and extract insights (only used internally)."""
    # Implementation...
    return {"key_insight": "finding", "confidence": 0.95}

# 2. Define an external tool that leverages embedded reasoning
@register_external_tool()
async def research_question(question: str) -> dict:
    """
    Research a question and provide a comprehensive answer.
    
    This external tool is exposed to consuming LLMs but internally
    uses embedded reasoning with access to embedded tools.
    """
    # Define system prompt for embedded reasoning
    system_prompt = """
    You are a research assistant with access to internal tools:
    - search_database: Search for information
    - analyze_data: Analyze and extract insights
    
    Use these tools to thoroughly research the question.
    """
    
    # Run embedded reasoning (this is where the magic happens)
    result = await run_embedded_reasoning(
        system_prompt=system_prompt,
        user_prompt=f"Research this question: {question}"
    )
    
    # Return a clean, structured response to the consuming LLM
    return {
        "answer": result["content"],
        "confidence": 0.9,
        "sources": ["source1", "source2"]
    }
```

### Running a Server with the Architecture Pattern

```python
from fluent_mcp import create_mcp_server
from my_tools import search_database, analyze_data, research_question

# Create and run MCP server
server = create_mcp_server(
    server_name="my_server",
    # Embedded tools (ONLY available to the embedded LLM)
    embedded_tools=[search_database, analyze_data],
    # External tools (exposed to consuming LLMs)
    external_tools=[research_question],
    config={
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
        "api_key": "ollama"
    }
)

server.run()
```

### Using Prompts with Tool Definitions

Fluent MCP supports defining which tools are available to a prompt directly in the prompt's frontmatter:

```markdown
---
name: math_tools
description: A prompt that uses math-related tools
model: gpt-4
temperature: 0.3
tools:
  - add_numbers
  - multiply_numbers
---
You are a math assistant that can perform calculations.
Use the available tools to help solve math problems.
```

When using this prompt with embedded reasoning, only the specified tools will be available:

```python
from fluent_mcp.core.llm_client import run_embedded_reasoning

# Get a prompt with tool definitions
math_prompt = server.get_prompt("math_tools")

# Run embedded reasoning with only the tools defined in the prompt
result = await run_embedded_reasoning(
    system_prompt=math_prompt["template"],
    user_prompt="What is 5 + 3?",
    prompt=math_prompt  # Pass the prompt to use its tool definitions
)
```

This approach allows for more precise control over which tools are available to different prompts, improving security and reducing the chance of unintended tool usage.

## Documentation

For more detailed documentation, see the [docs directory](docs/):

- [Getting Started](docs/getting_started.md)
- [Creating Tools](docs/creating_tools.md)
- [Running a Server](docs/running_a_server.md)
- [Embedded Reasoning](docs/embedded_reasoning.md)
- [Rate Limiting](docs/rate_limiting.md)
- [Self-Improving Systems](docs/self_improving_systems.md)
- [Troubleshooting](docs/troubleshooting.md)
- [API Reference](docs/api_reference.md)

## Examples

Check out the [examples directory](examples/) for complete working examples:

- [Tool Registry Example](examples/tool_registry_example.py)
- [Embedded Reasoning Example](examples/embedded_reasoning_example.py)
- [External Tools Example](examples/external_tools_example.py)
- [Reasoning External Tool Example](examples/reasoning_external_tool_example.py)
- [Prompt Loader Example](examples/prompt_loader_example.py)
- [Prompt Tools Example](examples/prompt_tools_example.py)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
black .
isort .
```

## License

MIT
