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

import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, get_args, get_origin, get_type_hints

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


def register_external_tool(name: Optional[str] = None):
    """
    Decorator to register a function as an external tool.

    IMPORTANT: External tools are the ONLY tools exposed to consuming LLMs through the MCP protocol.
    These tools are made available to external AI systems that interact with your MCP server.
    Use these for operations that you want to expose to consuming LLMs, such as data retrieval,
    code generation, or other capabilities you want to provide to external AI systems.

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
        _external_tools[tool_name] = wrapper
        logger.info(f"Registered external tool: {tool_name}")

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
