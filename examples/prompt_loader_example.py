"""
Example usage of the prompt loader in Fluent MCP.

This script demonstrates how to load prompts from a directory,
create an MCP server with the loaded prompts, and access and use
those prompts.
"""

import logging
import os
import tempfile
from typing import Dict, List, Optional

from fluent_mcp.core.prompt_loader import PromptLoader, load_prompts
from fluent_mcp.core.server import MCPServer
from fluent_mcp.core.tool_registry import embedded_tool, external_tool


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


def create_example_prompts(directory: str) -> None:
    """
    Create example prompt files in the specified directory.

    Args:
        directory: Directory to create prompt files in
    """
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Basic prompt with minimal frontmatter
    basic_prompt = """---
name: basic
description: A basic prompt for testing
---
This is a basic prompt for testing the prompt loader.
"""

    # System prompt with model type and temperature
    system_prompt = """---
name: system
description: A system prompt for the LLM
model: gpt-4
temperature: 0.7
---
You are a helpful AI assistant. Answer the user's questions to the best of your ability.
"""

    # Complex prompt with multiple frontmatter fields
    complex_prompt = """---
name: complex
description: A complex prompt with multiple frontmatter fields
model: gpt-4
temperature: 0.5
max_tokens: 1000
top_p: 0.9
---
You are a specialized AI assistant for helping with coding tasks.
The user will ask you questions about programming, and you should
provide helpful, accurate responses.
"""

    # Specialized prompt for a specific task
    specialized_prompt = """---
name: specialized
description: A specialized prompt for a specific task
model: gpt-3.5-turbo
temperature: 0.2
---
You are an AI assistant specialized in explaining complex concepts
in simple terms. When the user asks about a complex topic, break it
down into easy-to-understand explanations.
"""

    # Prompt with tool definitions in frontmatter
    tools_prompt = """---
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
"""

    # Prompt with weather tool in frontmatter
    weather_prompt = """---
name: weather_tools
description: A prompt that uses weather-related tools
model: gpt-4
temperature: 0.3
tools:
  - get_weather
---
You are a weather assistant that can provide weather information.
Use the available tools to help answer weather-related questions.
"""

    # Prompt with multiple tools in frontmatter
    multi_tools_prompt = """---
name: multi_tools
description: A prompt that uses multiple tools
model: gpt-4
temperature: 0.3
tools:
  - add_numbers
  - multiply_numbers
  - get_weather
---
You are a versatile assistant that can perform calculations and provide weather information.
Use the available tools to help answer the user's questions.
"""

    # Write the prompts to files
    with open(os.path.join(directory, "basic.md"), "w") as f:
        f.write(basic_prompt)

    with open(os.path.join(directory, "system.md"), "w") as f:
        f.write(system_prompt)

    with open(os.path.join(directory, "complex.md"), "w") as f:
        f.write(complex_prompt)

    with open(os.path.join(directory, "specialized.md"), "w") as f:
        f.write(specialized_prompt)

    with open(os.path.join(directory, "math_tools.md"), "w") as f:
        f.write(tools_prompt)

    with open(os.path.join(directory, "weather_tools.md"), "w") as f:
        f.write(weather_prompt)

    with open(os.path.join(directory, "multi_tools.md"), "w") as f:
        f.write(multi_tools_prompt)


def main() -> None:
    """
    Main entry point for the script.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create a temporary directory for prompts
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create example prompts
        create_example_prompts(temp_dir)

        # Load prompts from the directory
        prompts = load_prompts(temp_dir)

        # Create an MCP server with the loaded prompts
        server = MCPServer(prompts=prompts)

        # Log information about the prompts
        logging.info(f"Loaded {len(prompts)} prompts")
        for prompt in prompts:
            name = prompt["config"]["name"]
            description = prompt["config"]["description"]
            logging.info(f"Prompt: {name} - {description}")

            # Log tools if present
            if "tools" in prompt["config"]:
                tools = prompt["config"]["tools"]
                logging.info(f"  Tools: {', '.join(tools)}")

        # Demonstrate accessing a prompt by name
        basic_prompt = server.get_prompt("basic")
        if basic_prompt:
            logging.info(f"Retrieved prompt: {basic_prompt['config']['name']}")
            logging.info(f"Template: {basic_prompt['template']}")

        # Demonstrate accessing a prompt with tools
        math_tools_prompt = server.get_prompt("math_tools")
        if math_tools_prompt:
            logging.info(f"Retrieved prompt with tools: {math_tools_prompt['config']['name']}")
            logging.info(f"Tools: {', '.join(math_tools_prompt['config']['tools'])}")

        # Demonstrate creating a second server using the prompts directory parameter
        server2 = MCPServer(prompts_dir=temp_dir)
        logging.info(f"Created second server with prompts directory: {temp_dir}")

        # Demonstrate using a prompt with tools for embedded reasoning
        import asyncio

        from fluent_mcp.core.llm_client import run_embedded_reasoning

        async def demo_embedded_reasoning_with_tools():
            # Get a prompt with tools
            math_prompt = server.get_prompt("math_tools")
            if math_prompt:
                # Run embedded reasoning with the prompt
                result = await run_embedded_reasoning(
                    system_prompt=math_prompt["template"], user_prompt="What is 5 + 3?", prompt=math_prompt
                )
                logging.info(f"Embedded reasoning result with math tools: {result}")

                # Check if tool calls were made
                if result["tool_calls"]:
                    logging.info(f"Tool calls made: {len(result['tool_calls'])}")
                    for call in result["tool_calls"]:
                        logging.info(f"  Tool: {call['function']['name']}")
                        logging.info(f"  Arguments: {call['function']['arguments']}")

        # Run the async demo function
        asyncio.run(demo_embedded_reasoning_with_tools())


if __name__ == "__main__":
    main()
