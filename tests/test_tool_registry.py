"""
Tests for the tool registry module.
"""

import logging
import unittest
from typing import Any, Dict, List

from fluent_mcp.core.tool_registry import (
    _embedded_tools,
    get_embedded_tool,
    get_tools_as_openai_format,
    list_embedded_tools,
    register_embedded_tool,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_tool_registry")


# Define some test tools
@register_embedded_tool()
def test_tool_1(param1: str, param2: int = 42) -> str:
    """A test tool that concatenates a string and an integer."""
    return f"{param1} {param2}"


@register_embedded_tool(name="custom_name_tool")
def test_tool_2(items: List[str], flag: bool = False) -> Dict[str, Any]:
    """A test tool that processes a list of items."""
    return {"items": items, "count": len(items), "flag": flag}


class TestToolRegistry(unittest.TestCase):
    """Test cases for the tool registry module."""

    def setUp(self):
        """Set up test environment."""
        # Clear the registry before each test
        _embedded_tools.clear()

        # Re-register the test tools
        global test_tool_1, test_tool_2
        test_tool_1 = register_embedded_tool()(test_tool_1)
        test_tool_2 = register_embedded_tool(name="custom_name_tool")(test_tool_2)

    def test_register_embedded_tool(self):
        """Test registering an embedded tool."""
        # Check that the tools were registered
        self.assertIn("test_tool_1", _embedded_tools)
        self.assertIn("custom_name_tool", _embedded_tools)

        # Check that the functions are preserved
        self.assertEqual(test_tool_1("hello", 123), "hello 123")

        result = test_tool_2(["a", "b", "c"], True)
        self.assertEqual(result["count"], 3)
        self.assertTrue(result["flag"])

    def test_get_embedded_tool(self):
        """Test getting an embedded tool."""
        tool = get_embedded_tool("test_tool_1")
        self.assertIsNotNone(tool)
        self.assertEqual(tool("hello", 123), "hello 123")

        tool = get_embedded_tool("custom_name_tool")
        self.assertIsNotNone(tool)

        # Test getting a non-existent tool
        tool = get_embedded_tool("non_existent_tool")
        self.assertIsNone(tool)

    def test_list_embedded_tools(self):
        """Test listing embedded tools."""
        tools = list_embedded_tools()
        self.assertIn("test_tool_1", tools)
        self.assertIn("custom_name_tool", tools)
        self.assertEqual(len(tools), 2)

    def test_get_tools_as_openai_format(self):
        """Test getting tools in OpenAI format."""
        tools = get_tools_as_openai_format()
        self.assertEqual(len(tools), 2)

        # Check the first tool
        tool1 = next(t for t in tools if t["function"]["name"] == "test_tool_1")
        self.assertEqual(tool1["type"], "function")
        self.assertIn("A test tool that concatenates", tool1["function"]["description"])

        # Check parameters
        params1 = tool1["function"]["parameters"]
        self.assertIn("param1", params1["properties"])
        self.assertIn("param2", params1["properties"])
        self.assertEqual(params1["properties"]["param1"]["type"], "string")
        self.assertEqual(params1["properties"]["param2"]["type"], "integer")
        self.assertIn("param1", params1["required"])
        self.assertNotIn("param2", params1["required"])  # param2 has a default value

        # Check the second tool
        tool2 = next(t for t in tools if t["function"]["name"] == "custom_name_tool")
        self.assertEqual(tool2["type"], "function")
        self.assertIn("A test tool that processes", tool2["function"]["description"])

        # Check parameters
        params2 = tool2["function"]["parameters"]
        self.assertIn("items", params2["properties"])
        self.assertIn("flag", params2["properties"])
        self.assertEqual(params2["properties"]["items"]["type"], "array")
        self.assertEqual(params2["properties"]["flag"]["type"], "boolean")
        self.assertIn("items", params2["required"])
        self.assertNotIn("flag", params2["required"])  # flag has a default value


if __name__ == "__main__":
    unittest.main()
