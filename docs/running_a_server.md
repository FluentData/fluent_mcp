# Running an MCP Server with Fluent MCP

This guide explains how to run an MCP server with Fluent MCP, including configuration, tool registration, and server lifecycle management.

## Server Overview

An MCP server is responsible for:

1. Managing communication with language models (LLMs)
2. Registering and executing tools
3. Processing prompts and messages
4. Handling the server lifecycle

## Creating a Server

There are two main ways to create an MCP server:

### Using the Scaffolder (Recommended)

```python
from fluent_mcp import scaffold_server

result = scaffold_server(
    output_dir=".",
    server_name="my_server",
    description="My MCP server with AI capabilities"
)

print(f"Server created at: {result['path']}")
```

This creates a new directory with the basic structure of an MCP server.

### Creating a Server Directly

```python
from fluent_mcp import create_mcp_server
from my_tools import calculate_sum, get_weather

server = create_mcp_server(
    server_name="my_server",
    embedded_tools=[calculate_sum, get_weather],
    prompts_dir="./prompts",
    config={
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
        "api_key": "ollama"  # Dummy value for Ollama
    }
)
```

## Server Configuration

The `config` parameter accepts the following options:

```python
config = {
    # LLM configuration
    "provider": "ollama",  # or "groq"
    "model": "llama2",    # Model name for the provider
    "base_url": "http://localhost:11434",  # API endpoint
    "api_key": "your_api_key",  # API key for the provider
    
    # Server configuration
    "host": "localhost",  # Server host
    "port": 8000,         # Server port
    "debug": False        # Debug mode
}
```

### Environment Variables

You can also configure the server using environment variables:

```
FLUENT_LOG_LEVEL=INFO
FLUENT_LLM_PROVIDER=ollama
FLUENT_LLM_MODEL=llama2
FLUENT_LLM_BASE_URL=http://localhost:11434
FLUENT_LLM_API_KEY=your_api_key_here
```

Load these variables in your `main.py` file:

```python
from dotenv import load_dotenv
load_dotenv()

# Load environment config
config = {
    "provider": os.getenv("FLUENT_LLM_PROVIDER"),
    "model": os.getenv("FLUENT_LLM_MODEL"),
    "base_url": os.getenv("FLUENT_LLM_BASE_URL"),
    "api_key": os.getenv("FLUENT_LLM_API_KEY"),
}
```

## Registering Tools

Register tools with your server using the `embedded_tools` and `external_tools` parameters:

```python
from my_server.tools.math_tools import calculate_sum, calculate_average
from my_server.tools.external_tools import format_data

server = create_mcp_server(
    server_name="my_server",
    embedded_tools=[calculate_sum, calculate_average],
    external_tools=[format_data],
    config=config
)
```

### Tool Discovery

If you're using a scaffolded project, you can discover and register tools automatically:

```python
import importlib
import inspect
from pathlib import Path

def discover_tools(package_name, package_path):
    """Discover and import all tools in the package."""
    embedded_tools = []
    external_tools = []
    
    # Find all Python files in the tools directory
    tools_dir = Path(package_path) / package_name / "tools"
    if not tools_dir.exists():
        return embedded_tools, external_tools
        
    for py_file in tools_dir.glob("**/*.py"):
        if py_file.name.startswith("_"):
            continue
            
        # Convert file path to module path
        rel_path = py_file.relative_to(package_path)
        module_path = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
        
        # Import the module
        try:
            module = importlib.import_module(module_path)
            
            # Find all registered tools in the module
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, "__wrapped__"):
                    if hasattr(obj, "_is_embedded_tool") and obj._is_embedded_tool:
                        embedded_tools.append(obj)
                    elif hasattr(obj, "_is_external_tool") and obj._is_external_tool:
                        external_tools.append(obj)
        except Exception as e:
            print(f"Error importing {module_path}: {e}")
            
    return embedded_tools, external_tools

# Discover tools
embedded_tools, external_tools = discover_tools("my_server", ".")

# Create server with discovered tools
server = create_mcp_server(
    server_name="my_server",
    embedded_tools=embedded_tools,
    external_tools=external_tools,
    config=config
)
```

## Loading Prompts

Load prompts from a directory:

```python
server = create_mcp_server(
    server_name="my_server",
    embedded_tools=embedded_tools,
    prompts_dir="./prompts",
    config=config
)
```

