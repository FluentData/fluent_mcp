"""
Tests for the reflection system functionality.
"""

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fluent_mcp.core.reflection import ReflectionLoop
from fluent_mcp.core.reflection_loader import ReflectionLoader


class TestReflectionLoader(unittest.TestCase):
    """Test cases for the reflection loader functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock templates directory
        self.templates_dir = os.path.join(
            os.path.dirname(__file__), "..", "fluent_mcp", "core", "templates", "reflection"
        )
        self.reflection_loader = ReflectionLoader(templates_dir=self.templates_dir)

    def test_load_templates(self):
        """Test loading templates."""
        # Reload templates to ensure they're loaded
        self.reflection_loader.load_templates()

        # Check that base templates are loaded
        self.assertIn("base_reflection", self.reflection_loader.base_templates)
        self.assertIn("tool_use", self.reflection_loader.base_templates)

        # Check that custom template is loaded
        self.assertIn("custom_reflection", self.reflection_loader.custom_templates)

        # Check that tool templates are loaded
        self.assertTrue(len(self.reflection_loader.tool_templates) > 0)

        # Check specific tool templates
        tool_template_names = [
            template["config"]["name"] for template in self.reflection_loader.tool_templates.values()
        ]
        self.assertIn("database_reflection", tool_template_names)
        self.assertIn("file_operations_reflection", tool_template_names)

    def test_get_reflection_template(self):
        """Test getting reflection templates."""
        # Test getting base reflection template
        base_template = self.reflection_loader.get_reflection_template()
        self.assertIsNotNone(base_template)
        self.assertIn("content", base_template)
        self.assertIn("config", base_template)

        # Test getting tool-specific reflection template
        tool_template = self.reflection_loader.get_reflection_template("query_database")
        self.assertIsNotNone(tool_template)
        self.assertIn("content", tool_template)
        self.assertIn("config", tool_template)

        # Test that tool-specific content is included
        self.assertIn("Database Operations Reflection", tool_template["content"])

    def test_format_reflection_template(self):
        """Test formatting reflection templates."""
        template = {
            "content": "Previous reasoning: {{previous_reasoning}}\nTool calls: {{tool_calls}}",
            "config": {"name": "test_template"},
        }

        variables = {"previous_reasoning": "This is the previous reasoning.", "tool_calls": "These are the tool calls."}

        formatted = self.reflection_loader.format_reflection_template(template, variables)
        self.assertEqual(
            formatted, "Previous reasoning: This is the previous reasoning.\nTool calls: These are the tool calls."
        )

    def test_get_applicable_tool_templates(self):
        """Test getting applicable tool templates."""
        # Ensure templates are loaded
        self.reflection_loader.load_templates()

        # Test with database tools
        database_tools = ["query_database", "update_database"]
        applicable_templates = self.reflection_loader.get_applicable_tool_templates(database_tools)
        self.assertTrue(len(applicable_templates) > 0)
        self.assertIn("database_reflection", applicable_templates)

        # Test with file operation tools
        file_tools = ["read_file", "write_file"]
        applicable_templates = self.reflection_loader.get_applicable_tool_templates(file_tools)
        self.assertTrue(len(applicable_templates) > 0)
        self.assertIn("file_operations_reflection", applicable_templates)

        # Test with mixed tools
        mixed_tools = ["query_database", "read_file"]
        applicable_templates = self.reflection_loader.get_applicable_tool_templates(mixed_tools)
        self.assertTrue(len(applicable_templates) > 0)
        self.assertIn("database_reflection", applicable_templates)
        self.assertIn("file_operations_reflection", applicable_templates)


class TestReflectionLoop(unittest.IsolatedAsyncioTestCase):
    """Test cases for the reflection loop functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock reflection loader
        self.reflection_loader = MagicMock(spec=ReflectionLoader)

        # Set up mock templates
        self.reflection_loader.get_reflection_template.return_value = {
            "content": "Reflection template content",
            "config": {"name": "test_template"},
        }

        self.reflection_loader.format_reflection_template.return_value = "Formatted reflection template"

        # Create a reflection loop with the mock loader
        self.reflection_loop = ReflectionLoop(reflection_loader=self.reflection_loader)

        # Set up mock LLM client
        self.llm_client = MagicMock()
        self.llm_client.generate = AsyncMock()
        self.llm_client.generate.return_value = {"status": "complete", "content": "Reflection result", "tool_calls": []}

    async def test_run_reflection(self):
        """Test running the reflection loop."""
        # Set up test data
        previous_reasoning = "Previous reasoning content"
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "query_database", "arguments": {"query": "SELECT * FROM users"}},
            }
        ]
        tool_results = [
            {
                "tool_call_id": "call_1",
                "function_name": "query_database",
                "arguments": {"query": "SELECT * FROM users"},
                "result": [{"id": 1, "name": "User 1"}],
            }
        ]
        system_prompt = "System prompt"
        user_prompt = "User prompt"

        # Mock the internal methods
        self.reflection_loop._run_reflection_with_llm = AsyncMock()
        self.reflection_loop._run_reflection_with_llm.return_value = {
            "status": "complete",
            "content": "Improved reasoning",
            "tool_calls": [],
        }

        self.reflection_loop._execute_reflection_tool_calls = AsyncMock()
        self.reflection_loop._execute_reflection_tool_calls.return_value = []

        # Run the reflection loop
        result = await self.reflection_loop.run_reflection(
            previous_reasoning=previous_reasoning,
            tool_calls=tool_calls,
            tool_results=tool_results,
            llm_client=self.llm_client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_iterations=2,
        )

        # Check the result
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["content"], "Improved reasoning")
        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(result["iterations"], 1)
        self.assertTrue("reflection_history" in result)

        # Check that the internal methods were called correctly
        self.reflection_loader.get_reflection_template.assert_called_once()
        self.reflection_loader.format_reflection_template.assert_called_once()
        self.reflection_loop._run_reflection_with_llm.assert_called_once()

    def test_format_tool_calls(self):
        """Test formatting tool calls."""
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "query_database", "arguments": {"query": "SELECT * FROM users"}},
            },
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "update_database",
                    "arguments": {"query": "UPDATE users SET name = 'New Name' WHERE id = 1"},
                },
            },
        ]

        formatted = self.reflection_loop._format_tool_calls(tool_calls)
        self.assertIn("Tool Call 1:", formatted)
        self.assertIn("Function: query_database", formatted)
        self.assertIn("Tool Call 2:", formatted)
        self.assertIn("Function: update_database", formatted)

    def test_format_tool_results(self):
        """Test formatting tool results."""
        tool_results = [
            {
                "tool_call_id": "call_1",
                "function_name": "query_database",
                "arguments": {"query": "SELECT * FROM users"},
                "result": [{"id": 1, "name": "User 1"}],
            },
            {
                "tool_call_id": "call_2",
                "function_name": "update_database",
                "arguments": {"query": "UPDATE users SET name = 'New Name' WHERE id = 1"},
                "result": {"affected_rows": 1},
            },
        ]

        formatted = self.reflection_loop._format_tool_results(tool_results)
        self.assertIn("Tool Result 1:", formatted)
        self.assertIn("Function: query_database", formatted)
        self.assertIn("Tool Result 2:", formatted)
        self.assertIn("Function: update_database", formatted)
