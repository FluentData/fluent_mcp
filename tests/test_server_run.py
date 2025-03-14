"""
Test script for the MCP server.
"""

import logging
import sys
import json
import threading
import time
from fluent_mcp import create_mcp_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_script")

def main():
    """Main entry point."""
    logger.info("Creating test server")
    
    # Create a simple tool for testing
    class TestTool:
        def __init__(self, name):
            self.name = name
            
        def __str__(self):
            return f"TestTool({self.name})"
    
    # Create a simple prompt for testing
    class TestPrompt:
        def __init__(self, name):
            self.name = name
            
        def __str__(self):
            return f"TestPrompt({self.name})"
    
    # Create some test tools and prompts
    embedded_tools = [TestTool("embedded_tool_1"), TestTool("embedded_tool_2")]
    external_tools = [TestTool("external_tool_1")]
    prompts = [TestPrompt("prompt_1"), TestPrompt("prompt_2")]
    
    # Create a config with LLM settings
    config = {
        # Server settings
        "host": "localhost",
        "port": 8000,
        "debug": True,
        
        # LLM settings
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama"  # Dummy value for Ollama
    }
    
    # Create the server
    server = create_mcp_server(
        server_name="test_server",
        embedded_tools=embedded_tools,
        external_tools=external_tools,
        prompts=prompts,
        config=config
    )
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.run)
    server_thread.daemon = True
    server_thread.start()
    
    # Send a test message
    logger.info("Sending test message")
    test_message = {
        "type": "test",
        "content": "Hello, server!"
    }
    print(json.dumps(test_message))
    
    # Wait for a response
    logger.info("Waiting for response")
    time.sleep(1)
    
    logger.info("Test complete")

if __name__ == "__main__":
    main() 