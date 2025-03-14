"""
Tests for the embedded reasoning functionality.
"""

import asyncio
import unittest
import logging
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from fluent_mcp.core.llm_client import (
    LLMClient,
    configure_llm_client,
    get_llm_client,
    run_embedded_reasoning,
    LLMClientError
)
from fluent_mcp.core.tool_registry import (
    register_embedded_tool,
    get_embedded_tool,
    list_embedded_tools,
    get_tools_as_openai_format,
    _embedded_tools
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_embedded_reasoning")

# Define some test tools
@register_embedded_tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@register_embedded_tool(name="greet_user")
def greet(name: str, formal: bool = False) -> str:
    """Generate a greeting for a user."""
    if formal:
        return f"Good day, {name}. How may I assist you today?"
    else:
        return f"Hey {name}! How's it going?"

class TestEmbeddedReasoning(unittest.TestCase):
    """Test cases for the embedded reasoning functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear the tool registry
        _embedded_tools.clear()
        
        # Re-register the test tools
        global add_numbers, greet
        add_numbers = register_embedded_tool()(add_numbers)
        greet = register_embedded_tool(name="greet_user")(greet)
        
        # Mock the LLM client
        self.mock_client = MagicMock()
        self.mock_client.provider = "test"
        self.mock_client.model = "test-model"
        
        # Create a mock response for chat completion
        self.mock_response = {
            "status": "complete",
            "content": "I'll help you with that calculation.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "add_numbers",
                        "arguments": {"a": 5, "b": 7}
                    }
                }
            ],
            "error": None
        }
        
        # Set up the mock client's chat_completion method
        async def mock_chat_completion(*args, **kwargs):
            return self.mock_response
        
        self.mock_client.chat_completion = mock_chat_completion
    
    @patch('fluent_mcp.core.llm_client.get_llm_client')
    def test_run_embedded_reasoning(self, mock_get_client):
        """Test running embedded reasoning."""
        # Set up the mock
        mock_get_client.return_value = self.mock_client
        
        # Run embedded reasoning
        system_prompt = "You are a helpful assistant that can use tools."
        user_prompt = "Can you add 5 and 7 for me?"
        
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_embedded_reasoning(system_prompt, user_prompt))
            
            # Check the result
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["content"], "I'll help you with that calculation.")
            self.assertEqual(len(result["tool_calls"]), 1)
            self.assertEqual(result["tool_calls"][0]["function"]["name"], "add_numbers")
            self.assertEqual(result["tool_calls"][0]["function"]["arguments"]["a"], 5)
            self.assertEqual(result["tool_calls"][0]["function"]["arguments"]["b"], 7)
        finally:
            loop.close()
        
    @patch('fluent_mcp.core.llm_client.get_llm_client')
    def test_run_embedded_reasoning_with_specific_tools(self, mock_get_client):
        """Test running embedded reasoning with specific tools."""
        # Set up the mock
        mock_get_client.return_value = self.mock_client
        
        # Create a specific tool list
        specific_tools = [
            {
                "type": "function",
                "function": {
                    "name": "greet_user",
                    "description": "Generate a greeting for a user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "formal": {"type": "boolean"}
                        },
                        "required": ["name"]
                    }
                }
            }
        ]
        
        # Run embedded reasoning with specific tools
        system_prompt = "You are a helpful assistant that can use tools."
        user_prompt = "Can you greet John formally?"
        
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_embedded_reasoning(system_prompt, user_prompt, tools=specific_tools))
        finally:
            loop.close()
    
    @patch('fluent_mcp.core.llm_client.get_llm_client')
    def test_run_embedded_reasoning_error_handling(self, mock_get_client):
        """Test error handling in embedded reasoning."""
        # Set up the mock to raise an exception
        mock_get_client.return_value = self.mock_client
        
        # Override the chat_completion method to raise an exception
        async def mock_chat_completion_error(*args, **kwargs):
            raise Exception("Test error")
        
        self.mock_client.chat_completion = mock_chat_completion_error
        
        # Run embedded reasoning
        system_prompt = "You are a helpful assistant that can use tools."
        user_prompt = "Can you add 5 and 7 for me?"
        
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_embedded_reasoning(system_prompt, user_prompt))
            
            # Check the result
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error"], "Test error")
            self.assertEqual(result["content"], "")
            self.assertEqual(len(result["tool_calls"]), 0)
        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main() 