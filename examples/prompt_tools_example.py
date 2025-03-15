"""
Example demonstrating how to use prompts with tool definitions in Fluent MCP.

This script shows how to:
1. Load prompts with tool definitions from a directory
2. Access the tools defined in the prompts
3. Use the prompts with embedded reasoning
"""

import asyncio
import logging
import os
from typing import Any, Dict, List

from fluent_mcp.core.llm_client import run_embedded_reasoning
from fluent_mcp.core.prompt_loader import get_prompt_tools, load_prompts
from fluent_mcp.core.server import MCPServer
from fluent_mcp.core.tool_registry import embedded_tool


# Define some example embedded tools for demonstration
@embedded_tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@embedded_tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@embedded_tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"The weather in {location} is sunny and 72 degrees."


async def run_math_example(server: MCPServer) -> None:
    """
    Run an example using the math tools prompt.

    Args:
        server: The MCP server with loaded prompts
    """
    # Get the math tools prompt
    math_prompt = server.get_prompt("math_tools")
    if not math_prompt:
        logging.error("Math tools prompt not found")
        return

    logging.info(f"Using prompt: {math_prompt['config']['name']}")

    # Get the tools defined in the prompt
    tools = get_prompt_tools(math_prompt)
    logging.info(f"Prompt has {len(tools)} tools defined")
    for tool in tools:
        logging.info(f"  Tool: {tool['function']['name']}")

    # Run embedded reasoning with the prompt
    result = await run_embedded_reasoning(
        system_prompt=math_prompt["template"], user_prompt="What is 7 + 4?", prompt=math_prompt
    )

    logging.info("Embedded reasoning result:")
    logging.info(f"  Content: {result['content']}")

    # Check if tool calls were made
    if result["tool_calls"]:
        logging.info(f"Tool calls made: {len(result['tool_calls'])}")
        for call in result["tool_calls"]:
            logging.info(f"  Tool: {call['function']['name']}")
            logging.info(f"  Arguments: {call['function']['arguments']}")


async def run_weather_example(server: MCPServer) -> None:
    """
    Run an example using the weather tools prompt.

    Args:
        server: The MCP server with loaded prompts
    """
    # Get the weather tools prompt
    weather_prompt = server.get_prompt("weather_tools")
    if not weather_prompt:
        logging.error("Weather tools prompt not found")
        return

    logging.info(f"Using prompt: {weather_prompt['config']['name']}")

    # Get the tools defined in the prompt
    tools = get_prompt_tools(weather_prompt)
    logging.info(f"Prompt has {len(tools)} tools defined")
    for tool in tools:
        logging.info(f"  Tool: {tool['function']['name']}")

    # Run embedded reasoning with the prompt
    result = await run_embedded_reasoning(
        system_prompt=weather_prompt["template"],
        user_prompt="What's the weather like in Seattle?",
        prompt=weather_prompt,
    )

    logging.info("Embedded reasoning result:")
    logging.info(f"  Content: {result['content']}")

    # Check if tool calls were made
    if result["tool_calls"]:
        logging.info(f"Tool calls made: {len(result['tool_calls'])}")
        for call in result["tool_calls"]:
            logging.info(f"  Tool: {call['function']['name']}")
            logging.info(f"  Arguments: {call['function']['arguments']}")


async def run_multi_tools_example(server: MCPServer) -> None:
    """
    Run an example using the multi tools prompt.

    Args:
        server: The MCP server with loaded prompts
    """
    # Get the multi tools prompt
    multi_prompt = server.get_prompt("multi_tools")
    if not multi_prompt:
        logging.error("Multi tools prompt not found")
        return

    logging.info(f"Using prompt: {multi_prompt['config']['name']}")

    # Get the tools defined in the prompt
    tools = get_prompt_tools(multi_prompt)
    logging.info(f"Prompt has {len(tools)} tools defined")
    for tool in tools:
        logging.info(f"  Tool: {tool['function']['name']}")

    # Run embedded reasoning with the prompt for math
    math_result = await run_embedded_reasoning(
        system_prompt=multi_prompt["template"], user_prompt="What is 5 multiplied by 3?", prompt=multi_prompt
    )

    logging.info("Math embedded reasoning result:")
    logging.info(f"  Content: {math_result['content']}")

    # Check if tool calls were made
    if math_result["tool_calls"]:
        logging.info(f"Tool calls made: {len(math_result['tool_calls'])}")
        for call in math_result["tool_calls"]:
            logging.info(f"  Tool: {call['function']['name']}")
            logging.info(f"  Arguments: {call['function']['arguments']}")

    # Run embedded reasoning with the prompt for weather
    weather_result = await run_embedded_reasoning(
        system_prompt=multi_prompt["template"], user_prompt="What's the weather like in New York?", prompt=multi_prompt
    )

    logging.info("Weather embedded reasoning result:")
    logging.info(f"  Content: {weather_result['content']}")

    # Check if tool calls were made
    if weather_result["tool_calls"]:
        logging.info(f"Tool calls made: {len(weather_result['tool_calls'])}")
        for call in weather_result["tool_calls"]:
            logging.info(f"  Tool: {call['function']['name']}")
            logging.info(f"  Arguments: {call['function']['arguments']}")


async def main() -> None:
    """
    Main entry point for the script.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get the path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    logging.info(f"Loading prompts from: {prompts_dir}")

    # Load prompts from the directory
    prompts = load_prompts(prompts_dir)
    logging.info(f"Loaded {len(prompts)} prompts")

    # Create an MCP server with the loaded prompts
    server = MCPServer(prompts=prompts)

    # Log information about the prompts
    for prompt in prompts:
        name = prompt["config"]["name"]
        description = prompt["config"]["description"]
        logging.info(f"Prompt: {name} - {description}")

        # Log tools if present
        if "tools" in prompt["config"]:
            tools = prompt["config"]["tools"]
            logging.info(f"  Tools: {', '.join(tools)}")

    # Run the examples
    await run_math_example(server)
    await run_weather_example(server)
    await run_multi_tools_example(server)


if __name__ == "__main__":
    asyncio.run(main())
