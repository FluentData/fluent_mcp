# Budget Management in Fluent MCP

This guide explains how to use the budget management system in Fluent MCP to track and enforce usage limits for tools across projects.

## Overview

The budget management system allows you to:

1. Set default budget limits for tools
2. Define custom budget limits in prompt frontmatter
3. Track tool usage by project, tool, and time period (hourly/daily)
4. Enforce budget limits during tool execution
5. Check remaining budget status

This helps prevent excessive tool usage, control costs, and ensure fair resource allocation across different projects and users.

## Configuring Default Budgets

You can configure default budget limits when creating an MCP server:

```python
from fluent_mcp import create_mcp_server

# Define default budget limits
budget_config = {
    "default_limits": {
        "search_database": {
            "hourly_limit": 50,
            "daily_limit": 500
        },
        "generate_image": {
            "hourly_limit": 10,
            "daily_limit": 100
        }
    }
}

# Create server with budget configuration
server = create_mcp_server(
    server_name="my_server",
    embedded_tools=[...],
    external_tools=[...],
    config={
        "provider": "openai",
        "model": "gpt-4",
        "budget": budget_config
    }
)
```

If no specific limits are set for a tool, it will use the global defaults:
- Hourly limit: 100 calls
- Daily limit: 1000 calls

## Custom Budgets in Prompt Frontmatter

You can define custom budget limits for specific prompts using frontmatter:

```markdown
---
name: data_analysis_prompt
description: A prompt for analyzing data
model: gpt-4
temperature: 0.3
tools:
  - search_database
  - analyze_data
  - generate_chart
budget:
  search_database:
    hourly_limit: 20
    daily_limit: 200
  analyze_data:
    hourly_limit: 15
    daily_limit: 150
  generate_chart:
    hourly_limit: 5
    daily_limit: 50
---
You are a data analysis assistant with access to several tools.
Use these tools to help analyze data and generate insights.
```

These custom limits will override the default limits when this specific prompt is used.

## Checking Budget Status

You can check the remaining budget for tools using the built-in tools:

### For Embedded LLMs

```python
from fluent_mcp.core.budget_tools import get_budget_status

# Check budget for all tools in a project
budget_info = get_budget_status(project_id="my_project")

# Check budget for a specific tool
tool_budget = get_budget_status(
    project_id="my_project",
    tool_name="search_database"
)

# Check budget with custom limits from a prompt
prompt_budget = get_budget_status(
    project_id="my_project",
    tool_name="search_database",
    prompt_id="data_analysis_prompt"
)
```

### For Consuming LLMs

External LLMs can check tool budgets using the `check_tool_budget` tool:

```python
# Example of a consuming LLM calling the check_tool_budget tool
result = await llm.call_tool(
    "check_tool_budget",
    {
        "project_id": "my_project",
        "tool_name": "search_database"
    }
)

# The result will include:
# {
#   "tool_name": "search_database",
#   "hourly": {
#     "remaining": 45,
#     "limit": 50,
#     "reset_at": "14:30:00"
#   },
#   "daily": {
#     "remaining": 450,
#     "limit": 500,
#     "reset_at": "2023-06-15"
#   },
#   "status": "ok"
# }
```

## Budget Enforcement

When a tool is called, the budget manager automatically:

1. Checks if the call would exceed hourly or daily limits
2. If limits are exceeded, returns a `BudgetExceededError`
3. If within limits, increments usage counters and allows the call

Example of handling budget exceeded errors:

```python
from fluent_mcp.core.budget import BudgetExceededError
from fluent_mcp.core.tool_execution import execute_embedded_tool

try:
    result = await execute_embedded_tool(
        tool_name="search_database",
        arguments={"query": "example"},
        project_id="my_project"
    )
    # Process result
except BudgetExceededError as e:
    print(f"Budget exceeded: {e}")
    # Handle budget exceeded case
```

## API Reference

### BudgetManager

The core class that manages budgets and tracks usage.

```python
from fluent_mcp.core.budget import BudgetManager

# Create a budget manager with default limits
budget_manager = BudgetManager({
    "tool_name": {
        "hourly_limit": 50,
        "daily_limit": 500
    }
})

# Set custom limits for a prompt
budget_manager.set_custom_limits(
    prompt_id="my_prompt",
    limits={
        "tool_name": {
            "hourly_limit": 20,
            "daily_limit": 200
        }
    }
)

# Check and update budget
try:
    budget_manager.check_and_update_budget(
        project_id="my_project",
        tool_name="tool_name",
        prompt_id="my_prompt"  # Optional
    )
except BudgetExceededError as e:
    # Handle budget exceeded
    pass

# Get remaining budget
budget_info = budget_manager.get_remaining_budget(
    project_id="my_project",
    tool_name="tool_name",  # Optional, if None returns all tools
    prompt_id="my_prompt"   # Optional
)

# Clean up old usage data
budget_manager.cleanup_old_usage_data()
```

