"""
Example usage of the tool registry.

This script demonstrates how to register and use embedded tools
with the Fluent MCP tool registry.
"""

import logging
import json
from typing import List, Dict, Any
from fluent_mcp.core.tool_registry import (
    register_embedded_tool,
    get_embedded_tool,
    list_embedded_tools,
    get_tools_as_openai_format
)
from fluent_mcp import create_mcp_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tool_registry_example")

# Define some example tools
@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

@register_embedded_tool(name="fetch_weather")
def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """
    Fetch the current weather for a location.
    
    Args:
        location: The city or location to get weather for
        units: The units to use (metric or imperial)
        
    Returns:
        A dictionary with weather information
    """
    # This is a mock implementation
    return {
        "location": location,
        "temperature": 22.5 if units == "metric" else 72.5,
        "conditions": "Sunny",
        "units": units
    }

@register_embedded_tool()
def generate_greeting(name: str, formal: bool = False) -> str:
    """
    Generate a greeting message.
    
    Args:
        name: The name to greet
        formal: Whether to use a formal greeting
        
    Returns:
        A greeting message
    """
    if formal:
        return f"Good day, {name}. How may I assist you today?"
    else:
        return f"Hey {name}! How's it going?"

def main():
    """Main entry point."""
    logger.info("Tool Registry Example")
    
    # List all registered tools
    tools = list_embedded_tools()
    logger.info(f"Registered tools: {', '.join(tools)}")
    
    # Use a tool directly
    sum_tool = get_embedded_tool("calculate_sum")
    if sum_tool:
        result = sum_tool([1, 2, 3, 4, 5])
        logger.info(f"Sum result: {result}")
    
    # Use another tool
    weather_tool = get_embedded_tool("fetch_weather")
    if weather_tool:
        result = weather_tool("New York", "imperial")
        logger.info(f"Weather result: {json.dumps(result, indent=2)}")
    
    # Get tools in OpenAI format
    openai_tools = get_tools_as_openai_format()
    logger.info(f"Tools in OpenAI format: {json.dumps(openai_tools, indent=2)}")
    
    # Create an MCP server with the registered tools
    logger.info("Creating MCP server with registered tools")
    
    # Get all the tool functions
    embedded_tools = [
        get_embedded_tool(name) for name in list_embedded_tools()
    ]
    
    # Create the server
    server = create_mcp_server(
        server_name="tool_example_server",
        embedded_tools=embedded_tools,
        config={
            "debug": True,
            # Add LLM config if needed
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama"  # Dummy value for Ollama
        }
    )
    
    logger.info("Server created successfully")
    logger.info("In a real application, you would call server.run() here")

if __name__ == "__main__":
    main() 