# Creating Tools with Fluent MCP

This guide explains how to create and register tools with Fluent MCP. The framework supports two types of tools:

1. **Embedded Tools**: Used by the LLM directly for reasoning and executing actions
2. **External Tools**: Exposed for external use, typically by AI coders or other MCP frontends

## Tool Registry Overview

Fluent MCP's tool registry provides decorators and functions for registering, discovering, and using tools. The key components are:

- `register_embedded_tool()`: Decorator for registering embedded tools
- `register_external_tool()`: Decorator for registering external tools
- `get_embedded_tool()`, `get_external_tool()`: Functions to retrieve tools by name
- `list_embedded_tools()`, `list_external_tools()`: Functions to list all registered tools
- `get_tools_as_openai_format()`: Function to get embedded tools in OpenAI function calling format

## Creating Embedded Tools

Embedded tools are used directly by the LLM during reasoning. To create an embedded tool:

```python
from fluent_mcp.core.tool_registry import register_embedded_tool
from typing import List, Dict, Any

@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: The list of numbers to sum
        
    Returns:
        The sum of the numbers
    """
    return sum(numbers)
```

### Naming Tools

By default, the tool name will be the function name. You can specify a custom name:

```python
@register_embedded_tool(name="add_numbers")
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)
```

### Tool Documentation

The tool's docstring is crucial as it's used to generate the tool description for the LLM. Make sure to:

1. Provide a clear, concise description of what the tool does
2. Document all parameters with proper types
3. Describe what the tool returns
4. Include examples if helpful

```python
@register_embedded_tool()
def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """
    Get the current weather for a location.
    
    Args:
        location: The city or location to get weather for (e.g., "New York", "London")
        units: The units to use - either "metric" or "imperial"
    
    Returns:
        A dictionary with weather information including temperature, 
        conditions, humidity, and wind speed
        
    Example:
        >>> get_weather("San Francisco", "metric")
        {
            "location": "San Francisco",
            "temperature": 18,
            "condition": "Foggy",
            "humidity": 85,
            "wind_speed": 15
        }
    """
    # Implementation here
```

### Type Annotations

Fluent MCP uses type annotations to generate the schema for the tool parameters. Supported types include:

- Basic types: `str`, `int`, `float`, `bool`
- Container types: `List[T]`, `Dict[K, V]`
- Optional parameters should have default values

## Creating External Tools

External tools are similar to embedded tools but are intended for use by external systems:

```python
from fluent_mcp.core.tool_registry import register_external_tool
from typing import Dict, Any

@register_external_tool()
def format_data(data: Dict[str, Any], pretty: bool = False) -> str:
    """
    Format a data dictionary as a string.
    
    Args:
        data: The data dictionary to format
        pretty: Whether to use pretty formatting with indentation
        
    Returns:
        The formatted data as a string
    """
    import json
    return json.dumps(data, indent=4 if pretty else None)
```

## Registering Tools Programmatically

Besides using decorators, you can register tools programmatically:

```python
from fluent_mcp.core.tool_registry import register_tool, register_external_tools

# Register a single tool
register_tool(calculate_sum)

# Register multiple external tools
external_tools = [format_data, convert_units, generate_report]
register_external_tools(external_tools)
```

## Testing Tools

Create unit tests for your tools to ensure they work as expected:

```python
def test_calculate_sum():
    result = calculate_sum([1, 2, 3, 4, 5])
    assert result == 15
    
    result = calculate_sum([])
    assert result == 0
    
    result = calculate_sum([-1, 1])
    assert result == 0
```

## Common Tool Patterns

### Working with External APIs

```python
@register_embedded_tool()
async def search_wikipedia(query: str, limit: int = 3) -> Dict[str, Any]:
    """
    Search Wikipedia for the given query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        Dictionary with search results
    """
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit
        }
        async with session.get("https://en.wikipedia.org/w/api.php", params=params) as response:
            data = await response.json()
            return {
                "query": query,
                "results": [
                    {
                        "title": result["title"],
                        "snippet": result["snippet"]
                    }
                    for result in data["query"]["search"]
                ]
            }
```

### Data Processing Tools

```python
@register_embedded_tool()
def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze text and return various statistics.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    return {
        "character_count": len(text),
        "word_count": len(words),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "sentence_count": text.count(".") + text.count("!") + text.count("?"),
    }
```

## Best Practices

1. **Keep tools focused**: Each tool should do one thing well
2. **Provide clear documentation**: Write clear docstrings explaining what the tool does
3. **Handle errors gracefully**: Catch exceptions and return meaningful error messages
4. **Use appropriate types**: Properly type your parameters and return values
5. **Consider performance**: For tools that might be called frequently, optimize for speed
6. **Add validation**: Validate input parameters to prevent errors
7. **Return structured data**: Return well-structured data that's easy to process

## Advanced Topics

### Tool Dependencies

Tools can use other tools:

```python
@register_embedded_tool()
def analyze_numbers(numbers: List[float]) -> Dict[str, Any]:
    """Analyze a list of numbers."""
    from fluent_mcp.core.tool_registry import get_embedded_tool
    
    calculate_sum = get_embedded_tool("calculate_sum")
    calculate_average = get_embedded_tool("calculate_average")
    
    return {
        "sum": calculate_sum(numbers),
        "average": calculate_average(numbers),
        "min": min(numbers) if numbers else None,
        "max": max(numbers) if numbers else None,
    }
```

### Asynchronous Tools

For I/O-bound operations, create async tools:

```python
@register_embedded_tool()
async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data from a URL."""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return {"status": "success", "data": await response.json()}
            else:
                return {"status": "error", "code": response.status}
```

## Registering Tools with Your Server

When creating your server, register your tools:

```python
from fluent_mcp import create_mcp_server
from my_package.tools.math_tools import calculate_sum, calculate_average
from my_package.tools.text_tools import analyze_text
from my_package.tools.external_tools import format_data

# Create and run MCP server
server = create_mcp_server(
    server_name="my_server",
    embedded_tools=[calculate_sum, calculate_average, analyze_text],
    external_tools=[format_data],
    config={
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
    }
)
```

## Next Steps

- [Running a Server](running_a_server.md): Learn how to run your MCP server with registered tools
- [Embedded Reasoning](embedded_reasoning.md): Understand how to use tools with embedded reasoning
- [Tool Examples](../examples/tool_registry_example.py): See complete tool examples
