"""
Tests for the external tool registry functionality.
"""

import unittest
import logging
from typing import List, Dict, Any
from unittest.mock import patch

from fluent_mcp.core.tool_registry import (
    register_external_tool,
    get_external_tool,
    list_external_tools,
    get_external_tools_as_openai_format,
    _external_tools
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_external_tools")

# Define some test external tools
@register_external_tool()
def fetch_data(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Fetch data from an external API."""
    return {"url": url, "params": params, "data": "Sample data"}

@register_external_tool(name="custom_external_tool")
def process_image(image_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process an image with external AI service."""
    return {
        "image_path": image_path,
        "options": options,
        "result": "Processed image data"
    }

class TestExternalTools(unittest.TestCase):
    """Test cases for the external tool registry functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear the registry before each test
        _external_tools.clear()
        
        # Re-register the test tools
        global fetch_data, process_image
        fetch_data = register_external_tool()(fetch_data)
        process_image = register_external_tool(name="custom_external_tool")(process_image)
    
    def test_register_external_tool(self):
        """Test registering an external tool."""
        # Check that the tools were registered
        self.assertIn("fetch_data", _external_tools)
        self.assertIn("custom_external_tool", _external_tools)
        
        # Check that the functions are preserved
        result = fetch_data("https://api.example.com", {"param1": "value1"})
        self.assertEqual(result["url"], "https://api.example.com")
        self.assertEqual(result["params"]["param1"], "value1")
        
        result = process_image("/path/to/image.jpg", {"resize": True})
        self.assertEqual(result["image_path"], "/path/to/image.jpg")
        self.assertTrue(result["options"]["resize"])
    
    def test_get_external_tool(self):
        """Test getting an external tool."""
        tool = get_external_tool("fetch_data")
        self.assertIsNotNone(tool)
        result = tool("https://api.example.com")
        self.assertEqual(result["url"], "https://api.example.com")
        
        tool = get_external_tool("custom_external_tool")
        self.assertIsNotNone(tool)
        
        # Test getting a non-existent tool
        tool = get_external_tool("non_existent_tool")
        self.assertIsNone(tool)
    
    def test_list_external_tools(self):
        """Test listing external tools."""
        tools = list_external_tools()
        self.assertIn("fetch_data", tools)
        self.assertIn("custom_external_tool", tools)
        self.assertEqual(len(tools), 2)
    
    def test_get_external_tools_as_openai_format(self):
        """Test getting external tools in OpenAI format."""
        tools = get_external_tools_as_openai_format()
        self.assertEqual(len(tools), 2)
        
        # Check the first tool
        fetch_data_tool = next((t for t in tools if t["function"]["name"] == "fetch_data"), None)
        self.assertIsNotNone(fetch_data_tool)
        self.assertEqual(fetch_data_tool["type"], "function")
        self.assertIn("url", fetch_data_tool["function"]["parameters"]["properties"])
        self.assertIn("params", fetch_data_tool["function"]["parameters"]["properties"])
        self.assertIn("url", fetch_data_tool["function"]["parameters"]["required"])
        
        # Check the second tool
        process_image_tool = next((t for t in tools if t["function"]["name"] == "custom_external_tool"), None)
        self.assertIsNotNone(process_image_tool)
        self.assertEqual(process_image_tool["type"], "function")
        self.assertIn("image_path", process_image_tool["function"]["parameters"]["properties"])
        self.assertIn("options", process_image_tool["function"]["parameters"]["properties"])
        self.assertIn("image_path", process_image_tool["function"]["parameters"]["required"])

if __name__ == "__main__":
    unittest.main() 