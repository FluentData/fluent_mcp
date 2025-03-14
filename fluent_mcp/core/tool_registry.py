"""
Tool registry for MCP.

This module provides a registry for tools that can be used by the LLM.
"""

from typing import Dict, Any, List, Callable, Optional


class Tool:
    """
    A tool that can be used by the LLM.
    """
    
    def __init__(self, name: str, description: str, function: Callable, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize a new tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            function: The function to call when the tool is invoked
            schema: JSON schema for the tool's parameters
        """
        self.name = name
        self.description = description
        self.function = function
        self.schema = schema or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary.
        
        Returns:
            A dictionary representation of the tool
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema
        }
        
    async def invoke(self, params: Dict[str, Any]) -> Any:
        """
        Invoke the tool with the given parameters.
        
        Args:
            params: Parameters for the tool
            
        Returns:
            The result of the tool invocation
        """
        # TODO: Implement parameter validation
        return await self.function(**params)


class ToolRegistry:
    """
    Registry for tools that can be used by the LLM.
    """
    
    def __init__(self):
        """Initialize a new tool registry."""
        self.tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: The tool to register
        """
        self.tools[tool.name] = tool
        print(f"Registered tool: {tool.name}")
        
    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            The tool, or None if not found
        """
        return self.tools.get(name)
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            A list of tool dictionaries
        """
        return [tool.to_dict() for tool in self.tools.values()] 