"""
Tests for edge cases and error handling in the prompt loader tool definitions functionality.
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
logger = logging.getLogger("test_prompt_tools_edge_cases")


class TestPromptToolsEdgeCases(unittest.TestCase):
    """Test cases for edge cases and error handling in the prompt loader tool definitions functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test prompts
        self.test_dir = tempfile.mkdtemp()

        # Create test prompt files with edge cases
        self.empty_file_prompt = os.path.join(self.test_dir, "empty_file.md")
        with open(self.empty_file_prompt, "w", encoding="utf-8") as f:
            f.write("")

        self.malformed_yaml_prompt = os.path.join(self.test_dir, "malformed_yaml.md")
        with open(self.malformed_yaml_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Malformed YAML
description: A prompt with malformed YAML
tools: [tool_1, tool_2  # Missing closing bracket
---

This prompt has malformed YAML in the frontmatter.
"""
            )

        self.non_string_tool_prompt = os.path.join(self.test_dir, "non_string_tool.md")
        with open(self.non_string_tool_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Non-String Tool
description: A prompt with a non-string tool
tools:
  - tool_1
  - 42
  - true
---

This prompt has non-string tools in the frontmatter.
"""
            )

        self.nested_tools_prompt = os.path.join(self.test_dir, "nested_tools.md")
        with open(self.nested_tools_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Nested Tools
description: A prompt with nested tools
tools:
  - tool_1
  - - nested_tool_1
    - nested_tool_2
---

This prompt has nested tools in the frontmatter.
"""
            )

        self.tools_as_dict_prompt = os.path.join(self.test_dir, "tools_as_dict.md")
        with open(self.tools_as_dict_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Tools as Dict
description: A prompt with tools as a dictionary
tools:
  tool_1: true
  tool_2: false
---

This prompt has tools as a dictionary in the frontmatter.
"""
            )

        self.tools_as_string_prompt = os.path.join(self.test_dir, "tools_as_string.md")
        with open(self.tools_as_string_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Tools as String
description: A prompt with tools as a string
tools: "tool_1,tool_2"
---

This prompt has tools as a string in the frontmatter.
"""
            )

        self.very_long_tools_list_prompt = os.path.join(self.test_dir, "very_long_tools_list.md")
        with open(self.very_long_tools_list_prompt, "w", encoding="utf-8") as f:
            f.write(
                """---
name: Very Long Tools List
description: A prompt with a very long tools list
tools:
  - tool_1
  - tool_2
  - tool_3
  - tool_4
  - tool_5
  - tool_6
  - tool_7
  - tool_8
  - tool_9
  - tool_10
  - tool_11
  - tool_12
  - tool_13
  - tool_14
  - tool_15
  - tool_16
  - tool_17
  - tool_18
  - tool_19
  - tool_20
---

This prompt has a very long tools list in the frontmatter.
"""
            )

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    def test_empty_file(self):
        """Test parsing an empty file."""
        with self.assertRaises(InvalidFrontmatterError):
            parse_markdown_with_frontmatter(self.empty_file_prompt)

    def test_malformed_yaml(self):
        """Test parsing a file with malformed YAML."""
        with self.assertRaises(InvalidFrontmatterError):
            parse_markdown_with_frontmatter(self.malformed_yaml_prompt)

    def test_non_string_tool(self):
        """Test parsing a file with non-string tools."""
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.non_string_tool_prompt)

    def test_nested_tools(self):
        """Test parsing a file with nested tools."""
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.nested_tools_prompt)

    def test_tools_as_dict(self):
        """Test parsing a file with tools as a dictionary."""
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.tools_as_dict_prompt)

    def test_tools_as_string(self):
        """Test parsing a file with tools as a string."""
        with self.assertRaises(InvalidToolsFormatError):
            parse_markdown_with_frontmatter(self.tools_as_string_prompt)

    def test_very_long_tools_list(self):
        """Test parsing a file with a very long tools list."""
        # This should not raise an exception
        prompt = parse_markdown_with_frontmatter(self.very_long_tools_list_prompt)
        self.assertEqual(len(prompt["config"]["tools"]), 20)

    @patch("fluent_mcp.core.tool_registry.get_tools_as_openai_format")
    def test_get_prompt_tools_with_empty_registry(self, mock_get_tools):
        """Test get_prompt_tools with an empty tool registry."""
        # Mock an empty tool registry
        mock_get_tools.return_value = []

        # Create a prompt with tools
        prompt = {
            "config": {
                "name": "Test Prompt",
                "description": "A test prompt",
                "tools": ["tool_1", "tool_2"],
            },
            "template": "Test template",
        }

        # Get tools for the prompt (should return an empty list)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 0)

    @patch("fluent_mcp.core.tool_registry.get_tools_as_openai_format")
    def test_get_prompt_tools_with_partial_registry(self, mock_get_tools):
        """Test get_prompt_tools with a partial tool registry."""
        # Mock a partial tool registry
        mock_get_tools.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "tool_1",
                    "description": "Tool 1 description",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            # tool_2 is missing
            {
                "type": "function",
                "function": {
                    "name": "tool_3",
                    "description": "Tool 3 description",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

        # Create a prompt with tools
        prompt = {
            "config": {
                "name": "Test Prompt",
                "description": "A test prompt",
                "tools": ["tool_1", "tool_2", "tool_3"],
            },
            "template": "Test template",
        }

        # Get tools for the prompt (should return only tool_1 and tool_3)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 2)
        tool_names = [tool["function"]["name"] for tool in tools]
        self.assertIn("tool_1", tool_names)
        self.assertIn("tool_3", tool_names)
        self.assertNotIn("tool_2", tool_names)

    @patch("fluent_mcp.core.llm_client.get_llm_client")
    def test_run_embedded_reasoning_with_no_client(self, mock_get_llm_client):
        """Test run_embedded_reasoning when no LLM client is configured."""
        from fluent_mcp.core.llm_client import LLMClientNotConfiguredError, run_embedded_reasoning

        # Mock get_llm_client to raise LLMClientNotConfiguredError
        mock_get_llm_client.side_effect = LLMClientNotConfiguredError("LLM client not configured")

        # Create a prompt with tools
        prompt = {
            "config": {
                "name": "Test Prompt",
                "description": "A test prompt",
                "tools": ["tool_1", "tool_2"],
            },
            "template": "Test template",
        }

        # Run embedded reasoning (should handle the error gracefully)
        result = run_embedded_reasoning(
            system_prompt="System prompt",
            user_prompt="User prompt",
            prompt=prompt,
        )

        # Verify that the result contains an error
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "LLM client not configured")
        self.assertEqual(result["content"], "")
        self.assertEqual(result["tool_calls"], [])

    @patch("fluent_mcp.core.tool_registry.get_tools_as_openai_format")
    def test_get_prompt_tools_with_duplicate_tools(self, mock_get_tools):
        """Test get_prompt_tools with duplicate tools in the prompt."""
        # Mock the tool registry
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
        ]

        # Create a prompt with duplicate tools
        prompt = {
            "config": {
                "name": "Test Prompt",
                "description": "A test prompt",
                "tools": ["tool_1", "tool_2", "tool_1", "tool_2"],
            },
            "template": "Test template",
        }

        # Get tools for the prompt (should return each tool only once)
        tools = get_prompt_tools(prompt)
        self.assertEqual(len(tools), 2)
        tool_names = [tool["function"]["name"] for tool in tools]
        self.assertEqual(tool_names.count("tool_1"), 1)
        self.assertEqual(tool_names.count("tool_2"), 1)


if __name__ == "__main__":
    unittest.main()