### Tool Execution with Budget Enforcement

```python
from fluent_mcp.core.tool_execution import (
    execute_tool_with_budget,
    execute_embedded_tool,
    execute_external_tool
)

# Execute an embedded tool with budget enforcement
result = await execute_embedded_tool(
    tool_name="tool_name",
    arguments={"param": "value"},
    project_id="my_project",
    prompt_id="my_prompt"  # Optional
)

# Execute an external tool with budget enforcement
result = await execute_external_tool(
    tool_name="tool_name",
    arguments={"param": "value"},
    project_id="my_project",
    prompt_id="my_prompt"  # Optional
)
```

## Best Practices

1. **Set appropriate limits**: Consider the nature of each tool and set limits accordingly. Expensive or resource-intensive tools should have lower limits.

2. **Use project-specific tracking**: Use different project IDs for different use cases to track and limit usage separately.

3. **Implement graceful fallbacks**: When a budget is exceeded, provide alternative solutions or clear guidance to users.

4. **Monitor usage patterns**: Regularly review budget usage to identify potential issues or opportunities for optimization.

5. **Clean up old data**: Call `cleanup_old_usage_data()` periodically to prevent memory leaks from accumulating usage data.

6. **Use custom budgets wisely**: Define custom budgets in prompts that have specific requirements, but don't override defaults unnecessarily.

7. **Check budgets proactively**: Before making expensive tool calls, check the remaining budget to avoid unexpected failures.

## Example: Complete Budget Management Workflow

```python
import asyncio
from fluent_mcp import create_mcp_server
from fluent_mcp.core.budget_tools import get_budget_status
from fluent_mcp.core.llm_client import run_embedded_reasoning
from fluent_mcp.core.tool_registry import register_embedded_tool

# Define and register a tool
@register_embedded_tool()
def search_database(query: str):
    """Search the database for information."""
    # Implementation...
    return {"results": ["result1", "result2"]}

# Define budget configuration
budget_config = {
    "default_limits": {
        "search_database": {
            "hourly_limit": 50,
            "daily_limit": 500
        }
    }
}

# Create server with budget configuration
server = create_mcp_server(
    server_name="my_server",
    embedded_tools=[search_database],
    config={
        "provider": "openai",
        "model": "gpt-4",
        "budget": budget_config
    }
)

async def main():
    # Check initial budget
    initial_budget = get_budget_status(
        project_id="my_project",
        tool_name="search_database"
    )
    print(f"Initial budget: {initial_budget}")
    
    # Run embedded reasoning with budget tracking
    result = await run_embedded_reasoning(
        system_prompt="You are a helpful assistant with access to a database.",
        user_prompt="Find information about machine learning.",
        project_id="my_project"
    )
    
    # Check updated budget
    updated_budget = get_budget_status(
        project_id="my_project",
        tool_name="search_database"
    )
    print(f"Updated budget: {updated_budget}")
    
    # Process results
    print(f"Response: {result['content']}")
    if "tool_results" in result:
        for tool_result in result["tool_results"]:
            print(f"Tool: {tool_result['function_name']}")
            print(f"Result: {tool_result['result']}")

# Run the example
asyncio.run(main())
```

## Troubleshooting

### Budget Exceeded Errors

If you encounter budget exceeded errors, you have several options:

1. **Increase the limits**: Adjust the budget limits if they're too restrictive.
2. **Wait for reset**: Hourly budgets reset every hour, daily budgets reset every day.
3. **Use a different project ID**: If appropriate, use a different project ID with separate budget tracking.
4. **Optimize tool usage**: Review your code to reduce unnecessary tool calls.

### Missing Budget Information

If budget information is not available:

1. **Check server configuration**: Ensure the server was created with budget configuration.
2. **Verify project ID**: Make sure you're using the correct project ID for tracking.
3. **Check tool names**: Ensure tool names match exactly what's registered.

### Memory Usage Concerns

If you're concerned about memory usage from tracking many tools:

1. **Call cleanup_old_usage_data()**: Periodically clean up old usage data.
2. **Limit tracked projects**: Use a consistent set of project IDs rather than generating new ones.
3. **Focus on high-value tools**: Only set explicit limits for tools that need them. 