Prompt files should be in Markdown format with YAML frontmatter:

```markdown
---
name: Text Analysis Prompt
description: A prompt for analyzing text using embedded tools
model: gpt-4
temperature: 0.3
---

You are a text analysis assistant that can analyze text using various tools.

Available tools:
- word_count: Counts the number of words in a text
- reverse_text: Reverses the input text

When asked to analyze text, use these tools to provide insights about the text.
```

## Running the Server

Once configured, run the server:

```python
server.run()
```

This starts the server and begins processing messages through stdin/stdout.

### Main Entry Point

For a complete server entry point (`main.py`):

```python
#!/usr/bin/env python
"""
Main entry point for my MCP server.
"""

import os
import logging
from dotenv import load_dotenv
from fluent_mcp import create_mcp_server

# Import your tools
from my_server.tools.math_tools import calculate_sum, calculate_average
from my_server.tools.text_tools import analyze_text

# Set up logging
load_dotenv()
logging.basicConfig(level=os.getenv("FLUENT_LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    logger.info("Starting my_server...")
    
    # Load environment config
    config = {
        "provider": os.getenv("FLUENT_LLM_PROVIDER"),
        "model": os.getenv("FLUENT_LLM_MODEL"),
        "base_url": os.getenv("FLUENT_LLM_BASE_URL"),
        "api_key": os.getenv("FLUENT_LLM_API_KEY"),
    }
    
    # Register tools
    embedded_tools = [calculate_sum, calculate_average, analyze_text]
    external_tools = []
    
    # Create and run MCP server
    server = create_mcp_server(
        server_name="my_server",
        embedded_tools=embedded_tools,
        external_tools=external_tools,
        prompts_dir="./prompts",
        config=config
    )
    
    logger.info("Server created, starting...")
    server.run()

if __name__ == "__main__":
    main()
```

## Server Lifecycle

The server follows this lifecycle:

1. **Initialization**: Server is created with configuration
2. **Startup**: Tools and prompts are registered
3. **Running**: Server processes messages and executes tools
4. **Shutdown**: Server cleans up resources when stopped

You can add custom logic to each phase:

```python
@asynccontextmanager
async def custom_lifespan(app):
    # Startup
    print("Starting up...")
    
    # Do startup initialization here
    
    yield
    
    # Shutdown
    print("Shutting down...")
    
    # Do cleanup here

# Add custom lifespan to server
server.lifespan = custom_lifespan
```

## Processing Messages

The server processes messages through a message loop:

```python
async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a message and return a response."""
    message_type = message.get("type", "unknown")
    
    # Process different message types
    if message_type == "query":
        # Process query message
        pass
    elif message_type == "tool_call":
        # Process tool call message
        pass
    
    # Return a response
    return {
        "type": f"{message_type}_response",
        "response": "Processed message"
    }
```

## Handling Errors

Add error handling to your server:

```python
try:
    server.run()
except KeyboardInterrupt:
    print("Server stopped by user")
except Exception as e:
    print(f"Error running server: {e}")
    import traceback
    traceback.print_exc()
```

## Advanced Configuration

### Custom LLM Providers

Support for additional LLM providers:

```python
from fluent_mcp.core.llm_client import LLMClient

class CustomLLMClient(LLMClient):
    """Custom LLM client implementation."""
    
    def __init__(self, config):
        """Initialize the custom client."""
        self.provider = "custom"
        self.model = config.get("model")
        self.api_key = config.get("api_key")
        
    async def chat_completion(self, messages, tools=None, temperature=0.3, max_tokens=1000):
        """Implement custom chat completion."""
        # Custom implementation here
        return {
            "status": "complete",
            "content": "Custom response",
            "tool_calls": []
        }

# Register the custom provider
from fluent_mcp.core.llm_client import configure_llm_client

config = {
    "provider": "custom",
    "model": "my-model",
    "api_key": "my-key"
}

# Patch the LLM client class
with patch("fluent_mcp.core.llm_client.LLMClient", CustomLLMClient):
    configure_llm_client(config)
```

## Next Steps

- [Embedded Reasoning](embedded_reasoning.md): Learn how to use embedded reasoning with your tools
- [API Reference](api_reference.md): Explore the full API reference
- [Examples](../examples/): See complete working examples
