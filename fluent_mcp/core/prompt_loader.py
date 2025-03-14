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
                    except PromptLoaderError as e:
                        logger.warning(f"Skipping prompt file {file_path}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Unexpected error loading prompt {file_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {str(e)}")

    logger.info(f"Loaded {len(prompts)} prompts from {directory}")
    return prompts
