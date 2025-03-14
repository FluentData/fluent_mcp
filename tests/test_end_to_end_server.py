"""
End-to-end tests for MCP server functionality.

This module tests the complete flow of creating and using an MCP server,
including scaffolding, tool registration, prompt loading, and embedded reasoning.
"""

import os
import sys
import shutil
import tempfile
import unittest
import logging
import asyncio
import traceback
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_end_to_end_server")

# Import Fluent MCP components
from fluent_mcp import create_mcp_server
from fluent_mcp.core import (
    register_embedded_tool,
    register_external_tool,
    run_embedded_reasoning,
    LLMClient,
    configure_llm_client,
    get_llm_client
)

class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing.
    
    This class simulates the behavior of a real LLM client without making actual API calls.
    It responds to specific prompts with predefined responses and tool calls.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the mock client.
        
        Args:
            config: Configuration dictionary for the client
        """
        self.logger = logging.getLogger("fluent_mcp.llm_client")
        self.provider = config.get("provider", "mock")
        self.model = config.get("model", "mock-model")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.api_key = config.get("api_key", "mock-key")
        self._client = None
        self.logger.info(f"Initialized mock LLM client with model {self.model}")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             tools: Optional[List[Dict[str, Any]]] = None, 
                             temperature: float = 0.3, 
                             max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Mock implementation of chat completion.
        
        This method simulates the behavior of a real chat completion API call.
        It analyzes the input messages and tools, and returns a predefined response
        based on the content of the messages.
        
        Args:
            messages: List of messages in the conversation
            tools: List of tools available to the model
            temperature: Sampling temperature (not used in mock)
            max_tokens: Maximum number of tokens to generate (not used in mock)
            
        Returns:
            A dictionary containing the response and any tool calls
        """
        self.logger.info(f"Mock chat completion with {len(messages)} messages")
        
        # Extract the user message
        user_message = next((m["content"] for m in messages if m["role"] == "user"), "")
        
        # Check if tools are provided
        tool_names = []
        if tools:
            tool_names = [tool["function"]["name"] for tool in tools if tool["type"] == "function"]
            self.logger.info(f"Available tools: {', '.join(tool_names)}")
        
        # Prepare a mock response based on the user message
        if "Analyze this text:" in user_message:
            # Extract the text to analyze
            text_to_analyze = user_message.split("Analyze this text:", 1)[1].strip().strip("'\"")
            
            # Determine which tools to call based on available tools
            tool_calls = []
            
            if "word_count" in tool_names:
                tool_calls.append({
                    "id": "call_word_count",
                    "type": "function",
                    "function": {
                        "name": "word_count",
                        "arguments": {"text": text_to_analyze}
                    }
                })
            
            if "reverse_text" in tool_names:
                tool_calls.append({
                    "id": "call_reverse_text",
                    "type": "function",
                    "function": {
                        "name": "reverse_text",
                        "arguments": {"text": text_to_analyze}
                    }
                })
            
            return {
                "status": "complete",
                "content": f"I'll analyze the text: '{text_to_analyze}' using the available tools.",
                "tool_calls": tool_calls,
                "error": None
            }
        else:
            # Default response
            return {
                "status": "complete",
                "content": "I'm not sure how to help with that specific request.",
                "tool_calls": [],
                "error": None
            }


