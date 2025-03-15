"""
Fluent MCP - A modern package for MCP servers.

This package provides tools for scaffolding and managing MCP servers
with a focus on AI integration.
"""

__version__ = "0.1.0"

# Import and expose budget management
from fluent_mcp.core.budget import BudgetExceededError, BudgetManager
from fluent_mcp.core.budget_tools import check_tool_budget, get_budget_status
from fluent_mcp.core.server import create_mcp_server
from fluent_mcp.core.tool_execution import execute_embedded_tool, execute_external_tool

# Import and expose core API
from fluent_mcp.scaffolder import scaffold_server

__all__ = [
    "scaffold_server",
    "create_mcp_server",
    "BudgetManager",
    "BudgetExceededError",
    "get_budget_status",
    "check_tool_budget",
    "execute_embedded_tool",
    "execute_external_tool",
]
