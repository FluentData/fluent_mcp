"""
Budget management tools for Fluent MCP.

This module provides built-in tools for checking and managing budgets.
"""

import logging
from typing import Any, Dict, Optional

from fluent_mcp.core.tool_registry import register_embedded_tool, register_external_tool


@register_embedded_tool()
def get_budget_status(
    project_id: str, tool_name: Optional[str] = None, prompt_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the current budget status for a tool or all tools.

    Args:
        project_id: ID of the project
        tool_name: Optional name of the tool (if None, returns for all tools)
        prompt_id: Optional ID of the prompt with custom limits

    Returns:
        Dictionary with budget information
    """
    from fluent_mcp.core.server import get_current_server

    logger = logging.getLogger("fluent_mcp.budget_tools")

    server = get_current_server()
    if not server or not hasattr(server, "budget_manager"):
        logger.warning("Budget manager not available")
        return {
            "error": "Budget manager not available",
            "project_id": project_id,
            "tool_name": tool_name,
        }

    budget_manager = server.budget_manager
    budget_info = budget_manager.get_remaining_budget(project_id, tool_name, prompt_id)

    logger.info(f"Retrieved budget status for project '{project_id}'")
    return budget_info


@register_external_tool()
def check_tool_budget(project_id: str, tool_name: str) -> Dict[str, Any]:
    """
    Check the remaining budget for a specific tool.

    This tool allows consuming LLMs to check if they have sufficient budget
    before making expensive tool calls.

    Args:
        project_id: ID of the project
        tool_name: Name of the tool to check

    Returns:
        Dictionary with budget information for the tool
    """
    from fluent_mcp.core.server import get_current_server

    logger = logging.getLogger("fluent_mcp.budget_tools")

    server = get_current_server()
    if not server or not hasattr(server, "budget_manager"):
        logger.warning("Budget manager not available")
        return {
            "error": "Budget manager not available",
            "project_id": project_id,
            "tool_name": tool_name,
        }

    budget_manager = server.budget_manager
    budget_info = budget_manager.get_remaining_budget(project_id, tool_name)

    # Simplify the response for external consumption
    if tool_name in budget_info["tools"]:
        tool_budget = budget_info["tools"][tool_name]

        # Format reset times as human-readable strings
        hourly_reset = tool_budget["hourly"]["reset_time"]
        daily_reset = tool_budget["daily"]["reset_time"]

        from datetime import datetime

        hourly_reset_str = datetime.fromtimestamp(hourly_reset).strftime("%H:%M:%S")
        daily_reset_str = datetime.fromtimestamp(daily_reset).strftime("%Y-%m-%d")

        result = {
            "tool_name": tool_name,
            "hourly": {
                "remaining": tool_budget["hourly"]["remaining"],
                "limit": tool_budget["hourly"]["limit"],
                "reset_at": hourly_reset_str,
            },
            "daily": {
                "remaining": tool_budget["daily"]["remaining"],
                "limit": tool_budget["daily"]["limit"],
                "reset_at": daily_reset_str,
            },
            "status": "ok",
        }

        # Add warning if budget is low
        if tool_budget["hourly"]["remaining"] < tool_budget["hourly"]["limit"] * 0.1:
            result["status"] = "warning"
            result["warning"] = f"Hourly budget is low: {tool_budget['hourly']['remaining']} calls remaining"
        elif tool_budget["daily"]["remaining"] < tool_budget["daily"]["limit"] * 0.1:
            result["status"] = "warning"
            result["warning"] = f"Daily budget is low: {tool_budget['daily']['remaining']} calls remaining"

        logger.info(f"Retrieved budget status for tool '{tool_name}' in project '{project_id}'")
        return result
    else:
        logger.warning(f"Tool '{tool_name}' not found in budget information")
        return {
            "tool_name": tool_name,
            "status": "unknown",
            "message": f"No budget information available for tool '{tool_name}'",
        }
