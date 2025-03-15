"""
Tests for the prompt loader tool definitions functionality.
"""

import logging
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from fluent_mcp.core.prompt_loader import (
    InvalidFrontmatterError,
    InvalidToolsFormatError,
    MissingRequiredFieldError,
    get_prompt_tools,
    load_prompts,
    parse_markdown_with_frontmatter,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_prompt_tools")


class TestPromptTools(unittest.TestCase):
    """Test cases for the prompt loader tool definitions functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test prompts
        self.test_dir = tempfile.mkdtemp()

        # Create test prompt files with tool definitions
        self.valid_tools_prompt = os.path.join(self.test_dir, "valid_tools.md")
        with open(self.valid_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Valid Tools Prompt
description: A prompt with valid tool definitions
model: gpt-4
temperature: 0.7
tools:
  - tool_1
  - tool_2
---

This is a prompt with valid tool definitions.
"""
            )

        self.empty_tools_prompt = os.path.join(self.test_dir, "empty_tools.md")
        with open(self.empty_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Empty Tools Prompt
description: A prompt with an empty tools list
model: gpt-4
temperature: 0.7
tools: []
---

This prompt has an empty tools list.
"""
            )

        self.no_tools_prompt = os.path.join(self.test_dir, "no_tools.md")
        with open(self.no_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: No Tools Prompt
description: A prompt without tool definitions
model: gpt-4
temperature: 0.7
---

This prompt has no tool definitions.
"""
            )

        self.invalid_tools_format_prompt = os.path.join(self.test_dir, "invalid_tools_format.md")
        with open(self.invalid_tools_format_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Invalid Tools Format
description: A prompt with invalid tools format
model: gpt-4
temperature: 0.7
tools: "not_a_list"
---

This prompt has an invalid tools format (not a list).
"""
            )

        self.invalid_tool_item_prompt = os.path.join(self.test_dir, "invalid_tool_item.md")
        with open(self.invalid_tool_item_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Invalid Tool Item
description: A prompt with an invalid tool item
model: gpt-4
temperature: 0.7
tools:
  - tool_1
  - 42
  - tool_3
---

This prompt has an invalid tool item (not a string).
"""
            )

        self.mixed_tools_prompt = os.path.join(self.test_dir, "mixed_tools.md")
        with open(self.mixed_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Mixed Tools Prompt
description: A prompt with mixed valid and invalid tool references
model: gpt-4
temperature: 0.7
tools:
  - tool_1
  - non_existent_tool
  - tool_2
---

This prompt has mixed valid and invalid tool references.
"""
            )

        self.duplicate_tools_prompt = os.path.join(self.test_dir, "duplicate_tools.md")
        with open(self.duplicate_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Duplicate Tools Prompt
description: A prompt with duplicate tool names
model: gpt-4
temperature: 0.7
tools:
  - tool_1
  - tool_2
  - tool_1
---

This prompt has duplicate tool names.
"""
            )

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    def test_parse_markdown_with_tools(self):
        """Test parsing a markdown file with tool definitions."""
        # Test valid tools prompt
        prompt = parse_markdown_with_frontmatter(self.valid_tools_prompt)
        self.assertEqual(prompt["config"]["name"], "Valid Tools Prompt")
        self.assertEqual(prompt["config"]["description"], "A prompt with valid tool definitions")
        self.assertEqual(prompt["config"]["tools"], ["tool_1", "tool_2"])
        self.assertIn("This is a prompt with valid tool definitions.", prompt["template"])

        # Test empty tools list
        prompt = parse_markdown_with_frontmatter(self.empty_tools_prompt)
        self.assertEqual(prompt["config"]["tools"], [])

        # Test no tools field
        prompt = parse_markdown_with_frontmatter(self.no_tools_prompt)
        self.assertNotIn("tools", prompt["config"])

        # Test invalid tools format (not a list)
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.invalid_tools_format_prompt)

        # Test invalid tool item (not a string)
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.invalid_tool_item_prompt)

    @patch("fluent_mcp.core.tool_registry.get_embedded_tool")
    @patch("fluent_mcp.core.tool_registry.get_tools_as_openai_format")
    def test_get_prompt_tools(self, mock_get_tools, mock_get_embedded_tool):
        """Test getting tools defined in a prompt."""
        # Mock the tool registry functions
        mock_get_tools.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "tool_1",
                    "description": "Tool 1 description",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_2",
                    "description": "Tool 2 description",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_3",
                    "description": "Tool 3 description",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

        # Test with valid tools prompt
        prompt = parse_markdown_with_frontmatter(self.valid_tools_prompt)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["function"]["name"], "tool_1")
        self.assertEqual(tools[1]["function"]["name"], "tool_2")

        # Test with empty tools list
        prompt = parse_markdown_with_frontmatter(self.empty_tools_prompt)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 0)

        # Test with no tools field
        prompt = parse_markdown_with_frontmatter(self.no_tools_prompt)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 0)

        # Test with mixed valid and invalid tool references
        prompt = parse_markdown_with_frontmatter(self.mixed_tools_prompt)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["function"]["name"], "tool_1")
        self.assertEqual(tools[1]["function"]["name"], "tool_2")

        # Test with duplicate tool names (should only include each tool once)
        prompt = parse_markdown_with_frontmatter(self.duplicate_tools_prompt)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 2)
        tool_names = [tool["function"]["name"] for tool in tools]
        self.assertEqual(tool_names.count("tool_1"), 1)
        self.assertEqual(tool_names.count("tool_2"), 1)

    @patch("fluent_mcp.core.llm_client.get_llm_client")
    def test_run_embedded_reasoning_with_prompt_tools(self, mock_get_llm_client):
        """Test running embedded reasoning with tools defined in a prompt."""
        # Mock the LLM client
        mock_client = MagicMock()
        mock_get_llm_client.return_value = mock_client

        # Mock the chat_completion method
        mock_client.chat_completion.return_value = {
            "status": "complete",
            "content": "Test response",
            "tool_calls": [],
            "error": None,
        }

        # Import the function to test
        from fluent_mcp.core.llm_client import run_embedded_reasoning

        # Test with valid tools prompt
        with patch("fluent_mcp.core.prompt_loader.get_prompt_tools") as mock_get_prompt_tools:
            # Mock the get_prompt_tools function
            mock_get_prompt_tools.return_value = [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_1",
                        "description": "Tool 1 description",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "tool_2",
                        "description": "Tool 2 description",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                    },
                },
            ]

            # Run embedded reasoning with a prompt
            prompt = parse_markdown_with_frontmatter(self.valid_tools_prompt)
            result = run_embedded_reasoning(
                system_prompt="System prompt",
                user_prompt="User prompt",
                prompt=prompt,
            )

            # Verify that the client was called with the correct tools
            mock_client.chat_completion.assert_called_once()
            call_args = mock_client.chat_completion.call_args[1]
            self.assertEqual(len(call_args["tools"]), 2)
            self.assertEqual(call_args["tools"][0]["function"]["name"], "tool_1")
            self.assertEqual(call_args["tools"][1]["function"]["name"], "tool_2")

        # Test with no tools prompt
        mock_client.chat_completion.reset_mock()
        with patch("fluent_mcp.core.prompt_loader.get_prompt_tools") as mock_get_prompt_tools:
            # Mock the get_prompt_tools function to return an empty list
            mock_get_prompt_tools.return_value = []

            # Run embedded reasoning with a prompt that has no tools
            prompt = parse_markdown_with_frontmatter(self.no_tools_prompt)
            result = run_embedded_reasoning(
                system_prompt="System prompt",
                user_prompt="User prompt",
                prompt=prompt,
            )

            # Verify that the client was called with an empty tools list
            mock_client.chat_completion.assert_called_once()
            call_args = mock_client.chat_completion.call_args[1]
            self.assertEqual(len(call_args["tools"]), 0)

        # Test with explicit tools parameter (should override prompt tools)
        mock_client.chat_completion.reset_mock()
        with patch("fluent_mcp.core.prompt_loader.get_prompt_tools") as mock_get_prompt_tools:
            # Mock the get_prompt_tools function
            mock_get_prompt_tools.return_value = [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_1",
                        "description": "Tool 1 description",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "tool_2",
                        "description": "Tool 2 description",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                    },
                },
            ]

            # Define explicit tools
            explicit_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "explicit_tool",
                        "description": "Explicit tool description",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                    },
                }
            ]

            # Run embedded reasoning with a prompt and explicit tools
            prompt = parse_markdown_with_frontmatter(self.valid_tools_prompt)
            result = run_embedded_reasoning(
                system_prompt="System prompt",
                user_prompt="User prompt",
                tools=explicit_tools,  # This should override prompt tools
                prompt=prompt,
            )

            # Verify that the client was called with the explicit tools
            mock_client.chat_completion.assert_called_once()
            call_args = mock_client.chat_completion.call_args[1]
            self.assertEqual(len(call_args["tools"]), 1)
            self.assertEqual(call_args["tools"][0]["function"]["name"], "explicit_tool")


if __name__ == "__main__":
    unittest.main()
