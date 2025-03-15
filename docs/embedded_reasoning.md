# Embedded Reasoning with Fluent MCP

This guide explains how to use embedded reasoning with Fluent MCP, a powerful feature that allows language models to use tools for reasoning and problem-solving.

## What is Embedded Reasoning?

Embedded reasoning enables language models to:

1. Process a user's request
2. Decide which tools to call
3. Execute those tools
4. Use the tool results to formulate a comprehensive response

This process happens through a single function call and provides a seamless way for LLMs to enhance their capabilities using your custom tools.

## Basic Usage

Here's the simplest way to use embedded reasoning:

```python
from fluent_mcp.core.llm_client import run_embedded_reasoning

# Define the prompts
system_prompt = """You are a helpful assistant that can perform calculations.
Use the provided tools to solve math problems."""

user_prompt = """I have the following numbers: 5, 10, 15, 20, and 25.
Can you calculate their sum, product, and average?"""

# Run embedded reasoning
result = await run_embedded_reasoning(system_prompt, user_prompt)

# Process the result
print(f"LLM response: {result['content']}")

for tool_call in result["tool_calls"]:
    if tool_call["type"] == "function":
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]
        
        print(f"Tool call: {function_name}({arguments})")
        
        # Execute the tool call (in a real application)
```

## Setting Up Embedded Reasoning

### 1. Configure the LLM Client

First, configure the LLM client:

```python
from fluent_mcp.core.llm_client import configure_llm_client

config = {
    "provider": "ollama",
    "model": "llama2",
    "base_url": "http://localhost:11434",
    "api_key": "ollama"  # Dummy value for Ollama
}

llm_client = configure_llm_client(config)
```

### 2. Register Your Tools

Register the tools you want to use for reasoning:

```python
from fluent_mcp.core.tool_registry import register_embedded_tool
from typing import List, Dict, Any

@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

@register_embedded_tool()
def calculate_product(numbers: List[float]) -> float:
    """Calculate the product of a list of numbers."""
    result = 1
    for num in numbers:
        result *= num
    return result

@register_embedded_tool()
def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
```

### 3. Run Embedded Reasoning

Now you can run embedded reasoning:

```python
# Async function that uses embedded reasoning
async def process_math_query(query: str) -> Dict[str, Any]:
    system_prompt = """You are a math assistant that can perform calculations.
    Use the provided tools to solve mathematical problems."""
    
    result = await run_embedded_reasoning(system_prompt, query)
    
    # Process tool calls and execute them
    responses = []
    for tool_call in result["tool_calls"]:
        if tool_call["type"] == "function":
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            
            # Get the tool function
            from fluent_mcp.core.tool_registry import get_embedded_tool
            tool_fn = get_embedded_tool(function_name)
            
            if tool_fn:
                # Execute the tool
                try:
                    tool_result = tool_fn(**arguments)
                    responses.append({
                        "tool": function_name,
                        "arguments": arguments,
                        "result": tool_result
                    })
                except Exception as e:
                    responses.append({
                        "tool": function_name,
                        "arguments": arguments,
                        "error": str(e)
                    })
    
    return {
        "llm_response": result["content"],
        "tool_responses": responses
    }
```

## Complete Example

Here's a complete example of using embedded reasoning:

