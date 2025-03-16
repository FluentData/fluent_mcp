"""
Tool registry for Fluent MCP.

This module provides functionality for registering and retrieving
tools that can be used by the MCP server.

There are two distinct types of tools in Fluent MCP:

1. Embedded Tools: These tools are ONLY for use by the embedded LLM within the MCP server.
   They are not exposed to consuming LLMs and are used for internal reasoning and processing.
   Register these with the @register_embedded_tool decorator.

2. External Tools: These tools are exposed through the MCP server to consuming LLMs.
   They are the only tools that external AI systems can access via the MCP protocol.
   Register these with the @register_external_tool decorator.

This architectural pattern ensures a clear separation between internal tools used by
the embedded reasoning engine and external tools exposed to consuming LLMs.
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union, get_args, get_origin, get_type_hints

from fluent_mcp.core.error_handling import MCPError
from fluent_mcp.core.reflection import ReflectionLoop

# Global registry for embedded tools
_embedded_tools = {}

# Global registry for external tools
_external_tools = {}

logger = logging.getLogger("fluent_mcp.tool_registry")


def register_embedded_tool(name: Optional[str] = None):
    """
    Decorator to register a function as an embedded tool.

    IMPORTANT: Embedded tools are ONLY for use by the embedded LLM within the MCP server.
    They are hidden from consuming LLMs and only available to the embedded reasoning engine.
    Use these for internal processing, reasoning, and operations that should not be
    directly exposed to external AI systems.

    Args:
        name: Optional name for the tool. If not provided, the function name will be used.

    Returns:
        The decorated function.
    """

    def decorator(func):
        nonlocal name
        tool_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Register the tool
        _embedded_tools[tool_name] = wrapper
        logger.info(f"Registered embedded tool: {tool_name}")

        return wrapper

    return decorator


def register_external_tool(
    name: Optional[str] = None,
    use_reflection: bool = True,
    reflection_budget: int = 5,
):
    """
    Decorator to register a function as an external tool.

    IMPORTANT: External tools are the ONLY tools exposed to consuming LLMs through the MCP protocol.
    These tools are made available to external AI systems that interact with your MCP server.
    Use these for operations that you want to expose to consuming LLMs, such as data retrieval,
    code generation, or other capabilities you want to provide to external AI systems.

    The decorator supports structured reflection, allowing tools to use the reflection loop
    for improved reasoning and decision making.

    Args:
        name: Optional name for the tool. If not provided, the function name will be used.
        use_reflection: Whether to enable structured reflection for this tool (default: True)
        reflection_budget: Number of iterations for reflection (default: 5)

    Returns:
        The decorated function.

    Example:
        @register_external_tool(use_reflection=True, reflection_budget=10)
        async def web_research(query: str, task: str = 'Research this topic') -> str:
            '''Research a topic on the web.'''
            # Implementation details...
            return result
    """

    def decorator(func):
        nonlocal name
        tool_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # If reflection is disabled, execute the function directly
                if not use_reflection:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)

                # Get the task from kwargs or use a default
                task = kwargs.get("task", "Execute this tool")

                # Create reflection loop instance
                reflection_loop = ReflectionLoop()

                # Get the LLM client from kwargs (required for reflection)
                llm_client = kwargs.get("llm_client")
                if not llm_client:
                    raise MCPError("LLM client is required for reflection")

                # Run the structured reflection loop
                reflection_result = await reflection_loop.run_structured_reflection_loop(
                    original_task=task,
                    tool_name=tool_name,
                    llm_client=llm_client,
                    initial_budget=reflection_budget,
                    max_iterations=reflection_budget,
                )

                # Check reflection status
                if reflection_result["status"] == "complete":
                    return reflection_result["result"]
                elif reflection_result["status"] == "budget_exhausted":
                    raise MCPError("Reflection budget exhausted before completion")
                elif reflection_result["status"] == "error":
                    raise MCPError(f"Reflection error: {reflection_result['result']}")
                else:
                    raise MCPError(f"Unexpected reflection status: {reflection_result['status']}")

            except Exception as e:
                logger.error(f"Error in external tool {tool_name}: {str(e)}")
                raise MCPError(f"Tool execution failed: {str(e)}")

        # Register the tool
        _external_tools[tool_name] = wrapper
        logger.info(f"Registered external tool: {tool_name} (reflection: {use_reflection})")

        return wrapper

    return decorator


def get_embedded_tool(name: str) -> Optional[Callable]:
    """
    Get an embedded tool by name.

    Args:
        name: The name of the tool to retrieve.

    Returns:
        The tool function if found, None otherwise.
    """
    tool = _embedded_tools.get(name)
    if tool:
        logger.debug(f"Retrieved embedded tool: {name}")
    else:
        logger.warning(f"Embedded tool not found: {name}")

    return tool


def get_external_tool(name: str) -> Optional[Callable]:
    """
    Get an external tool by name.

    Args:
        name: The name of the tool to retrieve.

    Returns:
        The tool function if found, None otherwise.
    """
    tool = _external_tools.get(name)
    if tool:
        logger.debug(f"Retrieved external tool: {name}")
    else:
        logger.warning(f"External tool not found: {name}")

    return tool


def list_embedded_tools() -> List[str]:
    """
    List all registered embedded tool names.

    Returns:
        A list of registered tool names.
    """
    return list(_embedded_tools.keys())


def list_external_tools() -> List[str]:
    """
    List all registered external tool names.

    Returns:
        A list of registered external tool names.
    """
    return list(_external_tools.keys())


def _get_parameter_schema(param: inspect.Parameter) -> Dict[str, Any]:
    """
    Generate a JSON Schema for a function parameter.

    Args:
        param: The parameter to generate a schema for.

    Returns:
        A JSON Schema object for the parameter.
    """
    schema = {}

    # Get type annotation if available
    type_hints = get_type_hints(param.default) if callable(param.default) else {}
    param_type = type_hints.get("return") if type_hints else param.annotation

    # Handle different types
    if param_type is inspect.Parameter.empty:
        schema["type"] = "string"  # Default to string if no type hint
    elif param_type is str:
        schema["type"] = "string"
    elif param_type is int:
        schema["type"] = "integer"
    elif param_type is float:
        schema["type"] = "number"
    elif param_type is bool:
        schema["type"] = "boolean"
    elif get_origin(param_type) is list or get_origin(param_type) is List:
        schema["type"] = "array"
        item_type = get_args(param_type)[0] if get_args(param_type) else "string"
        if item_type is str:
            schema["items"] = {"type": "string"}
        elif item_type is int:
            schema["items"] = {"type": "integer"}
        elif item_type is float:
            schema["items"] = {"type": "number"}
        elif item_type is bool:
            schema["items"] = {"type": "boolean"}
        else:
            schema["items"] = {"type": "object"}
    elif get_origin(param_type) is dict or get_origin(param_type) is Dict:
        schema["type"] = "object"
    else:
        schema["type"] = "object"

    # Handle default values and required status
    if param.default is not inspect.Parameter.empty:
        schema["default"] = param.default

    return schema


def get_tools_as_openai_format() -> List[Dict[str, Any]]:
    """
    Get all registered embedded tools in OpenAI function calling format.

    These tools are for use by the embedded LLM within the MCP server and are not
    exposed to consuming LLMs. This function is typically used when setting up
    the embedded reasoning engine to give it access to internal tools.

    Returns:
        A list of tools formatted for OpenAI's function calling API.
    """
    return _get_tools_as_openai_format(_embedded_tools)


def get_external_tools_as_openai_format() -> List[Dict[str, Any]]:
    """
    Get all registered external tools in OpenAI function calling format.

    These tools are exposed to consuming LLMs through the MCP protocol. This function
    is typically used when setting up the MCP server to expose tools to external
    AI systems.

    Returns:
        A list of external tools formatted for OpenAI's function calling API.
    """
    return _get_tools_as_openai_format(_external_tools)


def _get_tools_as_openai_format(
    tools_dict: Dict[str, Callable],
) -> List[Dict[str, Any]]:
    """
    Convert a dictionary of tools to OpenAI function calling format.

    Args:
        tools_dict: Dictionary of tool name to tool function

    Returns:
        A list of tools formatted for OpenAI's function calling API.
    """
    tools = []

    for name, func in tools_dict.items():
        # Get function signature and docstring
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description available."

        # Create parameters schema
        parameters = {"type": "object", "properties": {}, "required": []}

        for param_name, param in sig.parameters.items():
            # Skip self parameter for methods
            if param_name == "self":
                continue

            # Add parameter to schema
            parameters["properties"][param_name] = _get_parameter_schema(param)

            # Mark as required if no default value
            if param.default is inspect.Parameter.empty:
                parameters["required"].append(param_name)

        # Create tool definition
        tool = {
            "type": "function",
            "function": {"name": name, "description": doc, "parameters": parameters},
        }

        tools.append(tool)

    return tools


def register_tool(tool: Callable) -> None:
    """
    Register a tool function directly (non-decorator approach).

    Args:
        tool: The tool function to register.
    """
    tool_name = getattr(tool, "__name__", str(tool))
    _embedded_tools[tool_name] = tool
    logger.info(f"Registered embedded tool: {tool_name}")


def register_external_tools(tools: List[Callable]) -> None:
    """
    Register a list of external tools with the tool registry.

    IMPORTANT: External tools are the ONLY tools exposed to consuming LLMs through the MCP protocol.
    This function allows you to register multiple external tools at once, which is useful when
    setting up an MCP server with a predefined set of tools.

    Args:
        tools: List of tool functions to register as external tools
    """
    if not tools:
        logger.warning("No external tools provided for registration")
        return

    logger.info(f"Registering {len(tools)} external tools with the tool registry")
    for tool in tools:
        if callable(tool):
            tool_name = getattr(tool, "__name__", str(tool))
            _external_tools[tool_name] = tool
            logger.info(f"Registered external tool: {tool_name}")
        else:
            logger.warning(f"Skipping non-callable external tool: {tool}")


@register_embedded_tool()
def gather_thoughts(
    analysis: str,
    next_steps: str,
    workflow_state: str,
    is_complete: bool = False,
) -> Dict[str, Any]:
    """
    Gather thoughts and insights during the structured reflection process.

    This tool is used by the embedded LLM to record its analysis, plan next steps,
    and update the workflow state during the structured reflection loop. It helps
    track progress and maintain state across iterations of the reflection process.

    The tool is typically called when the LLM has:
    1. Analyzed the current situation or previous actions
    2. Determined the next steps to take
    3. Updated its understanding of the workflow state
    4. Decided whether the task is complete

    Args:
        analysis: Current analysis of the situation, including insights and observations
        next_steps: Planned next steps or actions to take
        workflow_state: Current state of the workflow, tracking progress and decisions
        is_complete: Whether the reflection process is complete (default: False)

    Returns:
        A dictionary containing:
        - status: 'complete' if is_complete is True, otherwise 'in_progress'
        - analysis: The provided analysis
        - next_steps: The provided next steps
        - workflow_state: The provided workflow state
    """
    return {
        "status": "complete" if is_complete else "in_progress",
        "analysis": analysis,
        "next_steps": next_steps,
        "workflow_state": workflow_state,
    }


@register_embedded_tool()
def job_complete(result: str) -> Dict[str, Any]:
    """
    Mark a job as complete and provide the final result.

    This tool is used by the embedded LLM to indicate that a task has been
    completed successfully and to provide the final result. It should be called
    when the LLM has:
    1. Successfully completed all required steps
    2. Generated a satisfactory final result
    3. Determined that no further reflection is needed

    The tool helps maintain a clear separation between in-progress work and
    completed tasks, making it easier to track the status of long-running
    or complex operations.

    Args:
        result: The final result or output of the completed task

    Returns:
        A dictionary containing:
        - status: Always 'complete'
        - result: The provided final result
    """
    return {
        "status": "complete",
        "result": result,
    }
