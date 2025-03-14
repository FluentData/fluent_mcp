"""
Fluent MCP - A modern package for MCP servers.

This package provides tools for scaffolding and managing MCP servers
with a focus on AI integration.
"""

__version__ = "0.1.0"

from fluent_mcp.core.server import create_mcp_server

# Import and expose core API
from fluent_mcp.scaffolder import scaffold_server

__all__ = ["scaffold_server", "create_mcp_server"]
