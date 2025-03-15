"""
Budget management for Fluent MCP.

This module provides functionality for tracking and enforcing usage limits
for tools across projects, with support for both global default budgets
and custom budgets defined in prompt frontmatter.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from fluent_mcp.core.error_handling import MCPError


class BudgetExceededError(MCPError):
    """Error raised when a tool's budget has been exceeded."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        limit_type: str,
        current_usage: int,
        limit: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new budget exceeded error.

        Args:
            message: Error message
            tool_name: Name of the tool that exceeded its budget
            limit_type: Type of limit that was exceeded (hourly or daily)
            current_usage: Current usage count
            limit: Budget limit that was exceeded
            details: Additional error details
        """
        error_details = {
            "tool_name": tool_name,
            "limit_type": limit_type,
            "current_usage": current_usage,
            "limit": limit,
        }
        if details:
            error_details.update(details)

        super().__init__(message, "budget_exceeded", error_details)


class BudgetManager:
    """
    Manager for tracking and enforcing tool usage budgets.

    This class tracks tool usage by project, tool, and time period (hourly/daily),
    supports default budget limits, and allows custom budget overrides from
    prompt frontmatter.
    """

    def __init__(self, default_limits: Optional[Dict[str, Dict[str, int]]] = None):
        """
        Initialize a new budget manager.

        Args:
            default_limits: Optional dictionary of default budget limits by tool name.
                           Format: {tool_name: {"hourly_limit": int, "daily_limit": int}}
        """
        self.logger = logging.getLogger("fluent_mcp.budget")

        # Default limits for all tools if not specified
        self.global_default_hourly_limit = 100
        self.global_default_daily_limit = 1000

        # Default limits by tool name
        self.default_limits = default_limits or {}

        # Custom limits by prompt ID
        self.custom_limits: Dict[str, Dict[str, Dict[str, int]]] = {}

        # Usage tracking
        # Format: {project_id: {tool_name: {"hourly": {hour_timestamp: count}, "daily": {day_timestamp: count}}}}
        self.usage: Dict[str, Dict[str, Dict[str, Dict[int, int]]]] = {}

        self.logger.info("Budget manager initialized")
        if default_limits:
            self.logger.info(f"Default limits set for {len(default_limits)} tools")

    def set_custom_limits(self, prompt_id: str, limits: Dict[str, Dict[str, int]]) -> None:
        """
        Set custom budget limits for a specific prompt.

        Args:
            prompt_id: ID of the prompt
            limits: Dictionary of budget limits by tool name.
                   Format: {tool_name: {"hourly_limit": int, "daily_limit": int}}
        """
        self.custom_limits[prompt_id] = limits
        self.logger.info(f"Custom limits set for prompt {prompt_id} with {len(limits)} tool limits")

    def get_tool_limits(self, tool_name: str, prompt_id: Optional[str] = None) -> Tuple[int, int]:
        """
        Get the hourly and daily limits for a tool.

        Args:
            tool_name: Name of the tool
            prompt_id: Optional ID of the prompt with custom limits

        Returns:
            Tuple of (hourly_limit, daily_limit)
        """
        # Check for custom limits first
        if prompt_id and prompt_id in self.custom_limits:
            prompt_limits = self.custom_limits[prompt_id]
            if tool_name in prompt_limits:
                tool_limits = prompt_limits[tool_name]
                hourly_limit = tool_limits.get("hourly_limit")
                daily_limit = tool_limits.get("daily_limit")

                # Fall back to default limits if not specified
                if hourly_limit is None:
                    hourly_limit = self._get_default_hourly_limit(tool_name)
                if daily_limit is None:
                    daily_limit = self._get_default_daily_limit(tool_name)

                return hourly_limit, daily_limit

        # Fall back to default limits
        return (self._get_default_hourly_limit(tool_name), self._get_default_daily_limit(tool_name))

    def _get_default_hourly_limit(self, tool_name: str) -> int:
        """
        Get the default hourly limit for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Default hourly limit
        """
        if tool_name in self.default_limits and "hourly_limit" in self.default_limits[tool_name]:
            return self.default_limits[tool_name]["hourly_limit"]
        return self.global_default_hourly_limit

    def _get_default_daily_limit(self, tool_name: str) -> int:
        """
        Get the default daily limit for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Default daily limit
        """
        if tool_name in self.default_limits and "daily_limit" in self.default_limits[tool_name]:
            return self.default_limits[tool_name]["daily_limit"]
        return self.global_default_daily_limit

    def _get_current_hour_timestamp(self) -> int:
        """
        Get the timestamp for the current hour.

        Returns:
            Timestamp for the current hour (seconds since epoch, truncated to hour)
        """
        return int(time.time()) // 3600 * 3600

    def _get_current_day_timestamp(self) -> int:
        """
        Get the timestamp for the current day.

        Returns:
            Timestamp for the current day (seconds since epoch, truncated to day)
        """
        return int(time.time()) // 86400 * 86400

    def _get_usage(self, project_id: str, tool_name: str, period: str, timestamp: int) -> int:
        """
        Get the usage count for a tool in a specific period.

        Args:
            project_id: ID of the project
            tool_name: Name of the tool
            period: Time period ("hourly" or "daily")
            timestamp: Timestamp for the period

        Returns:
            Usage count
        """
        if (
            project_id in self.usage
            and tool_name in self.usage[project_id]
            and period in self.usage[project_id][tool_name]
            and timestamp in self.usage[project_id][tool_name][period]
        ):
            return self.usage[project_id][tool_name][period][timestamp]
        return 0

    def _increment_usage(self, project_id: str, tool_name: str, period: str, timestamp: int) -> int:
        """
        Increment the usage count for a tool in a specific period.

        Args:
            project_id: ID of the project
            tool_name: Name of the tool
            period: Time period ("hourly" or "daily")
            timestamp: Timestamp for the period

        Returns:
            New usage count
        """
        # Initialize nested dictionaries if they don't exist
        if project_id not in self.usage:
            self.usage[project_id] = {}
        if tool_name not in self.usage[project_id]:
            self.usage[project_id][tool_name] = {"hourly": {}, "daily": {}}
        if period not in self.usage[project_id][tool_name]:
            self.usage[project_id][tool_name][period] = {}

        # Increment usage
        if timestamp not in self.usage[project_id][tool_name][period]:
            self.usage[project_id][tool_name][period][timestamp] = 1
        else:
            self.usage[project_id][tool_name][period][timestamp] += 1

        return self.usage[project_id][tool_name][period][timestamp]

    def check_and_update_budget(self, project_id: str, tool_name: str, prompt_id: Optional[str] = None) -> bool:
        """
        Check if a tool call is within budget and update usage if it is.

        Args:
            project_id: ID of the project
            tool_name: Name of the tool
            prompt_id: Optional ID of the prompt with custom limits

        Returns:
            True if the call is within budget, False otherwise

        Raises:
            BudgetExceededError: If the tool call exceeds the budget
        """
        # Get current timestamps
        hour_timestamp = self._get_current_hour_timestamp()
        day_timestamp = self._get_current_day_timestamp()

        # Get current usage
        hourly_usage = self._get_usage(project_id, tool_name, "hourly", hour_timestamp)
        daily_usage = self._get_usage(project_id, tool_name, "daily", day_timestamp)

        # Get limits
        hourly_limit, daily_limit = self.get_tool_limits(tool_name, prompt_id)

        # Check if limits are exceeded
        if hourly_usage >= hourly_limit:
            next_hour = datetime.fromtimestamp(hour_timestamp + 3600).strftime("%H:%M:%S")
            raise BudgetExceededError(
                f"Hourly budget exceeded for tool '{tool_name}'. "
                f"Current usage: {hourly_usage}, Limit: {hourly_limit}. "
                f"Budget will reset at {next_hour}.",
                tool_name,
                "hourly",
                hourly_usage,
                hourly_limit,
            )

        if daily_usage >= daily_limit:
            next_day = datetime.fromtimestamp(day_timestamp + 86400).strftime("%Y-%m-%d")
            raise BudgetExceededError(
                f"Daily budget exceeded for tool '{tool_name}'. "
                f"Current usage: {daily_usage}, Limit: {daily_limit}. "
                f"Budget will reset on {next_day}.",
                tool_name,
                "daily",
                daily_usage,
                daily_limit,
            )

        # Update usage
        self._increment_usage(project_id, tool_name, "hourly", hour_timestamp)
        self._increment_usage(project_id, tool_name, "daily", day_timestamp)

        self.logger.debug(
            f"Tool '{tool_name}' usage updated for project '{project_id}': "
            f"hourly={hourly_usage + 1}/{hourly_limit}, daily={daily_usage + 1}/{daily_limit}"
        )

        return True

    def get_remaining_budget(
        self, project_id: str, tool_name: Optional[str] = None, prompt_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the remaining budget for a tool or all tools.

        Args:
            project_id: ID of the project
            tool_name: Optional name of the tool (if None, returns for all tools)
            prompt_id: Optional ID of the prompt with custom limits

        Returns:
            Dictionary with remaining budget information
        """
        # Get current timestamps
        hour_timestamp = self._get_current_hour_timestamp()
        day_timestamp = self._get_current_day_timestamp()

        result: Dict[str, Any] = {"project_id": project_id, "timestamp": int(time.time()), "tools": {}}

        # If tool_name is specified, only get budget for that tool
        if tool_name:
            tool_names = [tool_name]
        # Otherwise, get all tools that have been used or have custom limits
        else:
            tool_names: Set[str] = set()

            # Add tools that have been used
            if project_id in self.usage:
                tool_names.update(self.usage[project_id].keys())

            # Add tools with custom limits for the prompt
            if prompt_id and prompt_id in self.custom_limits:
                tool_names.update(self.custom_limits[prompt_id].keys())

            # Add tools with default limits
            tool_names.update(self.default_limits.keys())

        # Get budget for each tool
        for tool in tool_names:
            hourly_usage = self._get_usage(project_id, tool, "hourly", hour_timestamp)
            daily_usage = self._get_usage(project_id, tool, "daily", day_timestamp)

            hourly_limit, daily_limit = self.get_tool_limits(tool, prompt_id)

            result["tools"][tool] = {
                "hourly": {
                    "usage": hourly_usage,
                    "limit": hourly_limit,
                    "remaining": max(0, hourly_limit - hourly_usage),
                    "reset_time": hour_timestamp + 3600,
                },
                "daily": {
                    "usage": daily_usage,
                    "limit": daily_limit,
                    "remaining": max(0, daily_limit - daily_usage),
                    "reset_time": day_timestamp + 86400,
                },
            }

        return result

    def cleanup_old_usage_data(self) -> None:
        """
        Clean up old usage data to prevent memory leaks.

        This removes usage data older than 2 days.
        """
        current_time = int(time.time())
        two_days_ago = current_time - (2 * 86400)

        for project_id in list(self.usage.keys()):
            for tool_name in list(self.usage[project_id].keys()):
                # Clean up hourly data
                hourly_data = self.usage[project_id][tool_name].get("hourly", {})
                for timestamp in list(hourly_data.keys()):
                    if timestamp < two_days_ago:
                        del hourly_data[timestamp]

                # Clean up daily data
                daily_data = self.usage[project_id][tool_name].get("daily", {})
                for timestamp in list(daily_data.keys()):
                    if timestamp < two_days_ago:
                        del daily_data[timestamp]

                # Remove empty tool entries
                if not hourly_data and not daily_data:
                    del self.usage[project_id][tool_name]

            # Remove empty project entries
            if not self.usage[project_id]:
                del self.usage[project_id]

        self.logger.debug("Cleaned up old usage data")
