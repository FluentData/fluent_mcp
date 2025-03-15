"""
Prompt loader for MCP.

This module provides functionality for loading and managing prompts
for language models.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("fluent_mcp.prompt_loader")

# Regular expression for extracting YAML frontmatter
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class PromptLoaderError(Exception):
    """Base exception for prompt loader errors."""

    pass


class InvalidFrontmatterError(PromptLoaderError):
    """Exception raised when frontmatter is invalid."""

    pass


class MissingRequiredFieldError(PromptLoaderError):
    """Exception raised when a required field is missing."""

    pass


class InvalidToolsFormatError(PromptLoaderError):
    """Exception raised when the tools list format is invalid."""

    pass


class InvalidBudgetFormatError(PromptLoaderError):
    """Exception raised when the budget configuration format is invalid."""

    pass


class PromptLoader:
    """
    Loader for LLM prompts.

    Loads prompts from files or templates and manages prompt variables.
    """

    def __init__(self, prompt_dir: Optional[str] = None):
        """
        Initialize a new prompt loader.

        Args:
            prompt_dir: Directory containing prompt files
        """
        self.prompt_dir = prompt_dir or os.path.join(os.getcwd(), "prompts")
        self.prompts: Dict[str, str] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}

        # Load prompts from directory if it exists
        if os.path.exists(self.prompt_dir):
            logger.info(f"Loading prompts from {self.prompt_dir}")
            self.load_prompts(self.prompt_dir)

    def load_prompt(self, name: str) -> Optional[str]:
        """
        Load a prompt by name.

        Args:
            name: The name of the prompt

        Returns:
            The prompt text, or None if not found
        """
        # Check if already loaded
        if name in self.prompts:
            return self.prompts[name]

        # Try to load from file
        prompt_path = os.path.join(self.prompt_dir, f"{name}.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                self.prompts[name] = prompt
                return prompt

        return None

    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a prompt template by name.

        Args:
            name: The name of the template

        Returns:
            The template, or None if not found
        """
        # Check if already loaded
        if name in self.templates:
            return self.templates[name]

        # Try to load from file
        template_path = os.path.join(self.prompt_dir, f"{name}.json")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = json.load(f)
                self.templates[name] = template
                return template

        return None

    def format_prompt(self, prompt: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt with variables.

        Args:
            prompt: The prompt text
            variables: Variables to substitute in the prompt

        Returns:
            The formatted prompt
        """
        # TODO: Implement more sophisticated formatting
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt


def parse_markdown_with_frontmatter(file_path: str) -> Dict[str, Any]:
    """
    Parse a markdown file with YAML frontmatter.

    Args:
        file_path: Path to the markdown file

    Returns:
        A dictionary containing the parsed frontmatter and template content

    Raises:
        InvalidFrontmatterError: If the frontmatter is invalid
        MissingRequiredFieldError: If a required field is missing
        InvalidToolsFormatError: If the tools list format is invalid
        InvalidBudgetFormatError: If the budget configuration format is invalid
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter
        frontmatter_match = FRONTMATTER_PATTERN.match(content)
        if not frontmatter_match:
            raise InvalidFrontmatterError(f"No valid frontmatter found in {file_path}")

        frontmatter_yaml = frontmatter_match.group(1)
        template_content = content[frontmatter_match.end() :]

        # Parse frontmatter
        try:
            config = yaml.safe_load(frontmatter_yaml)
            if not isinstance(config, dict):
                raise InvalidFrontmatterError(f"Frontmatter in {file_path} is not a valid YAML object")
        except yaml.YAMLError as e:
            raise InvalidFrontmatterError(f"Invalid YAML in frontmatter of {file_path}: {str(e)}")

        # Check for required fields
        required_fields = ["name", "description"]
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise MissingRequiredFieldError(
                f"Missing required fields in frontmatter of {file_path}: {', '.join(missing_fields)}"
            )

        # Validate tools list if present
        if "tools" in config:
            tools = config["tools"]
            if not isinstance(tools, list):
                raise InvalidToolsFormatError(f"Tools in frontmatter of {file_path} must be a list")

            for tool in tools:
                if not isinstance(tool, str):
                    raise InvalidToolsFormatError(f"Each tool in frontmatter of {file_path} must be a string")

        # Validate budget configuration if present
        if "budget" in config:
            budget = config["budget"]
            if not isinstance(budget, dict):
                raise InvalidBudgetFormatError(f"Budget in frontmatter of {file_path} must be a dictionary")

            for tool_name, tool_budget in budget.items():
                if not isinstance(tool_budget, dict):
                    raise InvalidBudgetFormatError(
                        f"Budget for tool '{tool_name}' in frontmatter of {file_path} must be a dictionary"
                    )

                # Check for valid budget fields
                for field, value in tool_budget.items():
                    if field not in ["hourly_limit", "daily_limit"]:
                        logger.warning(
                            f"Unknown budget field '{field}' for tool '{tool_name}' in frontmatter of {file_path}"
                        )

                    if not isinstance(value, int) or value <= 0:
                        raise InvalidBudgetFormatError(
                            f"Budget limit '{field}' for tool '{tool_name}' in frontmatter of {file_path} "
                            f"must be a positive integer"
                        )

        # Create the prompt dictionary
        relative_path = os.path.relpath(file_path)
        prompt = {
            "path": relative_path,
            "config": config,
            "template": template_content.strip(),
        }

        return prompt

    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise


def load_prompts(directory: str) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for .md files and parse them as prompts.

    Args:
        directory: Directory to scan for prompt files

    Returns:
        A list of prompts as dictionaries
    """
    prompts = []
    logger.info(f"Loading prompts from directory: {directory}")

    try:
        # Walk through the directory recursively
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    try:
                        prompt = parse_markdown_with_frontmatter(file_path)
                        prompts.append(prompt)
                        logger.info(f"Loaded prompt: {prompt['config'].get('name')} from {prompt['path']}")

                        # Log if tools are defined in the prompt
                        if "tools" in prompt["config"]:
                            tool_names = prompt["config"]["tools"]
                            logger.info(
                                f"Prompt '{prompt['config'].get('name')}' has {len(tool_names)} tools defined: {', '.join(tool_names)}"
                            )
                    except PromptLoaderError as e:
                        logger.warning(f"Skipping prompt file {file_path}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Unexpected error loading prompt {file_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {str(e)}")

    logger.info(f"Loaded {len(prompts)} prompts from {directory}")
    return prompts


def get_prompt_tools(prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get the embedded tool definitions for a prompt.

    This function looks up each tool name specified in the prompt's frontmatter
    in the embedded tools registry and returns the corresponding tool definitions
    in OpenAI function calling format.

    Args:
        prompt: A prompt dictionary from the prompt loader

    Returns:
        A list of tool definitions in OpenAI function calling format,
        or an empty list if no tools are specified in the frontmatter
    """
    from fluent_mcp.core.tool_registry import get_embedded_tool, get_tools_as_openai_format

    logger.debug(f"Getting tools for prompt: {prompt['config'].get('name')}")

    # If no tools are specified in the frontmatter, return an empty list
    if "tools" not in prompt["config"]:
        logger.debug(f"No tools specified in prompt: {prompt['config'].get('name')}")
        return []

    tool_names = prompt["config"]["tools"]
    if not tool_names:
        logger.debug(f"Empty tools list in prompt: {prompt['config'].get('name')}")
        return []

    logger.info(f"Looking up {len(tool_names)} tools for prompt: {prompt['config'].get('name')}")

    # Get all available tools in OpenAI format
    all_tools = get_tools_as_openai_format()
    all_tools_dict = {tool["function"]["name"]: tool for tool in all_tools}

    # Look up each tool by name
    prompt_tools = []
    for tool_name in tool_names:
        if tool_name in all_tools_dict:
            prompt_tools.append(all_tools_dict[tool_name])
            logger.debug(f"Found tool: {tool_name}")
        else:
            logger.warning(f"Tool not found in registry: {tool_name}")

    logger.info(f"Found {len(prompt_tools)} tools for prompt: {prompt['config'].get('name')}")
    return prompt_tools


def get_prompt_budget(prompt: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Get the budget configuration for a prompt.

    This function extracts the budget configuration from the prompt's frontmatter.

    Args:
        prompt: A prompt dictionary from the prompt loader

    Returns:
        A dictionary containing the budget configuration,
        or an empty dictionary if no budget is specified in the frontmatter
    """
    logger.debug(f"Getting budget configuration for prompt: {prompt['config'].get('name')}")

    # If no budget is specified in the frontmatter, return an empty dictionary
    if "budget" not in prompt["config"]:
        logger.debug(f"No budget specified in prompt: {prompt['config'].get('name')}")
        return {}

    budget = prompt["config"]["budget"]
    if not budget:
        logger.debug(f"Empty budget configuration in prompt: {prompt['config'].get('name')}")
        return {}

    logger.info(f"Found budget configuration for {len(budget)} tools in prompt: {prompt['config'].get('name')}")

    # Return the budget configuration
    return budget
