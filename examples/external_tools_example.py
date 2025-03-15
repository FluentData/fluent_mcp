"""
Example usage of external tools in Fluent MCP.

This script demonstrates how to register and use external tools
that are exposed to consuming LLMs through the MCP protocol.

IMPORTANT: External tools are the ONLY tools exposed to consuming LLMs through the MCP protocol.
These tools are made available to external AI systems that interact with your MCP server.
Use these for operations that you want to expose to consuming LLMs, such as data retrieval,
code generation, or other capabilities you want to provide to external AI systems.
"""

import json
import logging
from typing import Any, Dict, List

from fluent_mcp import create_mcp_server
from fluent_mcp.core.tool_registry import (
    get_external_tool,
    get_external_tools_as_openai_format,
    list_external_tools,
    register_external_tool,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("external_tools_example")


# Define some example external tools
# These tools are exposed to consuming LLMs through the MCP protocol
@register_external_tool()
def search_documentation(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the documentation for a given query.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        A list of matching documentation entries
    """
    # This is a mock implementation
    logger.info(f"Searching documentation for: {query} (max results: {max_results})")

    # In a real implementation, you would search a documentation database
    mock_results = [
        {
            "title": "Getting Started",
            "url": "https://docs.example.com/getting-started",
            "snippet": f"This guide will help you get started with our product. Relevant to: {query}",
        },
        {
            "title": "API Reference",
            "url": "https://docs.example.com/api-reference",
            "snippet": f"Complete API reference for developers. Relevant to: {query}",
        },
        {
            "title": "Troubleshooting",
            "url": "https://docs.example.com/troubleshooting",
            "snippet": f"Common issues and their solutions. Relevant to: {query}",
        },
    ]

    return mock_results[:max_results]


@register_external_tool(name="generate_code_snippet")
def generate_code(language: str, task_description: str) -> Dict[str, Any]:
    """
    Generate a code snippet for a given task.

    Args:
        language: The programming language to use
        task_description: Description of what the code should do

    Returns:
        A dictionary containing the generated code and metadata
    """
    # This is a mock implementation
    logger.info(f"Generating {language} code for: {task_description}")

    # In a real implementation, you would call an LLM or code generation service
    mock_code = ""
    if language.lower() == "python":
        mock_code = f"""
def solve_{task_description.replace(" ", "_")}():
    # TODO: Implement {task_description}
    print("Solving: {task_description}")
    return "Solution"
        """
    elif language.lower() == "javascript":
        mock_code = f"""
function solve{task_description.replace(" ", "")}() {{
    // TODO: Implement {task_description}
    console.log("Solving: {task_description}");
    return "Solution";
}}
        """
    else:
        mock_code = f"// Code for {task_description} in {language}"

    return {
        "language": language,
        "task": task_description,
        "code": mock_code,
        "metadata": {
            "generated_at": "2023-07-15T12:00:00Z",
            "model": "mock-code-generator",
        },
    }


@register_external_tool()
def execute_database_query(query: str, database: str = "default") -> Dict[str, Any]:
    """
    Execute a database query.

    Args:
        query: The SQL query to execute
        database: The database to query

    Returns:
        Query results and metadata
    """
    # This is a mock implementation
    logger.info(f"Executing query on {database} database: {query}")

    # In a real implementation, you would connect to a database and execute the query
    mock_results = {
        "columns": ["id", "name", "value"],
        "rows": [[1, "Item 1", 100], [2, "Item 2", 200], [3, "Item 3", 300]],
        "metadata": {"database": database, "query_time_ms": 42, "row_count": 3},
    }

    return mock_results


def main():
    """Main entry point."""
    logger.info("External Tools Example")

    # List all registered external tools
    tools = list_external_tools()
    logger.info(f"Registered external tools: {', '.join(tools)}")

    # Use an external tool directly
    search_tool = get_external_tool("search_documentation")
    if search_tool:
        results = search_tool("installation guide", max_results=2)
        logger.info(f"Search results: {json.dumps(results, indent=2)}")

    # Use another external tool
    code_tool = get_external_tool("generate_code_snippet")
    if code_tool:
        result = code_tool("python", "sort a list of numbers")
        logger.info(f"Generated code: {result['code']}")

    # Get external tools in OpenAI format
    openai_tools = get_external_tools_as_openai_format()
    logger.info(f"Number of tools in OpenAI format: {len(openai_tools)}")

    # Create an MCP server with the registered external tools
    logger.info("Creating MCP server with registered external tools")
    logger.info("These tools will be exposed to consuming LLMs through the MCP protocol")

    # Get all the external tool functions
    external_tools = [get_external_tool(name) for name in list_external_tools()]

    # Create the server
    server = create_mcp_server(
        server_name="external_tools_example_server",
        external_tools=external_tools,  # These tools will be exposed to consuming LLMs
        config={
            "debug": True,
            # Add LLM config if needed
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",  # Dummy value for Ollama
        },
    )

    logger.info("Server created successfully")
    logger.info("In a real application, you would call server.run() here")
    logger.info("When the server runs, external tools will be available to consuming LLMs")


if __name__ == "__main__":
    main()
