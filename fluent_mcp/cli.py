"""
Command-line interface for Fluent MCP.

This module provides CLI commands for scaffolding and managing MCP servers.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

from fluent_mcp.scaffolder import scaffold_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fluent_mcp.cli")


def is_directory_suitable_for_direct_scaffolding(directory: str = ".") -> bool:
    """
    Check if the directory is suitable for direct scaffolding.

    A directory is suitable if it's empty or only contains spec files
    (instructions.md and/or spec.md).

    Args:
        directory: The directory to check (defaults to current directory)

    Returns:
        True if the directory is suitable for direct scaffolding, False otherwise
    """
    # Get all files and directories in the specified directory
    contents = os.listdir(directory)

    # If the directory is empty, it's suitable
    if not contents:
        return True

    # Check if the directory only contains spec files
    allowed_files = ["instructions.md", "spec.md"]
    for item in contents:
        if item not in allowed_files:
            return False

    return True


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fluent MCP - A modern package for MCP servers")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scaffold command (legacy)
    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold a new MCP server (legacy)")
    scaffold_parser.add_argument("name", help="Name of the server")
    scaffold_parser.add_argument("--config", help="Path to config file")

    # New command
    new_parser = subparsers.add_parser("new", help="Create a new MCP server")
    new_parser.add_argument("name", help="Name of the server")
    new_parser.add_argument("--config", help="Path to config file")
    new_parser.add_argument(
        "--new-dir",
        "-d",
        action="store_true",
        help="Force creating a new directory even if the current directory is empty or only has spec files",
    )
    new_parser.add_argument(
        "--cursor",
        "-c",
        action="store_true",
        help="Generate Cursor rules for AI-assisted development according to Fluent MCP's architectural patterns",
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)

    if not parsed_args.command:
        print("Please specify a command. Use --help for more information.")
        return 1

    if parsed_args.command == "scaffold" or parsed_args.command == "new":
        print(f"Creating new MCP server: {parsed_args.name}")

        # For the "new" command, implement smart directory detection
        if parsed_args.command == "new":
            # Check if the current directory is suitable for direct scaffolding
            is_suitable = is_directory_suitable_for_direct_scaffolding()

            # Determine the output directory and server name based on the check and the --new-dir flag
            if is_suitable and not getattr(parsed_args, "new_dir", False):
                logger.info(
                    "Current directory is empty or only contains spec files. Scaffolding directly in this directory."
                )
                output_dir = "."
                server_name = "."  # Special value to indicate using the current directory
            else:
                if getattr(parsed_args, "new_dir", False):
                    logger.info("--new-dir flag specified. Creating a new directory for the server.")
                else:
                    logger.info("Current directory contains other files. Creating a new directory for the server.")
                output_dir = "."
                server_name = parsed_args.name  # Create a new directory with the specified name
        else:
            # For the legacy "scaffold" command, use the original behavior
            output_dir = "."
            server_name = parsed_args.name

        # Get the cursor flag value
        generate_cursor_rules = getattr(parsed_args, "cursor", False)
        if generate_cursor_rules:
            logger.info("--cursor flag specified. Will generate Cursor rules for AI-assisted development.")

        # Call scaffold_server with the correct parameters
        result = scaffold_server(
            output_dir=output_dir,
            server_name=server_name,
            description=f"MCP server for {parsed_args.name}",
            generate_cursor_rules=generate_cursor_rules,
        )

        if result and "path" in result and result["path"]:
            print(f"Server created at: {result['path']}")
            return 0
        else:
            print("Failed to create server")
            return 1
    else:
        print(f"Unknown command: {parsed_args.command}")
        print("Please specify a valid command. Use --help for more information.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
