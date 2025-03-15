"""
Reflection loader for MCP.

This module provides functionality for loading and managing reflection templates
for the structured reflection loop in embedded reasoning.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Set

from fluent_mcp.core.prompt_loader import parse_markdown_with_frontmatter

logger = logging.getLogger("fluent_mcp.reflection_loader")


class ReflectionLoaderError(Exception):
    """Base exception for reflection loader errors."""

    pass


class InvalidApplicationModeError(ReflectionLoaderError):
    """Exception raised when the application mode is invalid."""

    pass


class ReflectionLoader:
    """
    Loader for reflection templates.

    Loads and manages reflection templates for the structured reflection loop.
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize a new reflection loader.

        Args:
            templates_dir: Directory containing reflection templates
        """
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "templates", "reflection")
        self.base_templates: Dict[str, Dict[str, Any]] = {}
        self.custom_templates: Dict[str, Dict[str, Any]] = {}
        self.tool_templates: Dict[str, Dict[str, Any]] = {}

        # Load templates if the directory exists
        if os.path.exists(self.templates_dir):
            logger.info(f"Loading reflection templates from {self.templates_dir}")
            self.load_templates()

    def load_templates(self) -> None:
        """
        Load all reflection templates from the templates directory.
        """
        # Load base templates
        self._load_base_templates()

        # Load custom templates
        self._load_custom_templates()

        # Load tool-specific templates
        self._load_tool_templates()

    def _load_base_templates(self) -> None:
        """
        Load base reflection templates.
        """
        base_dir = self.templates_dir
        if not os.path.exists(base_dir):
            logger.warning(f"Base templates directory does not exist: {base_dir}")
            return

        for file in os.listdir(base_dir):
            if file.endswith(".md") and file not in ["custom_reflection.md"]:
                file_path = os.path.join(base_dir, file)
                try:
                    template = parse_markdown_with_frontmatter(file_path)
                    name = template["config"]["name"]
                    self.base_templates[name] = template
                    logger.info(f"Loaded base template: {name} from {file_path}")
                except Exception as e:
                    logger.error(f"Error loading base template {file_path}: {str(e)}")

    def _load_custom_templates(self) -> None:
        """
        Load custom reflection templates.
        """
        base_dir = self.templates_dir
        custom_template_path = os.path.join(base_dir, "custom_reflection.md")

        if os.path.exists(custom_template_path):
            try:
                template = parse_markdown_with_frontmatter(custom_template_path)
                name = template["config"]["name"]
                self.custom_templates[name] = template
                logger.info(f"Loaded custom template: {name} from {custom_template_path}")
            except Exception as e:
                logger.error(f"Error loading custom template {custom_template_path}: {str(e)}")

    def _load_tool_templates(self) -> None:
        """
        Load tool-specific reflection templates.
        """
        tools_dir = os.path.join(self.templates_dir, "tools")
        if not os.path.exists(tools_dir):
            logger.warning(f"Tool templates directory does not exist: {tools_dir}")
            return

        for file in os.listdir(tools_dir):
            if file.endswith(".md"):
                file_path = os.path.join(tools_dir, file)
                try:
                    template = parse_markdown_with_frontmatter(file_path)
                    name = template["config"]["name"]
                    self.tool_templates[name] = template
                    logger.info(f"Loaded tool template: {name} from {file_path}")

                    # Log if tools are defined in the template
                    if "tools" in template["config"]:
                        tool_names = template["config"]["tools"]
                        logger.info(f"Template '{name}' applies to {len(tool_names)} tools: {', '.join(tool_names)}")
                except Exception as e:
                    logger.error(f"Error loading tool template {file_path}: {str(e)}")

    def get_reflection_template(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the combined reflection template for a specific tool.

        This method applies the hierarchical reflection system:
        1. Start with the base reflection template
        2. Apply custom reflection template if available
        3. Apply tool-specific reflection template if available and applicable

        Args:
            tool_name: Optional name of the tool to get the reflection template for

        Returns:
            A dictionary containing the combined reflection template
        """
        combined_template = {"content": "", "config": {}}

        # Start with the base reflection template
        base_template = self.base_templates.get("base_reflection")
        if base_template:
            combined_template["content"] = base_template["template"]
            combined_template["config"] = base_template["config"].copy()

        # Apply custom reflection template if available
        custom_template = self.custom_templates.get("custom_reflection")
        if custom_template:
            application_mode = custom_template["config"].get("application_mode", "append")
            if application_mode == "append":
                combined_template["content"] += "\n\n" + custom_template["template"]
            elif application_mode == "overwrite":
                combined_template["content"] = custom_template["template"]
            else:
                logger.warning(f"Invalid application mode '{application_mode}' in custom template")

            # Update config
            for key, value in custom_template["config"].items():
                if key != "application_mode":
                    combined_template["config"][key] = value

        # Apply tool-specific reflection template if available and applicable
        if tool_name:
            for template_name, template in self.tool_templates.items():
                if "tools" in template["config"] and tool_name in template["config"]["tools"]:
                    application_mode = template["config"].get("application_mode", "append")
                    if application_mode == "append":
                        combined_template["content"] += "\n\n" + template["template"]
                    elif application_mode == "overwrite":
                        combined_template["content"] = template["template"]
                    else:
                        logger.warning(
                            f"Invalid application mode '{application_mode}' in tool template {template_name}"
                        )

                    # Update config
                    for key, value in template["config"].items():
                        if key not in ["application_mode", "tools"]:
                            combined_template["config"][key] = value

                    logger.info(f"Applied tool-specific template '{template_name}' for tool '{tool_name}'")

        return combined_template

    def get_tool_use_template(self) -> Dict[str, Any]:
        """
        Get the tool use template.

        Returns:
            A dictionary containing the tool use template
        """
        tool_use_template = self.base_templates.get("tool_use")
        if not tool_use_template:
            logger.warning("Tool use template not found")
            return {"content": "", "config": {}}

        return {"content": tool_use_template["template"], "config": tool_use_template["config"].copy()}

    def format_reflection_template(self, template: Dict[str, Any], variables: Dict[str, Any]) -> str:
        """
        Format a reflection template with variables.

        Args:
            template: The reflection template dictionary
            variables: Variables to substitute in the template

        Returns:
            The formatted template content
        """
        content = template["content"]

        # Replace variables in the template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))

        return content

    def get_applicable_tool_templates(self, tool_names: List[str]) -> Set[str]:
        """
        Get the names of tool templates that apply to the given tools.

        Args:
            tool_names: List of tool names to check

        Returns:
            A set of template names that apply to the given tools
        """
        applicable_templates = set()

        for template_name, template in self.tool_templates.items():
            if "tools" in template["config"]:
                template_tools = set(template["config"]["tools"])
                if any(tool in template_tools for tool in tool_names):
                    applicable_templates.add(template_name)

        return applicable_templates
