"""
Example usage of the reflection loop in Fluent MCP.

This script demonstrates how to use the structured reflection loop
for embedded reasoning, allowing the LLM to reflect on its reasoning
process and improve its performance.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List

from fluent_mcp.core.llm_client import configure_llm_client, run_embedded_reasoning
from fluent_mcp.core.tool_registry import register_embedded_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reflection_example")


# Define some example tools for demonstration
@register_embedded_tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@register_embedded_tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@register_embedded_tool()
def divide_numbers(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@register_embedded_tool()
def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


@register_embedded_tool()
def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """
    Get the current weather for a location.

    Args:
        location: The city and country (e.g., "London,UK")
        units: The units to use (metric or imperial)

    Returns:
        A dictionary containing weather information
    """
    # This is a mock implementation
    if units not in ["metric", "imperial"]:
        raise ValueError("Units must be either 'metric' or 'imperial'")

    # Return mock data
    if units == "metric":
        return {
            "location": location,
            "temperature": 22.5,
            "humidity": 65,
            "wind_speed": 10.2,
            "description": "Partly cloudy",
            "units": "metric",
        }
    else:
        return {
            "location": location,
            "temperature": 72.5,
            "humidity": 65,
            "wind_speed": 6.3,
            "description": "Partly cloudy",
            "units": "imperial",
        }


async def run_example():
    """Run the reflection example."""
    try:
        # Configure the LLM client
        # For this example, we'll use a mock LLM client
        # In a real application, you would configure a real LLM client
        config = {
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434",
            "api_key": "ollama",  # Dummy value for Ollama
        }

        llm_client = configure_llm_client(config)

        # Example 1: Math problem with reflection
        logger.info("--- Example 1: Math Problem with Reflection ---")

        system_prompt = """You are a helpful assistant that can perform calculations.
        Use the provided tools to solve math problems."""

        user_prompt = """I have the following numbers: 5, 10, 15, 20, and 25.
        Can you calculate their sum, product, and average?"""

        # Run embedded reasoning with reflection enabled
        result = await run_embedded_reasoning(
            system_prompt=system_prompt, user_prompt=user_prompt, enable_reflection=True, max_reflection_iterations=2
        )

        # Process the result
        if result["status"] == "complete":
            logger.info(f"Response: {result['content']}")

            # Log reflection history if available
            if "reflection_history" in result:
                logger.info(f"Reflection iterations: {result.get('reflection_iterations', 0)}")
                for i, reflection in enumerate(result["reflection_history"]):
                    logger.info(f"Reflection {i+1}:")
                    logger.info(f"  Content: {reflection['reflection']}")

            # Log tool calls
            for tool_call in result["tool_calls"]:
                if tool_call["type"] == "function":
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    logger.info(f"Tool call: {function_name}({arguments})")

            # Log tool results if available
            if "tool_results" in result:
                for tool_result in result["tool_results"]:
                    function_name = tool_result["function_name"]
                    result_value = tool_result["result"]
                    logger.info(f"Tool result: {function_name} = {result_value}")
        else:
            logger.error(f"Error: {result['error']}")

        # Example 2: Weather information with reflection
        logger.info("\n--- Example 2: Weather Information with Reflection ---")

        system_prompt = """You are a helpful assistant that can provide weather information.
        Use the provided tools to get weather data."""

        user_prompt = """What's the current weather in New York?
        Also, can you tell me the weather in London in imperial units?"""

        # Run embedded reasoning with reflection enabled
        result = await run_embedded_reasoning(
            system_prompt=system_prompt, user_prompt=user_prompt, enable_reflection=True, max_reflection_iterations=2
        )

        # Process the result
        if result["status"] == "complete":
            logger.info(f"Response: {result['content']}")

            # Log reflection history if available
            if "reflection_history" in result:
                logger.info(f"Reflection iterations: {result.get('reflection_iterations', 0)}")
                for i, reflection in enumerate(result["reflection_history"]):
                    logger.info(f"Reflection {i+1}:")
                    logger.info(f"  Content: {reflection['reflection']}")

            # Log tool calls
            for tool_call in result["tool_calls"]:
                if tool_call["type"] == "function":
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    logger.info(f"Tool call: {function_name}({arguments})")

            # Log tool results if available
            if "tool_results" in result:
                for tool_result in result["tool_results"]:
                    function_name = tool_result["function_name"]
                    result_value = tool_result["result"]
                    logger.info(f"Tool result: {function_name} = {result_value}")
        else:
            logger.error(f"Error: {result['error']}")

    except Exception as e:
        logger.exception(f"Error in example: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run_example())
