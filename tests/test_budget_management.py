"""
Tests for the budget management functionality.
"""

import asyncio
import logging
import time
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from fluent_mcp.core.budget import BudgetExceededError, BudgetManager
from fluent_mcp.core.budget_tools import check_tool_budget, get_budget_status
from fluent_mcp.core.prompt_loader import InvalidBudgetFormatError, parse_markdown_with_frontmatter
from fluent_mcp.core.server import Server
from fluent_mcp.core.tool_execution import execute_embedded_tool, execute_external_tool
from fluent_mcp.core.tool_registry import register_embedded_tool, register_external_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_budget_management")


# Define some test tools
@register_embedded_tool()
def test_embedded_tool(param1: str, param2: int = 0) -> Dict[str, Any]:
    """A test embedded tool."""
    return {"param1": param1, "param2": param2, "type": "embedded"}


@register_external_tool()
def test_external_tool(param1: str, param2: int = 0) -> Dict[str, Any]:
    """A test external tool."""
    return {"param1": param1, "param2": param2, "type": "external"}


class TestBudgetManager(unittest.TestCase):
    """Test cases for the budget manager functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a budget manager with default limits
        self.budget_manager = BudgetManager(
            {
                "test_embedded_tool": {"hourly_limit": 5, "daily_limit": 10},
                "test_external_tool": {"hourly_limit": 3, "daily_limit": 6},
            }
        )

        # Set custom limits for a prompt
        self.budget_manager.set_custom_limits(
            "test_prompt", {"test_embedded_tool": {"hourly_limit": 2, "daily_limit": 4}}
        )

    def test_get_tool_limits(self):
        """Test getting tool limits."""
        # Test default limits
        hourly_limit, daily_limit = self.budget_manager.get_tool_limits("test_embedded_tool")
        self.assertEqual(hourly_limit, 5)
        self.assertEqual(daily_limit, 10)

        # Test custom limits from prompt
        hourly_limit, daily_limit = self.budget_manager.get_tool_limits("test_embedded_tool", "test_prompt")
        self.assertEqual(hourly_limit, 2)
        self.assertEqual(daily_limit, 4)

        # Test global default limits for unknown tool
        hourly_limit, daily_limit = self.budget_manager.get_tool_limits("unknown_tool")
        self.assertEqual(hourly_limit, 100)
        self.assertEqual(daily_limit, 1000)

    def test_check_and_update_budget(self):
        """Test checking and updating budget."""
        # Test successful budget check
        result = self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")
        self.assertTrue(result)

        # Get usage
        hour_timestamp = self.budget_manager._get_current_hour_timestamp()
        day_timestamp = self.budget_manager._get_current_day_timestamp()
        hourly_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "hourly", hour_timestamp)
        daily_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "daily", day_timestamp)

        # Check that usage was incremented
        self.assertEqual(hourly_usage, 1)
        self.assertEqual(daily_usage, 1)

        # Test budget exceeded
        for _ in range(4):  # Call 4 more times to reach the limit of 5
            self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")

        # Next call should exceed the budget
        with self.assertRaises(BudgetExceededError) as context:
            self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")

        # Check error details
        self.assertEqual(context.exception.tool_name, "test_embedded_tool")
        self.assertEqual(context.exception.limit_type, "hourly")
        self.assertEqual(context.exception.current_usage, 5)
        self.assertEqual(context.exception.limit, 5)

    def test_check_and_update_budget_with_prompt(self):
        """Test checking and updating budget with prompt-specific limits."""
        # Test with prompt-specific limits
        result = self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool", "test_prompt")
        self.assertTrue(result)

        # Call one more time to reach the prompt-specific limit of 2
        self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool", "test_prompt")

        # Next call should exceed the budget
        with self.assertRaises(BudgetExceededError) as context:
            self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool", "test_prompt")

        # Check error details
        self.assertEqual(context.exception.tool_name, "test_embedded_tool")
        self.assertEqual(context.exception.limit_type, "hourly")
        self.assertEqual(context.exception.current_usage, 2)
        self.assertEqual(context.exception.limit, 2)

    def test_get_remaining_budget(self):
        """Test getting remaining budget."""
        # Make some tool calls
        self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")
        self.budget_manager.check_and_update_budget("test_project", "test_external_tool")

        # Get remaining budget for a specific tool
        budget_info = self.budget_manager.get_remaining_budget("test_project", "test_embedded_tool")

        # Check budget info structure
        self.assertEqual(budget_info["project_id"], "test_project")
        self.assertIn("timestamp", budget_info)
        self.assertIn("tools", budget_info)
        self.assertIn("test_embedded_tool", budget_info["tools"])

        # Check tool budget details
        tool_budget = budget_info["tools"]["test_embedded_tool"]
        self.assertIn("hourly", tool_budget)
        self.assertIn("daily", tool_budget)
        self.assertEqual(tool_budget["hourly"]["usage"], 1)
        self.assertEqual(tool_budget["hourly"]["limit"], 5)
        self.assertEqual(tool_budget["hourly"]["remaining"], 4)
        self.assertEqual(tool_budget["daily"]["usage"], 1)
        self.assertEqual(tool_budget["daily"]["limit"], 10)
        self.assertEqual(tool_budget["daily"]["remaining"], 9)

        # Get remaining budget for all tools
        all_budget_info = self.budget_manager.get_remaining_budget("test_project")
        self.assertIn("test_embedded_tool", all_budget_info["tools"])
        self.assertIn("test_external_tool", all_budget_info["tools"])

    def test_cleanup_old_usage_data(self):
        """Test cleaning up old usage data."""
        # Add some usage data
        self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")

        # Manually add some old data
        hour_timestamp = self.budget_manager._get_current_hour_timestamp() - (3 * 86400)  # 3 days ago
        day_timestamp = self.budget_manager._get_current_day_timestamp() - (3 * 86400)  # 3 days ago
        self.budget_manager._increment_usage("test_project", "test_embedded_tool", "hourly", hour_timestamp)
        self.budget_manager._increment_usage("test_project", "test_embedded_tool", "daily", day_timestamp)

        # Clean up old data
        self.budget_manager.cleanup_old_usage_data()

        # Check that old data was removed
        hourly_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "hourly", hour_timestamp)
        daily_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "daily", day_timestamp)
        self.assertEqual(hourly_usage, 0)
        self.assertEqual(daily_usage, 0)

        # Check that current data was preserved
        current_hour = self.budget_manager._get_current_hour_timestamp()
        current_day = self.budget_manager._get_current_day_timestamp()
        hourly_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "hourly", current_hour)
        daily_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "daily", current_day)
        self.assertEqual(hourly_usage, 1)
        self.assertEqual(daily_usage, 1)


class TestPromptLoaderBudget(unittest.TestCase):
    """Test cases for the prompt loader budget functionality."""

    def test_parse_markdown_with_budget(self):
        """Test parsing a markdown file with budget configuration."""
        import os
        import tempfile

        # Create a temporary markdown file with budget configuration
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(
                """---
