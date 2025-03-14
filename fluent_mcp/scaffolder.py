"""
Scaffolding logic for MCP servers.

This module provides functions for scaffolding new MCP servers
with the necessary configuration and structure.
"""

import os
from typing import Any, Dict, Optional


def scaffold_server(
    output_dir: str,
    server_name: str,
    description: Optional[str] = None,
    author: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, str]:
    """
    Scaffold a new MCP server project with the given name and description.

    This creates a new directory with the server name and populates it with
    the necessary files to get started with a basic MCP server.

    Args:
        output_dir: The directory where the server project will be created
        server_name: The name of the server
        description: Optional description of the server
        author: Optional author of the server
        email: Optional email of the server

    Returns:
        A dictionary containing the path to the scaffolded server
    """
    # Create the server directory structure
    server_dir = os.path.join(output_dir, server_name)
    if os.path.exists(server_dir):
        raise ValueError(f"Directory {server_dir} already exists. Please choose a different name or location.")

    # Create the directory structure
    try:
        create_directory_structure(server_name, server_dir)
        create_server_files(server_name, server_dir)
        print(f"Successfully scaffolded server at: {server_dir}")
        return {"path": server_dir}
    except Exception as e:
        print(f"Error scaffolding server: {str(e)}")
        return {"path": ""}


def create_directory_structure(name: str, server_path: str) -> None:
    """
    Create the directory structure for a new MCP server.

    Args:
        name: The name of the server
        server_path: The path to the server directory
    """
    # Define the directory structure
    directories = [
        "",  # Root directory
        f"{name}",  # Server package
        f"{name}/tools",
        f"{name}/prompts",
        f"{name}/llm",
        f"{name}/tests",
    ]

    # Create directories
    for directory in directories:
        dir_path = os.path.join(server_path, directory)
        os.makedirs(dir_path, exist_ok=True)

    # Create empty __init__.py files
    init_files = [
        f"{name}/__init__.py",
        f"{name}/tools/__init__.py",
        f"{name}/llm/__init__.py",
        f"{name}/tests/__init__.py",
    ]

    for init_file in init_files:
        with open(os.path.join(server_path, init_file), "w") as f:
            f.write(f'"""\n{name.capitalize()} MCP server package.\n"""\n')


def create_server_files(name: str, server_path: str) -> None:
    """
    Create the server files for a new MCP server.

    Args:
        name: The name of the server
        server_path: The path to the server directory
    """
    try:
        # Create main.py content directly
        main_py_content = f'''"""
Main entry point for {name} MCP server.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from fluent_mcp import create_mcp_server

load_dotenv()

logging.basicConfig(level=os.getenv("FLUENT_LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting {name}...")
    
    # Load environment config
    config = {{
        "provider": os.getenv("FLUENT_LLM_PROVIDER"),
        "model": os.getenv("FLUENT_LLM_MODEL"),
        "base_url": os.getenv("FLUENT_LLM_BASE_URL"),
        "api_key": os.getenv("FLUENT_LLM_API_KEY"),
    }}

    # Example empty lists for now — to be filled with tools/prompts later
    embedded_tools = []
    external_tools = []
    prompts = []

    # Create and run MCP server
    mcp_server = create_mcp_server(
        server_name="{name}",
        embedded_tools=embedded_tools,
        external_tools=external_tools,
        prompts=prompts,
        config=config
    )

    mcp_server.run()

if __name__ == "__main__":
    main()
'''

        main_py_path = os.path.join(server_path, "main.py")
        print(f"Writing main.py to {main_py_path}")
        with open(main_py_path, "w") as f:
            f.write(main_py_content)

        # Create .env.example with updated environment variables
        env_example_content = """# Server configuration
FLUENT_LOG_LEVEL=INFO

# LLM configuration
FLUENT_LLM_PROVIDER=openai
FLUENT_LLM_MODEL=gpt-4
FLUENT_LLM_BASE_URL=
FLUENT_LLM_API_KEY=your_api_key_here
"""

        env_example_path = os.path.join(server_path, ".env.example")
        print(f"Writing .env.example to {env_example_path}")
        with open(env_example_path, "w") as f:
            f.write(env_example_content)
    except Exception as e:
        print(f"Error creating server files: {str(e)}")
        raise


def generate_config_template() -> Dict[str, Any]:
    """
    Generate a template configuration for a new MCP server.

    Returns:
        A dictionary containing the template configuration
    """
    return {
        "server": {"host": "localhost", "port": 8000, "debug": False},
        "llm": {"provider": "openai", "model": "gpt-4", "api_key": "${OPENAI_API_KEY}"},
        "tools": [
            # Example tool configurations
        ],
    }