```python
import asyncio
import json
import logging
from typing import Any, Dict, List

from fluent_mcp.core.llm_client import configure_llm_client, run_embedded_reasoning
from fluent_mcp.core.tool_registry import register_embedded_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedded_reasoning_example")

# Define and register tools
@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

@register_embedded_tool()
def calculate_product(numbers: List[float]) -> float:
    """Calculate the product of a list of numbers."""
    result = 1
    for num in numbers:
        result *= num
    return result

@register_embedded_tool()
def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """Get the current weather for a location."""
    # Mock implementation
    return {
        "location": location,
        "temperature": 22 if units == "metric" else 72,
        "condition": "Sunny",
        "humidity": 65,
    }

async def run_example():
    # Configure LLM client
    config = {
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
        "api_key": "ollama"
    }
    
    try:
        configure_llm_client(config)
        
        # Example 1: Math calculation
        logger.info("--- Example 1: Math Calculation ---")
        system_prompt = """You are a helpful assistant that can perform calculations.
        Use the provided tools to solve math problems."""
        
        user_prompt = """I have the following numbers: 5, 10, 15, 20, and 25.
        Can you calculate their sum, product, and average?"""
        
        result = await run_embedded_reasoning(system_prompt, user_prompt)
        
        if result["status"] == "complete":
            logger.info(f"Response: {result['content']}")
            
            # Process tool calls
            for tool_call in result["tool_calls"]:
                if tool_call["type"] == "function":
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    logger.info(f"Tool call: {function_name}({arguments})")
                    
                    # Execute the tool call
                    from fluent_mcp.core.tool_registry import get_embedded_tool
                    tool_fn = get_embedded_tool(function_name)
                    
                    if tool_fn:
                        tool_result = tool_fn(**arguments)
                        logger.info(f"Tool result: {tool_result}")
        else:
            logger.error(f"Error: {result['error']}")
        
        # Example 2: Weather information
        logger.info("\n--- Example 2: Weather Information ---")
        system_prompt = """You are a helpful assistant that can provide weather information.
        Use the provided tools to get weather data."""
        
        user_prompt = """What's the current weather in New York?"""
        
        result = await run_embedded_reasoning(system_prompt, user_prompt)
        
        if result["status"] == "complete":
            logger.info(f"Response: {result['content']}")
            
            # Process tool calls
            for tool_call in result["tool_calls"]:
                if tool_call["type"] == "function":
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    logger.info(f"Tool call: {function_name}({arguments})")
                    
                    # Execute the tool call
                    from fluent_mcp.core.tool_registry import get_embedded_tool
                    tool_fn = get_embedded_tool(function_name)
                    
                    if tool_fn:
                        tool_result = tool_fn(**arguments)
                        logger.info(f"Tool result: {json.dumps(tool_result, indent=2)}")
        else:
            logger.error(f"Error: {result['error']}")
            
    except Exception as e:
        logger.exception(f"Error in example: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_example())
```

## Advanced Use Cases

### Multi-Turn Reasoning

For complex problems requiring multiple turns of reasoning:

```python
async def multi_turn_reasoning(problem: str):
    # First reasoning turn
    system_prompt = "You are a problem-solving assistant. First, analyze the problem."
    result1 = await run_embedded_reasoning(system_prompt, problem)
    
    # Extract information from first turn
    analysis = result1["content"]
    
    # Second reasoning turn with additional context
    system_prompt = f"""You are a problem-solving assistant.
    Previous analysis: {analysis}
    
    Now, use the provided tools to solve the problem step by step."""
    
    result2 = await run_embedded_reasoning(system_prompt, problem)
    
    # Process tool calls from second turn
    # ...
    
    return result2
```

### Tool Result Integration

Feed tool results back to the LLM for further processing:

```python
async def reasoning_with_tool_results(query: str):
    # First reasoning turn
    system_prompt = "You are a helpful assistant. Use tools to gather information."
    result1 = await run_embedded_reasoning(system_prompt, query)
    
    # Execute tool calls and collect results
    tool_results = []
    for tool_call in result1["tool_calls"]:
        if tool_call["type"] == "function":
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            
            # Get and execute the tool
            tool_fn = get_embedded_tool(function_name)
            if tool_fn:
                result = tool_fn(**arguments)
                tool_results.append({
                    "tool": function_name,
                    "arguments": arguments,
                    "result": result
                })
    
    # Second reasoning turn with tool results
    tool_results_str = json.dumps(tool_results, indent=2)
    system_prompt = f"""You are a helpful assistant.
    You previously used tools to gather information. Here are the results:
    
    {tool_results_str}
    
    Use this information to provide a comprehensive response."""
    
    result2 = await run_embedded_reasoning(system_prompt, query)
    
    return result2
```

## Best Practices

1. **Clear System Prompts**: Provide clear instructions in the system prompt
2. **Tool Documentation**: Write detailed docstrings for your tools
3. **Error Handling**: Gracefully handle tool execution errors
4. **Tool Composition**: Design tools that can be composed for complex tasks
5. **Feedback Loop**: For complex problems, implement a feedback loop with tool results
6. **Logging**: Log tool calls and results for debugging

## Common Issues and Solutions

### LLM Not Using Tools

If the LLM isn't using your tools:

1. Ensure your tools are registered correctly
2. Check that your system prompt explicitly instructs the LLM to use tools
3. Make the user prompt more specific about what tools to use
4. Verify the LLM provider supports function calling

### Tool Execution Errors

If tools fail during execution:

1. Validate tool input before processing
2. Add try-except blocks in your tools
3. Return structured error messages that the LLM can understand

```python
@register_embedded_tool()
def safe_division(dividend: float, divisor: float) -> Dict[str, Any]:
    """Safely divide two numbers."""
    try:
        if divisor == 0:
            return {"success": False, "error": "Division by zero"}
        result = dividend / divisor
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Next Steps

- [API Reference](api_reference.md): Explore the full Fluent MCP API
- [Example: Embedded Reasoning](../examples/embedded_reasoning_example.py): See a complete example
- [Advanced Configuration](advanced_configuration.md): Learn about advanced configuration options