name: Test Prompt
description: A test prompt with budget configuration
tools:
  - test_embedded_tool
  - test_external_tool
budget:
  test_embedded_tool:
    hourly_limit: 5
    daily_limit: 10
  test_external_tool:
    hourly_limit: 3
    daily_limit: 6
---

This is a test prompt with budget configuration.
""".encode(
                    "utf-8"
                )
            )
            temp_file = f.name

        try:
            # Parse the markdown file
            prompt = parse_markdown_with_frontmatter(temp_file)

            # Check that budget configuration was parsed correctly
            self.assertIn("budget", prompt["config"])
            self.assertIn("test_embedded_tool", prompt["config"]["budget"])
            self.assertIn("test_external_tool", prompt["config"]["budget"])
            self.assertEqual(prompt["config"]["budget"]["test_embedded_tool"]["hourly_limit"], 5)
            self.assertEqual(prompt["config"]["budget"]["test_embedded_tool"]["daily_limit"], 10)
            self.assertEqual(prompt["config"]["budget"]["test_external_tool"]["hourly_limit"], 3)
            self.assertEqual(prompt["config"]["budget"]["test_external_tool"]["daily_limit"], 6)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)

    def test_invalid_budget_format(self):
        """Test parsing a markdown file with invalid budget configuration."""
        import os
        import tempfile

        # Create a temporary markdown file with invalid budget configuration
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(
                """---
name: Test Prompt
description: A test prompt with invalid budget configuration
budget: not_a_dictionary
---

