"""
Core functionality for Fluent MCP.

This module contains the core components for server management,
LLM integration, tool registry, and error handling.
"""

from fluent_mcp.core.server import Server
from fluent_mcp.core.llm_client import (
    LLMClient, 
    configure_llm_client, 
    get_llm_client,
    run_embedded_reasoning
)
from fluent_mcp.core.tool_registry import (
    register_embedded_tool,
    get_embedded_tool,
    list_embedded_tools,
    get_tools_as_openai_format
)

__all__ = [
    "Server",
    "LLMClient",
    "configure_llm_client",
    "get_llm_client",
    "run_embedded_reasoning",
    "register_embedded_tool",
    "get_embedded_tool",
    "list_embedded_tools",
    "get_tools_as_openai_format",
]
