"""
Integration tests for the prompt loader tool definitions functionality.
"""

import asyncio
import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from fluent_mcp.core.llm_client import run_embedded_reasoning
from fluent_mcp.core.prompt_loader import get_prompt_tools, load_prompts
from fluent_mcp.core.server import MCPServer
from fluent_mcp.core.tool_registry import embedded_tool, register_embedded_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_prompt_tools_integration")


# Define some test tools for the integration tests
@embedded_tool
def test_add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@embedded_tool
def test_multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


@embedded_tool
def test_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"The weather in {location} is sunny and 72 degrees."


class TestPromptToolsIntegration(unittest.TestCase):
    """Integration test cases for the prompt loader tool definitions functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test prompts
        self.test_dir = tempfile.mkdtemp()

        # Create test prompt files with tool definitions
        self.math_tools_prompt = os.path.join(self.test_dir, "math_tools.md")
        with open(self.math_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: math_tools
description: A prompt that uses math-related tools
model: gpt-4
temperature: 0.3
tools:
  - test_add
  - test_multiply
---
You are a math assistant that can perform calculations.
Use the available tools to help solve math problems.
"""
            )

        self.weather_tools_prompt = os.path.join(self.test_dir, "weather_tools.md")
        with open(self.weather_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: weather_tools
description: A prompt that uses weather-related tools
model: gpt-4
temperature: 0.3
tools:
  - test_weather
---
You are a weather assistant that can provide weather information.
Use the available tools to help answer weather-related questions.
"""
            )

        self.multi_tools_prompt = os.path.join(self.test_dir, "multi_tools.md")
        with open(self.multi_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: multi_tools
description: A prompt that uses multiple tools
model: gpt-4
temperature: 0.3
tools:
  - test_add
  - test_multiply
  - test_weather
---
You are a versatile assistant that can perform calculations and provide weather information.
Use the available tools to help answer the user's questions.
"""
            )

        self.non_existent_tools_prompt = os.path.join(self.test_dir, "non_existent_tools.md")
        with open(self.non_existent_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: non_existent_tools
description: A prompt that references non-existent tools
model: gpt-4
temperature: 0.3
tools:
  - non_existent_tool_1
  - non_existent_tool_2
---
You are an assistant that tries to use non-existent tools.
"""
            )

        # Load prompts and create server
        self.prompts = load_prompts(self.test_dir)
        self.server = MCPServer(prompts=self.prompts)

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    def test_server_loads_prompts_with_tools(self):
        """Test that the server correctly loads prompts with tool definitions."""
        # Check that all prompts were loaded
        self.assertEqual(len(self.prompts), 4)

        # Check that we can retrieve prompts by name
        math_prompt = self.server.get_prompt("math_tools")
        self.assertIsNotNone(math_prompt)
        self.assertEqual(math_prompt["config"]["name"], "math_tools")
        self.assertEqual(math_prompt["config"]["tools"], ["test_add", "test_multiply"])

        weather_prompt = self.server.get_prompt("weather_tools")
        self.assertIsNotNone(weather_prompt)
        self.assertEqual(weather_prompt["config"]["name"], "weather_tools")
        self.assertEqual(weather_prompt["config"]["tools"], ["test_weather"])

        multi_prompt = self.server.get_prompt("multi_tools")
        self.assertIsNotNone(multi_prompt)
        self.assertEqual(multi_prompt["config"]["name"], "multi_tools")
        self.assertEqual(multi_prompt["config"]["tools"], ["test_add", "test_multiply", "test_weather"])

        non_existent_prompt = self.server.get_prompt("non_existent_tools")
        self.assertIsNotNone(non_existent_prompt)
        self.assertEqual(non_existent_prompt["config"]["name"], "non_existent_tools")
        self.assertEqual(non_existent_prompt["config"]["tools"], ["non_existent_tool_1", "non_existent_tool_2"])

    def test_get_prompt_tools_integration(self):
        """Test that get_prompt_tools correctly retrieves tools for prompts."""
        # Get tools for math prompt
        math_prompt = self.server.get_prompt("math_tools")
        math_tools = get_prompt_tools(math_prompt)
        self.assertEqual(len(math_tools), 2)
        math_tool_names = [tool["function"]["name"] for tool in math_tools]
        self.assertIn("test_add", math_tool_names)
        self.assertIn("test_multiply", math_tool_names)

        # Get tools for weather prompt
        weather_prompt = self.server.get_prompt("weather_tools")
        weather_tools = get_prompt_tools(weather_prompt)
        self.assertEqual(len(weather_tools), 1)
        self.assertEqual(weather_tools[0]["function"]["name"], "test_weather")

        # Get tools for multi prompt
        multi_prompt = self.server.get_prompt("multi_tools")
        multi_tools = get_prompt_tools(multi_prompt)
        self.assertEqual(len(multi_tools), 3)
        multi_tool_names = [tool["function"]["name"] for tool in multi_tools]
        self.assertIn("test_add", multi_tool_names)
        self.assertIn("test_multiply", multi_tool_names)
        self.assertIn("test_weather", multi_tool_names)

        # Get tools for non-existent tools prompt (should return empty list)
        non_existent_prompt = self.server.get_prompt("non_existent_tools")
        non_existent_tools = get_prompt_tools(non_existent_prompt)
        self.assertEqual(len(non_existent_tools), 0)

    @patch("fluent_mcp.core.llm_client.get_llm_client")
    def test_run_embedded_reasoning_integration(self, mock_get_llm_client):
        """Test running embedded reasoning with tools defined in prompts."""
        # Mock the LLM client
        mock_client = MagicMock()
        mock_get_llm_client.return_value = mock_client

        # Set up the mock to simulate tool calls
        def mock_chat_completion(messages, tools, **kwargs):
            # Check which tools are available and make appropriate tool calls
            tool_names = [tool["function"]["name"] for tool in tools]

            if "test_add" in tool_names and "test_multiply" in tool_names:
                # Math tools available
                return {
                    "status": "complete",
                    "content": "I'll calculate that for you.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "test_add",
                                "arguments": {"a": 5, "b": 3},
                            },
                        }
                    ],
                    "error": None,
                }
            elif "test_weather" in tool_names:
                # Weather tool available
                return {
                    "status": "complete",
                    "content": "Let me check the weather for you.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "test_weather",
                                "arguments": {"location": "Seattle"},
                            },
                        }
                    ],
                    "error": None,
                }
            else:
                # No relevant tools available
                return {
                    "status": "complete",
                    "content": "I don't have the tools to help with that.",
                    "tool_calls": [],
                    "error": None,
                }

        mock_client.chat_completion.side_effect = mock_chat_completion

        # Test with math tools prompt
        math_prompt = self.server.get_prompt("math_tools")
        math_result = run_embedded_reasoning(
            system_prompt=math_prompt["template"],
            user_prompt="What is 5 + 3?",
            prompt=math_prompt,
        )

        # Verify that the math tool was called
        self.assertEqual(math_result["content"], "I'll calculate that for you.")
        self.assertEqual(len(math_result["tool_calls"]), 1)
        self.assertEqual(math_result["tool_calls"][0]["function"]["name"], "test_add")

        # Test with weather tools prompt
        weather_prompt = self.server.get_prompt("weather_tools")
        weather_result = run_embedded_reasoning(
            system_prompt=weather_prompt["template"],
            user_prompt="What's the weather in Seattle?",
            prompt=weather_prompt,
        )

        # Verify that the weather tool was called
        self.assertEqual(weather_result["content"], "Let me check the weather for you.")
        self.assertEqual(len(weather_result["tool_calls"]), 1)
        self.assertEqual(weather_result["tool_calls"][0]["function"]["name"], "test_weather")

        # Test with non-existent tools prompt
        non_existent_prompt = self.server.get_prompt("non_existent_tools")
        non_existent_result = run_embedded_reasoning(
            system_prompt=non_existent_prompt["template"],
            user_prompt="Can you help me?",
            prompt=non_existent_prompt,
        )

        # Verify that no tools were called
        self.assertEqual(non_existent_result["content"], "I don't have the tools to help with that.")
        self.assertEqual(len(non_existent_result["tool_calls"]), 0)


if __name__ == "__main__":
    unittest.main()
