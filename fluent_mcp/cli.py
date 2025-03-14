"""
Command-line interface for Fluent MCP.

This module provides CLI commands for scaffolding and managing MCP servers.
"""

import argparse
import sys
from typing import List, Optional

from fluent_mcp.scaffolder import scaffold_server


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fluent MCP - A modern package for MCP servers"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scaffold command (legacy)
    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold a new MCP server (legacy)")
    scaffold_parser.add_argument("name", help="Name of the server")
    scaffold_parser.add_argument("--config", help="Path to config file")
    
    # New command
    new_parser = subparsers.add_parser("new", help="Create a new MCP server")
    new_parser.add_argument("name", help="Name of the server")
    new_parser.add_argument("--config", help="Path to config file")
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)
    
    if not parsed_args.command:
        print("Please specify a command. Use --help for more information.")
        return 1
    
    if parsed_args.command == "scaffold":
        print(f"Scaffolding server: {parsed_args.name}")
        result = scaffold_server(name=parsed_args.name, config_path=parsed_args.config)
        return 0 if result else 1
    elif parsed_args.command == "new":
        print(f"Creating new MCP server: {parsed_args.name}")
        result = scaffold_server(name=parsed_args.name, config_path=parsed_args.config)
        return 0 if result else 1
    else:
        print(f"Unknown command: {parsed_args.command}")
        print("Please specify a valid command. Use --help for more information.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