class TestEndToEndServer(unittest.TestCase):
    """
    Test end-to-end MCP server functionality.
    
    This test case validates the complete flow of creating and using an MCP server,
    including scaffolding, tool registration, prompt loading, and embedded reasoning.
    """
    
    def setUp(self):
        """
        Set up test environment.
        
        Creates a temporary directory structure for the test server,
        including prompts and tools directories.
        """
        # Create a temporary directory for the test server
        self.test_dir = tempfile.mkdtemp()
        self.server_dir = os.path.join(self.test_dir, "test_server")
        os.makedirs(self.server_dir)
        
        # Create a prompts directory
        self.prompts_dir = os.path.join(self.server_dir, "prompts")
        os.makedirs(self.prompts_dir)
        
        # Create a tools directory
        self.tools_dir = os.path.join(self.server_dir, "tools")
        os.makedirs(self.tools_dir)
        
        # Set up the current working directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create the necessary files for the test server
        self._create_test_server_files()
    
    def tearDown(self):
        """
        Clean up after tests.
        
        Restores the original working directory and removes the temporary directory.
        """
        # Restore the original working directory
        os.chdir(self.original_cwd)
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def _create_test_server_files(self):
        """
        Create the necessary files for the test server.
        
        This method creates:
        1. Python package structure with __init__.py files
        2. Embedded tool implementation (word_count)
        3. External tool implementation (reverse_text)
        4. Prompt file with YAML frontmatter
        5. Main server file
        """
        # Create __init__.py files to make the directories proper Python packages
        with open(os.path.join(self.server_dir, "__init__.py"), "w", encoding="utf-8") as f:
            f.write('"""Test server package."""\n')
        
        with open(os.path.join(self.tools_dir, "__init__.py"), "w", encoding="utf-8") as f:
            f.write('"""Test server tools package."""\n')
        
        # Create the embedded tools file
        embedded_tools_path = os.path.join(self.tools_dir, "embedded_tools.py")
        with open(embedded_tools_path, "w", encoding="utf-8") as f:
            f.write("""
from fluent_mcp.core import register_embedded_tool
from typing import Dict, Any

@register_embedded_tool()
def word_count(text: str) -> Dict[str, Any]:
    \"\"\"
    Count the number of words in a text.
    
    Args:
        text: The text to analyze
        
    Returns:
        A dictionary with word count statistics
    \"\"\"
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    return {
        "word_count": word_count,
        "character_count": char_count,
        "average_word_length": char_count / word_count if word_count > 0 else 0
    }
""")
        
        # Create the external tools file
        external_tools_path = os.path.join(self.tools_dir, "external_tools.py")
        with open(external_tools_path, "w", encoding="utf-8") as f:
            f.write("""
from fluent_mcp.core import register_external_tool
from typing import Dict, Any

@register_external_tool()
def reverse_text(text: str) -> Dict[str, Any]:
    \"\"\"
    Reverse the input text.
    
    Args:
        text: The text to reverse
        
    Returns:
        A dictionary with the reversed text and metadata
    \"\"\"
    reversed_text = text[::-1]
    
    return {
        "original_text": text,
        "reversed_text": reversed_text,
        "length": len(text)
    }
""")
        
        # Create the prompt file
        prompt_path = os.path.join(self.prompts_dir, "text_analysis.md")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("""---
name: Text Analysis Prompt
description: A prompt for analyzing text using embedded and external tools
model: gpt-4
temperature: 0.3
---

You are a text analysis assistant that can analyze text using various tools.

Available tools:
- word_count: Counts the number of words in a text
- reverse_text: Reverses the input text

When asked to analyze text, use these tools to provide insights about the text.
""")
        
        # Create the main server file
        main_path = os.path.join(self.server_dir, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write("""
import os
import sys
import logging
from fluent_mcp import create_mcp_server
from fluent_mcp.core import register_embedded_tool, register_external_tool

# Import tools
from tools.embedded_tools import word_count
from tools.external_tools import reverse_text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_server")

def main():
    # Create and run MCP server
    server = create_mcp_server(
        server_name="test_server",
        prompts_dir="prompts",
        config={
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434",
            "api_key": "ollama"
        }
    )
    
    server.run()

if __name__ == "__main__":
    main()
""")
    
    @patch('fluent_mcp.core.llm_client.LLMClient', MockLLMClient)
    def test_end_to_end_server(self):
        """
        Test the end-to-end MCP server functionality.
        
        This test validates:
        1. Importing tools from the test server
        2. Creating an MCP server with the tools and prompts
        3. Testing the embedded tool directly
        4. Testing the external tool directly
        5. Running embedded reasoning with the tools
        6. Verifying the results of the reasoning process
        """
        # Step 1: Import the tools from the test server
        # This simulates the user creating and importing tools in their own server
        logger.info("Step 1: Importing tools from the test server")
        sys.path.insert(0, self.test_dir)
        
        try:
            # Import the tools
            from test_server.tools.embedded_tools import word_count
            from test_server.tools.external_tools import reverse_text
            
            # Step 2: Create the MCP server
            # This simulates the user creating an MCP server with their tools and prompts
            logger.info("Step 2: Creating MCP server")
            server = create_mcp_server(
                server_name="test_server",
                embedded_tools=[word_count],  # Register the embedded tool
                external_tools=[reverse_text],  # Register the external tool
                prompts_dir=self.prompts_dir,  # Load prompts from the prompts directory
                config={
                    "provider": "mock",  # Use the mock provider for testing
                    "model": "mock-model"
                }
            )
            
            # Step 3: Test the embedded tool directly
            # This validates that the embedded tool works as expected
            logger.info("Step 3: Testing embedded tool directly")
            result = word_count("Hello world!")
            self.assertEqual(result["word_count"], 2)
            self.assertEqual(result["character_count"], 12)
            
            # Step 4: Test the external tool directly
            # This validates that the external tool works as expected
            logger.info("Step 4: Testing external tool directly")
            result = reverse_text("Hello world!")
            self.assertEqual(result["reversed_text"], "!dlrow olleH")
            
            # Step 5: Run embedded reasoning
            # This tests the integration of the LLM client with the tools
            logger.info("Step 5: Running embedded reasoning")
            
            # Create an event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run embedded reasoning with a test prompt
                system_prompt = "You are a helpful assistant that can analyze text."
                user_prompt = "Analyze this text: 'Hello world!'"
                
                try:
                    result = loop.run_until_complete(
                        run_embedded_reasoning(system_prompt, user_prompt)
                    )
                    
                    # Step 6: Verify the results
                    # This validates that the reasoning process worked correctly
                    logger.info("Step 6: Verifying results")
                    
                    # Check that the reasoning was completed successfully
                    self.assertEqual(result["status"], "complete")
                    self.assertIn("analyze", result["content"].lower())
                    self.assertIn("Hello world!", result["content"])
                    
                    # Check that the tools were called
                    self.assertTrue(len(result["tool_calls"]) > 0)
                    
                    # Check for word_count tool call
                    word_count_call = next(
                        (call for call in result["tool_calls"] if call["function"]["name"] == "word_count"),
                        None
                    )
                    self.assertIsNotNone(word_count_call)
                    self.assertEqual(word_count_call["function"]["arguments"]["text"], "Hello world!")
                    
                    # Check for reverse_text tool call
                    reverse_text_call = next(
                        (call for call in result["tool_calls"] if call["function"]["name"] == "reverse_text"),
                        None
                    )
                    self.assertIsNotNone(reverse_text_call)
                    self.assertEqual(reverse_text_call["function"]["arguments"]["text"], "Hello world!")
                    
                    logger.info("End-to-end test completed successfully")
                    
                except Exception as e:
                    logger.error(f"Error in embedded reasoning: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
                
            finally:
                loop.close()
                
        finally:
            # Clean up the path
            sys.path.remove(self.test_dir)


if __name__ == "__main__":
    unittest.main() 