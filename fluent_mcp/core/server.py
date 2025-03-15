"""
Server implementation for MCP.

This module provides the server implementation for MCP,
handling HTTP requests and managing the server lifecycle.
"""

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, TextIO, Union

from fluent_mcp.core.llm_client import LLMClientError, configure_llm_client
from fluent_mcp.core.prompt_loader import get_prompt_budget, load_prompts
from fluent_mcp.core.tool_registry import (
    list_embedded_tools,
    register_external_tools,
    register_tool,
)

# Global variable to store the current server instance
_current_server = None


def get_current_server():
    """
    Get the current server instance.

    Returns:
        The current server instance, or None if no server is running
    """
    return _current_server


class Server:
    """
    MCP Server implementation.

    Handles HTTP requests and manages the server lifecycle.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        name: str = "mcp_server",
        stdin: TextIO = sys.stdin,
        stdout: TextIO = sys.stdout,
    ):
        """
        Initialize a new server instance.

        Args:
            config: Server configuration
            name: Server name
            stdin: Input stream (defaults to sys.stdin)
            stdout: Output stream (defaults to sys.stdout)
        """
        self.config = config
        self.name = name
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 8000)
        self.debug = config.get("debug", False)
        self.routes = []
        self.tools = []
        self.prompts = []
        self.stdin = stdin
        self.stdout = stdout
        self.logger = logging.getLogger(f"fluent_mcp.{name}")
        self.llm_configured = False

        # Initialize budget manager if budget configuration is provided
        self.budget_manager = None
        if "budget" in config:
            from fluent_mcp.core.budget import BudgetManager

            self.budget_manager = BudgetManager(config.get("budget", {}).get("default_limits", {}))
            self.logger.info("Budget manager initialized with default limits")

    def register_tool(self, tool: Any) -> None:
        """
        Register a tool with the server.

        Args:
            tool: The tool to register
        """
        self.logger.info(f"Registering tool: {getattr(tool, 'name', str(tool))}")
        self.tools.append(tool)

        # Also register with the tool registry if it's a callable
        if callable(tool):
            register_tool(tool)

    def load_prompt(self, prompt: Any) -> None:
        """
        Load a prompt into the server.

        Args:
            prompt: The prompt to load
        """
        self.logger.info(f"Loading prompt: {getattr(prompt, 'name', str(prompt))}")
        self.prompts.append(prompt)

    def read_message(self) -> Dict[str, Any]:
        """
        Read a message from stdin.

        Returns:
            The parsed message
        """
        line = self.stdin.readline().strip()
        if not line:
            return {}
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse message: {line}")
            return {}

    def write_message(self, message: Dict[str, Any]) -> None:
        """
        Write a message to stdout.

        Args:
            message: The message to write
        """
        self.stdout.write(json.dumps(message) + "\n")
        self.stdout.flush()

    @asynccontextmanager
    async def lifespan(self):
        """
        Lifespan context manager for the server.

        This is a placeholder for now - will be used for startup/shutdown tasks.
        """
        self.logger.info(f"Starting {self.name} server")
        try:
            yield
        finally:
            self.logger.info(f"Shutting down {self.name} server")

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message and return a response.

        Args:
            message: The message to process

        Returns:
            The response message
        """
        # This is a placeholder - will be implemented later
        message_type = message.get("type", "unknown")
        self.logger.debug(f"Processing message of type: {message_type}")

        # Echo the message back with a response field
        return {
            "type": f"{message_type}_response",
            "original_message": message,
            "response": f"Processed {message_type} message",
        }

    def run(self) -> None:
        """
        Run the server, processing stdin/stdout messages.
        """
        self.logger.info(f"Running {self.name} server with stdin/stdout transport")

        # Check if LLM is configured before running
        if not self.llm_configured:
            self.logger.warning("LLM client is not configured. Some functionality may be limited.")

        # Log available tools
        if self.tools:
            self.logger.info(f"Server has {len(self.tools)} tools registered")
            registered_tools = list_embedded_tools()
            if registered_tools:
                self.logger.info(f"Available embedded tools: {', '.join(registered_tools)}")
        else:
            self.logger.warning("No tools registered with the server")

        async def main():
            async with self.lifespan():
                while True:
                    message = self.read_message()
                    if not message:
                        await asyncio.sleep(0.1)
                        continue

                    response = await self.process_message(message)
                    if response:
                        self.write_message(response)

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.exception(f"Error running server: {e}")


