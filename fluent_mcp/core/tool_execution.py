"""
Tool execution for Fluent MCP.

This module provides functionality for executing tools with budget enforcement.
"""

import logging
from typing import Any, Callable, Dict, Optional

from fluent_mcp.core.budget import BudgetExceededError
from fluent_mcp.core.server import get_current_server
from fluent_mcp.core.tool_registry import get_embedded_tool, get_external_tool


async def execute_tool_with_budget(
    tool_name: str,
    arguments: Dict[str, Any],
    project_id: str,
    prompt_id: Optional[str] = None,
    is_embedded: bool = True,
) -> Dict[str, Any]:
    """
    Execute a tool with budget enforcement.

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        project_id: ID of the project (for budget tracking)
        prompt_id: Optional ID of the prompt with custom budget limits
        is_embedded: Whether the tool is an embedded tool or an external tool

    Returns:
        The result of the tool execution
    """
    logger = logging.getLogger("fluent_mcp.tool_execution")

    # Get the current server
    server = get_current_server()
    if not server:
        logger.warning("No server instance available")
        return {
            "error": "No server instance available",
            "tool_name": tool_name,
        }

    # Check if budget management is enabled
    if server.budget_manager:
        try:
            # Check and update budget
            server.budget_manager.check_and_update_budget(project_id, tool_name, prompt_id)
        except BudgetExceededError as e:
            logger.warning(f"Budget exceeded for tool '{tool_name}': {str(e)}")
            return {
                "error": "budget_exceeded",
                "message": str(e),
                "details": e.details,
            }

    # Get the tool function
    tool_fn = None
    if is_embedded:
        tool_fn = get_embedded_tool(tool_name)
    else:
        tool_fn = get_external_tool(tool_name)

    if not tool_fn:
        logger.warning(f"Tool not found: {tool_name}")
        return {
            "error": "tool_not_found",
            "message": f"Tool '{tool_name}' not found",
        }

    # Execute the tool
    try:
        logger.info(f"Executing tool: {tool_name}")
        result = tool_fn(**arguments)
        return result
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {str(e)}")
        return {
            "error": "tool_execution_error",
            "message": f"Error executing tool '{tool_name}': {str(e)}",
        }


async def execute_embedded_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    project_id: str,
    prompt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute an embedded tool with budget enforcement.

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        project_id: ID of the project (for budget tracking)
        prompt_id: Optional ID of the prompt with custom budget limits

    Returns:
        The result of the tool execution
    """
    return await execute_tool_with_budget(tool_name, arguments, project_id, prompt_id, is_embedded=True)


async def execute_external_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    project_id: str,
    prompt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute an external tool with budget enforcement.

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        project_id: ID of the project (for budget tracking)
        prompt_id: Optional ID of the prompt with custom budget limits

    Returns:
        The result of the tool execution
    """
    return await execute_tool_with_budget(tool_name, arguments, project_id, prompt_id, is_embedded=False)
