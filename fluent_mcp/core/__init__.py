"""
Core functionality for Fluent MCP.

This module provides the core functionality for the Fluent MCP framework,
including the server, prompt loader, tool registry, and LLM client.
"""

from fluent_mcp.core.budget import BudgetExceededError, BudgetManager
from fluent_mcp.core.budget_tools import check_tool_budget, get_budget_status
from fluent_mcp.core.error_handling import (
    ConfigError,
    MCPError,
    ServerError,
)
from fluent_mcp.core.llm_client import (
    LLMClientNotConfiguredError,
    configure_llm_client,
    get_llm_client,
    run_embedded_reasoning,
)
from fluent_mcp.core.prompt_loader import (
    InvalidBudgetFormatError,
    InvalidFrontmatterError,
    InvalidToolsFormatError,
    MissingRequiredFieldError,
    PromptLoaderError,
    get_prompt_budget,
    get_prompt_tools,
    load_prompts,
    parse_markdown_with_frontmatter,
)
from fluent_mcp.core.reflection import ReflectionLoop, ReflectionState
from fluent_mcp.core.reflection_loader import ReflectionLoader
from fluent_mcp.core.server import Server, get_current_server
from fluent_mcp.core.tool_execution import (
    execute_embedded_tool,
    execute_external_tool,
    execute_tool_with_budget,
)
from fluent_mcp.core.tool_registry import (
    get_embedded_tool,
    get_external_tool,
    get_external_tools_as_openai_format,
    get_tools_as_openai_format,
    list_embedded_tools,
    list_external_tools,
    register_embedded_tool,
    register_external_tool,
)

__all__ = [
    # Server
    "Server",
    "get_current_server",
    # LLM Client
    "configure_llm_client",
    "get_llm_client",
    "run_embedded_reasoning",
    "LLMClientNotConfiguredError",
    # Tool Registry
    "register_embedded_tool",
    "register_external_tool",
    "get_embedded_tool",
    "get_external_tool",
    "get_tools_as_openai_format",
    "get_external_tools_as_openai_format",
    "list_embedded_tools",
    "list_external_tools",
    # Tool Execution
    "execute_embedded_tool",
    "execute_external_tool",
    "execute_tool_with_budget",
    # Prompt Loader
    "load_prompts",
    "get_prompt_tools",
    "get_prompt_budget",
    "parse_markdown_with_frontmatter",
    "PromptLoaderError",
    "InvalidFrontmatterError",
    "MissingRequiredFieldError",
    "InvalidToolsFormatError",
    "InvalidBudgetFormatError",
    # Budget Management
    "BudgetManager",
    "BudgetExceededError",
    "get_budget_status",
    "check_tool_budget",
    # Error Handling
    "MCPError",
    "ConfigError",
    "ServerError",
    # Reflection
    "ReflectionLoader",
    "ReflectionLoop",
    "ReflectionState",
]
