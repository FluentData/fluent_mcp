"""
Interactive test script for the MCP server.

This script creates a server and client in separate processes,
allowing them to communicate via pipes.
"""

import json
import logging
import subprocess
import sys
import threading
import time
from io import StringIO

from fluent_mcp import create_mcp_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interactive_test")


def server_process():
    """Run the server process."""

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
        "api_key": "ollama",  # Dummy value for Ollama
    }

    # Create the server
    server = create_mcp_server(
        server_name="interactive_server",
        embedded_tools=embedded_tools,
        external_tools=external_tools,
        prompts=prompts,
        config=config,
    )

    # Run the server
    server.run()


def client_process():
    """Run the client process."""
    logger.info("Starting client process")

    # Create a subprocess for the server
    server_proc = subprocess.Popen(
        [sys.executable, __file__, "--server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Function to read from the server's stdout
    def read_stdout():
        while True:
            line = server_proc.stdout.readline()
            if not line:
                break
            try:
                response = json.loads(line)
                logger.info(f"Received response: {response}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response: {line}")

    # Start a thread to read from the server's stdout
    stdout_thread = threading.Thread(target=read_stdout)
    stdout_thread.daemon = True
    stdout_thread.start()

    # Send some test messages
    test_messages = [
        {"type": "hello", "content": "Hello, server!"},
        {"type": "echo", "content": "Echo this message"},
        {"type": "query", "content": "What tools do you have?"},
    ]

    for message in test_messages:
        logger.info(f"Sending message: {message}")
        server_proc.stdin.write(json.dumps(message) + "\n")
        server_proc.stdin.flush()
        time.sleep(1)

    # Wait for a bit to receive all responses
    time.sleep(2)

    # Terminate the server process
    logger.info("Terminating server process")
    server_proc.terminate()
    server_proc.wait()

    logger.info("Client process complete")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        server_process()
    else:
        client_process()


if __name__ == "__main__":
    main()