This is a test prompt with invalid budget configuration.
""".encode(
                    "utf-8"
                )
            )
            temp_file = f.name

        try:
            # Parse the markdown file
            with self.assertRaises(InvalidBudgetFormatError):
                parse_markdown_with_frontmatter(temp_file)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)

    def test_invalid_budget_tool_format(self):
        """Test parsing a markdown file with invalid budget tool configuration."""
        import os
        import tempfile

        # Create a temporary markdown file with invalid budget tool configuration
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(
                """---
name: Test Prompt
description: A test prompt with invalid budget tool configuration
budget:
  test_embedded_tool: not_a_dictionary
---

This is a test prompt with invalid budget tool configuration.
""".encode(
                    "utf-8"
                )
            )
            temp_file = f.name

        try:
            # Parse the markdown file
            with self.assertRaises(InvalidBudgetFormatError):
                parse_markdown_with_frontmatter(temp_file)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)

    def test_invalid_budget_limit_format(self):
        """Test parsing a markdown file with invalid budget limit configuration."""
        import os
        import tempfile

        # Create a temporary markdown file with invalid budget limit configuration
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(
                """---
name: Test Prompt
description: A test prompt with invalid budget limit configuration
budget:
  test_embedded_tool:
    hourly_limit: -5
    daily_limit: not_a_number
---

This is a test prompt with invalid budget limit configuration.
""".encode(
                    "utf-8"
                )
            )
            temp_file = f.name

        try:
            # Parse the markdown file
            with self.assertRaises(InvalidBudgetFormatError):
                parse_markdown_with_frontmatter(temp_file)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)


class TestToolExecution(unittest.TestCase):
    """Test cases for the tool execution functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock server with budget manager
        self.server = MagicMock(spec=Server)
        self.budget_manager = BudgetManager(
            {
                "test_embedded_tool": {"hourly_limit": 5, "daily_limit": 10},
                "test_external_tool": {"hourly_limit": 3, "daily_limit": 6},
            }
        )
        self.server.budget_manager = self.budget_manager
        self.server.name = "test_server"

        # Patch get_current_server to return our mock server
        self.get_current_server_patcher = patch("fluent_mcp.core.server.get_current_server", return_value=self.server)
        self.mock_get_current_server = self.get_current_server_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.get_current_server_patcher.stop()

    def test_execute_embedded_tool(self):
        """Test executing an embedded tool with budget enforcement."""
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Execute the tool
            result = loop.run_until_complete(
                execute_embedded_tool("test_embedded_tool", {"param1": "test", "param2": 42}, "test_project")
            )

            # Check the result
            self.assertEqual(result["param1"], "test")
            self.assertEqual(result["param2"], 42)
            self.assertEqual(result["type"], "embedded")

            # Check that budget was updated
            hour_timestamp = self.budget_manager._get_current_hour_timestamp()
            day_timestamp = self.budget_manager._get_current_day_timestamp()
            hourly_usage = self.budget_manager._get_usage(
                "test_project", "test_embedded_tool", "hourly", hour_timestamp
            )
            daily_usage = self.budget_manager._get_usage("test_project", "test_embedded_tool", "daily", day_timestamp)
            self.assertEqual(hourly_usage, 1)
            self.assertEqual(daily_usage, 1)

            # Execute the tool until budget is exceeded
            for _ in range(4):  # Call 4 more times to reach the limit of 5
                loop.run_until_complete(
                    execute_embedded_tool("test_embedded_tool", {"param1": "test", "param2": 42}, "test_project")
                )

            # Next call should return a budget exceeded error
            result = loop.run_until_complete(
                execute_embedded_tool("test_embedded_tool", {"param1": "test", "param2": 42}, "test_project")
            )
            self.assertEqual(result["error"], "budget_exceeded")
            self.assertIn("Budget exceeded", result["message"])
        finally:
            loop.close()

    def test_execute_external_tool(self):
        """Test executing an external tool with budget enforcement."""
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Execute the tool
            result = loop.run_until_complete(
                execute_external_tool("test_external_tool", {"param1": "test", "param2": 42}, "test_project")
            )

            # Check the result
            self.assertEqual(result["param1"], "test")
            self.assertEqual(result["param2"], 42)
            self.assertEqual(result["type"], "external")

            # Check that budget was updated
            hour_timestamp = self.budget_manager._get_current_hour_timestamp()
            day_timestamp = self.budget_manager._get_current_day_timestamp()
            hourly_usage = self.budget_manager._get_usage(
                "test_project", "test_external_tool", "hourly", hour_timestamp
            )
            daily_usage = self.budget_manager._get_usage("test_project", "test_external_tool", "daily", day_timestamp)
            self.assertEqual(hourly_usage, 1)
            self.assertEqual(daily_usage, 1)

            # Execute the tool until budget is exceeded
            for _ in range(2):  # Call 2 more times to reach the limit of 3
                loop.run_until_complete(
                    execute_external_tool("test_external_tool", {"param1": "test", "param2": 42}, "test_project")
                )

            # Next call should return a budget exceeded error
            result = loop.run_until_complete(
                execute_external_tool("test_external_tool", {"param1": "test", "param2": 42}, "test_project")
            )
            self.assertEqual(result["error"], "budget_exceeded")
            self.assertIn("Budget exceeded", result["message"])
        finally:
            loop.close()