def register_embedded_tools(tools: List[Callable]) -> None:
    """
    Register a list of embedded tools with the tool registry.

    Args:
        tools: List of tool functions to register
    """
    logger = logging.getLogger("fluent_mcp.server")

    if not tools:
        logger.warning("No embedded tools provided for registration")
        return

    logger.info(f"Registering {len(tools)} embedded tools with the tool registry")
    for tool in tools:
        if callable(tool):
            register_tool(tool)
        else:
            logger.warning(f"Skipping non-callable tool: {tool}")


def create_mcp_server(
    server_name: str,
    embedded_tools: list = None,
    external_tools: list = None,
    prompts: list = None,
    prompts_dir: str = None,
    config: dict = None,
) -> Server:
    """
    Create and configure an MCP server.

    Args:
        server_name: Name of the server
        embedded_tools: List of embedded tools to register with the server
        external_tools: List of external tools to register with the server
        prompts: List of prompts to register with the server
        prompts_dir: Directory containing prompt files to load
        config: Configuration dictionary for the server

    Returns:
        An MCP server instance ready to run
    """
    # Set up logging
    logger = logging.getLogger(f"fluent_mcp.{server_name}")
    logger.info(f"Creating MCP server: {server_name}")

    # Initialize server with config
    config = config or {}
    server = Server(config, name=server_name)

    # Set the current server instance
    global _current_server
    _current_server = server

    # Configure LLM client if config has necessary LLM settings
    if all(key in config for key in ["provider", "model"]):
        try:
            configure_llm_client(config)
            server.llm_configured = True
            logger.info("LLM client configured successfully")
        except LLMClientError as e:
            logger.error(f"Failed to configure LLM client: {str(e)}")
            logger.warning("Server will run without LLM capabilities")
    else:
        logger.warning("LLM configuration incomplete. Server will run without LLM capabilities.")

    # Register embedded tools with the tool registry
    register_embedded_tools(embedded_tools)

    # Register external tools with the tool registry
    register_external_tools(external_tools)

    # Register embedded tools with the server
    if embedded_tools:
        logger.info(f"Registering {len(embedded_tools)} embedded tools with the server")
        for tool in embedded_tools:
            server.register_tool(tool)
    else:
        logger.warning("No embedded tools provided")

    # Register external tools
    if external_tools:
        logger.info(f"Registering {len(external_tools)} external tools")
        for tool in external_tools:
            server.register_tool(tool)
    else:
        logger.info("No external tools provided")

    # Load prompts from directory if provided
    if prompts_dir:
        logger.info(f"Loading prompts from directory: {prompts_dir}")
        try:
            loaded_prompts = load_prompts(prompts_dir)
            if loaded_prompts:
                logger.info(f"Loaded {len(loaded_prompts)} prompts from {prompts_dir}")
                # Add loaded prompts to the provided prompts list
                if prompts is None:
                    prompts = []
                prompts.extend(loaded_prompts)
            else:
                logger.warning(f"No prompts found in directory: {prompts_dir}")
        except Exception as e:
            logger.error(f"Error loading prompts from directory {prompts_dir}: {str(e)}")

    # Load prompts
    if prompts:
        logger.info(f"Loading {len(prompts)} prompts")
        for prompt in prompts:
            server.load_prompt(prompt)

            # Set custom budget limits if specified in the prompt
            if server.budget_manager and "budget" in prompt["config"]:
                prompt_budget = get_prompt_budget(prompt)
                if prompt_budget:
                    prompt_id = prompt["config"]["name"]
                    server.budget_manager.set_custom_limits(prompt_id, prompt_budget)
                    logger.info(f"Set custom budget limits for prompt: {prompt_id}")
    else:
        logger.info("No prompts provided")

    logger.info(f"MCP server '{server_name}' created successfully")
    return server