class TestBudgetTools(unittest.TestCase):
    """Test cases for the budget tools functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock server with budget manager
        self.server = MagicMock(spec=Server)
        self.budget_manager = BudgetManager(
            {
                "test_embedded_tool": {"hourly_limit": 5, "daily_limit": 10},
                "test_external_tool": {"hourly_limit": 3, "daily_limit": 6},
            }
        )
        self.server.budget_manager = self.budget_manager
        self.server.name = "test_server"

        # Patch get_current_server to return our mock server
        self.get_current_server_patcher = patch("fluent_mcp.core.server.get_current_server", return_value=self.server)
        self.mock_get_current_server = self.get_current_server_patcher.start()

        # Make some tool calls to have usage data
        self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")
        self.budget_manager.check_and_update_budget("test_project", "test_external_tool")

    def tearDown(self):
        """Clean up after tests."""
        self.get_current_server_patcher.stop()

    def test_get_budget_status(self):
        """Test the get_budget_status tool."""
        # Get budget status for a specific tool
        result = get_budget_status(project_id="test_project", tool_name="test_embedded_tool")

        # Check the result
        self.assertEqual(result["project_id"], "test_project")
        self.assertIn("timestamp", result)
        self.assertIn("tools", result)
        self.assertIn("test_embedded_tool", result["tools"])
        self.assertEqual(result["tools"]["test_embedded_tool"]["hourly"]["usage"], 1)
        self.assertEqual(result["tools"]["test_embedded_tool"]["hourly"]["limit"], 5)
        self.assertEqual(result["tools"]["test_embedded_tool"]["hourly"]["remaining"], 4)

        # Get budget status for all tools
        result = get_budget_status(project_id="test_project")
        self.assertIn("test_embedded_tool", result["tools"])
        self.assertIn("test_external_tool", result["tools"])

    def test_check_tool_budget(self):
        """Test the check_tool_budget tool."""
        # Check budget for a specific tool
        result = check_tool_budget(project_id="test_project", tool_name="test_embedded_tool")

        # Check the result
        self.assertEqual(result["tool_name"], "test_embedded_tool")
        self.assertIn("hourly", result)
        self.assertIn("daily", result)
        self.assertEqual(result["hourly"]["remaining"], 4)
        self.assertEqual(result["hourly"]["limit"], 5)
        self.assertIn("reset_at", result["hourly"])
        self.assertEqual(result["daily"]["remaining"], 9)
        self.assertEqual(result["daily"]["limit"], 10)
        self.assertIn("reset_at", result["daily"])
        self.assertEqual(result["status"], "ok")

        # Check budget for a tool with low remaining budget
        # First, make more calls to reduce the budget
        for _ in range(3):
            self.budget_manager.check_and_update_budget("test_project", "test_embedded_tool")

        # Now check the budget again
        result = check_tool_budget(project_id="test_project", tool_name="test_embedded_tool")
        self.assertEqual(result["hourly"]["remaining"], 1)
        self.assertEqual(result["status"], "warning")
        self.assertIn("warning", result)
        self.assertIn("Hourly budget is low", result["warning"])

        # Check budget for an unknown tool
        result = check_tool_budget(project_id="test_project", tool_name="unknown_tool")
        self.assertEqual(result["tool_name"], "unknown_tool")
        self.assertEqual(result["status"], "unknown")
        self.assertIn("message", result)
        self.assertIn("No budget information available", result["message"])


if __name__ == "__main__":
    unittest.main()
