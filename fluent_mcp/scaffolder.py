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
    generate_cursor_rules: bool = False,
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
        generate_cursor_rules: Whether to generate Cursor rules for AI-assisted development

    Returns:
        A dictionary containing the path to the scaffolded server
    """
    # Determine if we're scaffolding directly in the current directory
    use_current_dir = server_name == "."

    # Set the server directory path
    if use_current_dir:
        server_dir = output_dir
        # Extract the server name from the current directory
        server_name = os.path.basename(os.path.abspath(output_dir))
    else:
        server_dir = os.path.join(output_dir, server_name)
        if os.path.exists(server_dir):
            raise ValueError(f"Directory {server_dir} already exists. Please choose a different name or location.")

    # Create the directory structure
    try:
        if not use_current_dir:
            # Only create the directory if we're not using the current directory
            os.makedirs(server_dir, exist_ok=True)

        create_directory_structure(server_name, server_dir)
        create_server_files(server_name, server_dir, description, author, email)
        create_config_files(server_name, server_dir)
        if generate_cursor_rules:
            create_cursor_rules(server_name, server_dir)
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
    # Check if we're scaffolding directly in the current directory
    use_current_dir = server_path == "." or os.path.samefile(server_path, ".")

    # Define the directory structure
    directories = [
        "",  # Root directory (only needed if not using current directory)
        f"{name}",  # Server package
        f"{name}/tools",
        f"{name}/tools/embedded",  # Embedded tools directory
        f"{name}/tools/external",  # External tools directory
        f"{name}/prompts",
        f"{name}/prompts/system_prompts",  # System prompts directory
        f"{name}/llm",
        f"{name}/tests",
    ]

    # Create directories
    for directory in directories:
        # Skip the root directory if we're using the current directory
        if directory == "" and use_current_dir:
            continue

        dir_path = os.path.join(server_path, directory)
        os.makedirs(dir_path, exist_ok=True)

        # Create __init__.py files in Python package directories
        if directory != "":
            init_file = os.path.join(server_path, directory, "__init__.py")
            with open(init_file, "w") as f:
                f.write(f'"""Package for {directory}."""\n')

    # Create special __init__.py files for tools directories
    embedded_init = os.path.join(server_path, f"{name}/tools/embedded", "__init__.py")
    with open(embedded_init, "w") as f:
        f.write(f'"""Embedded tools for {name}.\n\nThese tools are only available to the embedded LLM."""\n')

    external_init = os.path.join(server_path, f"{name}/tools/external", "__init__.py")
    with open(external_init, "w") as f:
        f.write(f'"""External tools for {name}.\n\nThese tools are exposed to consuming LLMs."""\n')


def create_server_files(
    name: str,
    server_path: str,
    description: Optional[str] = None,
    author: Optional[str] = None,
    email: Optional[str] = None,
) -> None:
    """
    Create the server files for a new MCP server.

    Args:
        name: The name of the server
        server_path: The path to the server directory
        description: Optional description of the server
        author: Optional author of the server
        email: Optional email of the server
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

        # Create pyproject.toml
        # Use provided description or default
        project_description = description or f"A Model Context Protocol (MCP) server built with fluent_mcp"
        # Use provided author or default
        project_author = author or "Your Name"
        # Use provided email or default
        project_email = email or "your.email@example.com"

        pyproject_toml_content = f"""[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "{project_description}"
readme = "README.md"
authors = [
    {{name = "{project_author}", email = "{project_email}"}}
]
license = {{text = "MIT"}}
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
requires-python = ">=3.8"
dependencies = [
    "fluent_mcp>=0.1.0",
    "python-dotenv>=0.19.0",
    "httpx>=0.23.0",
    "pydantic>=1.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.18.0",
    "black>=22.1.0",
    "isort>=5.10.0",
    "flake8>=4.0.0",
    "mypy>=0.931",
    "pre-commit>=2.17.0",
]

[tool.black]
line-length = 100
target-version = ["py38"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
"""

        pyproject_toml_path = os.path.join(server_path, "pyproject.toml")
        print(f"Writing pyproject.toml to {pyproject_toml_path}")
        with open(pyproject_toml_path, "w") as f:
            f.write(pyproject_toml_content)

        # Create a basic README.md file
        readme_content = f"""# {name.capitalize()}

{project_description}

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

1. Copy `.env.example` to `.env` and fill in your API keys
2. Run the server:

```bash
python main.py
```

## Development

This project uses pytest for testing:

```bash
pytest
```

And black, isort, and flake8 for code formatting:

```bash
black .
isort .
flake8
```

You can also set up pre-commit hooks to automatically run these checks:

```bash
pre-commit install
```
"""

        readme_path = os.path.join(server_path, "README.md")
        print(f"Writing README.md to {readme_path}")
        with open(readme_path, "w") as f:
            f.write(readme_content)

    except Exception as e:
        print(f"Error creating server files: {str(e)}")
        raise


def create_config_files(name: str, server_path: str) -> None:
    """
    Create configuration files for code quality tools.

    Args:
        name: The name of the server
        server_path: The path to the server directory
    """
    try:
        # Create .flake8 configuration
        flake8_content = """[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
# E203 whitespace before ':' (conflicts with black)
# W503 line break before binary operator (conflicts with black)
ignore = E203,W503
"""

        flake8_path = os.path.join(server_path, ".flake8")
        print(f"Writing .flake8 to {flake8_path}")
        with open(flake8_path, "w") as f:
            f.write(flake8_content)

        # Create .isort.cfg configuration
        isort_content = (
            """[settings]
profile = black
line_length = 100
multi_line_output = 3
include_trailing_comma = True
force_grid_wrap = 0
use_parentheses = True
ensure_newline_before_comments = True
known_first_party = """
            + name
            + """
sections = FUTURE,STDLIB,THIRDPARTY,FIRSTPARTY,LOCALFOLDER
"""
        )

        isort_path = os.path.join(server_path, ".isort.cfg")
        print(f"Writing .isort.cfg to {isort_path}")
        with open(isort_path, "w") as f:
            f.write(isort_content)

        # Create .pre-commit-config.yaml
        pre_commit_content = """repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-toml
    -   id: debug-statements

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black
        args: [--line-length=100]

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black", "--line-length", "100"]

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]
        args: [--max-line-length=100, --ignore=E203,W503]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests]
"""

        pre_commit_path = os.path.join(server_path, ".pre-commit-config.yaml")
        print(f"Writing .pre-commit-config.yaml to {pre_commit_path}")
        with open(pre_commit_path, "w") as f:
            f.write(pre_commit_content)

    except Exception as e:
        print(f"Error creating configuration files: {str(e)}")
        raise


def create_cursor_rules(name: str, server_path: str) -> None:
    """
    Create Cursor rule files for AI-assisted development.

    Args:
        name: The name of the server
        server_path: The path to the server directory
    """
    try:
        # Create .cursor/rules directory
        cursor_rules_dir = os.path.join(server_path, ".cursor", "rules")
        os.makedirs(cursor_rules_dir, exist_ok=True)

        print(f"Creating Cursor rules in {cursor_rules_dir}")

        # 1. General coding standards rule
        general_coding_standards = f"""---
description: Provides guidance on general Python coding standards for this project
globs: ["**/*.py"]
alwaysApply: true
---

# General Coding Standards

## Python Coding Standards

Follow these coding standards for all Python files in this project:

### Code Style
- Follow PEP 8 with customizations in .flake8
- Maximum line length is 100 characters
- Use 4 spaces for indentation (no tabs)
- Use snake_case for variables and functions
- Use CamelCase for classes
- Use UPPER_CASE for constants

### Imports
- Sort imports using isort with the black profile
- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. First-party imports ({name})
  4. Local imports

### Documentation
- All modules, classes, and functions should have docstrings
- Use Google-style docstrings
- Include type hints for all function parameters and return values
- Document exceptions that may be raised

### Error Handling
- Use specific exception types from fluent_mcp.core.error_handling
- Implement proper error handling to prevent cascading failures
- Log errors appropriately using the logger
- Return clear error messages that enable debugging

### Testing
- Write unit tests for all functions
- Use pytest for testing
- Test both success and error cases
"""

        # 2. Two-tier architecture rule
        two_tier_architecture = f'''---
description: Enforces the two-tier LLM architecture pattern with embedded and consuming LLMs
globs: ["**/*.py"]
alwaysApply: true
---

# Two-Tier LLM Architecture

## Overview

Fluent MCP implements a powerful two-tier architecture:

### Embedded LLM
- An internal LLM that performs complex reasoning and multi-step tasks
- Used for internal processing within tools
- Not directly exposed to external systems
- Typically smaller, more focused models

### Consuming LLM
- The external LLM (like Claude, GPT-4) that interacts with your MCP server
- Makes requests to your external tools
- Receives simplified responses that hide implementation complexity

### Implementation Guidelines

When implementing features that require LLM reasoning:

1. Determine if the reasoning should be done by the embedded LLM or exposed to the consuming LLM
2. For complex multi-step reasoning, use the embedded LLM via `run_embedded_reasoning()`
3. Keep the interface to consuming LLMs simple and focused on their specific needs
4. Don't expose internal implementation details to consuming LLMs

### Example Pattern

```python
# External tool that uses embedded reasoning internally
@register_external_tool()
async def research_question(question: str) -> dict:
    """Research a question and provide an answer (exposed to consuming LLMs)."""
    
    # Define system prompt with access to embedded tools
    system_prompt = """
    You are a research assistant with access to internal tools.
    Use these tools to thoroughly research the question.
    """
    
    # Run embedded reasoning (offloading complex logic)
    result = await run_embedded_reasoning(
        system_prompt=system_prompt,
        user_prompt=f"Research this question: {{question}}"
    )
    
    # Return a clean, structured response (hiding complexity)
    return {{
        "answer": result["content"],
        "confidence": 0.9,
        "sources": ["source1", "source2"]
    }}
```
'''

        # 3. Embedded tools rule
        embedded_tools = f'''---
description: Guidelines for implementing embedded tools that are only available to the embedded LLM
globs: ["{name}/tools/embedded/**/*.py"]
alwaysApply: true
---

# Embedded Tools Guidelines

## Overview

Embedded tools are ONLY available to the embedded LLM, not exposed externally.

### Key Principles

1. Embedded tools should be focused on specific tasks
2. They should be registered with the `@embedded_tool` or `@register_embedded_tool()` decorator
3. They should be placed in the `{name}/tools/embedded/` directory
4. They should have clear, descriptive names and docstrings
5. They should use type hints for all parameters and return values

### Example

```python
from fluent_mcp.core.tool_registry import embedded_tool

@embedded_tool
def search_database(query: str) -> list:
    """
    Search the database for information.
    
    Args:
        query: The search query
        
    Returns:
        A list of search results
    """
    # Implementation...
    return ["result1", "result2"]
```

### Best Practices

- Keep embedded tools focused on a single responsibility
- Use descriptive names that clearly indicate what the tool does
- Provide detailed docstrings explaining the tool's purpose and parameters
- Handle errors gracefully and return meaningful error messages
- Log important information for debugging
- Return structured data that is easy for the embedded LLM to process
'''

        # 4. External tools rule
        external_tools = f'''---
description: Guidelines for implementing external tools that are exposed to consuming LLMs
globs: ["{name}/tools/external/**/*.py"]
alwaysApply: true
---

# External Tools Guidelines

## Overview

External tools are exposed to consuming LLMs through the MCP protocol.

### Key Principles

1. External tools should present a simple, user-friendly interface
2. They should be registered with the `@external_tool` or `@register_external_tool()` decorator
3. They should be placed in the `{name}/tools/external/` directory
4. They may use embedded reasoning internally to perform complex tasks
5. They should have clear, descriptive names and docstrings
6. They should use type hints for all parameters and return values

### Example

```python
from fluent_mcp.core.tool_registry import external_tool
from fluent_mcp.core.llm_client import run_embedded_reasoning

@external_tool
async def research_question(question: str) -> dict:
    """
    Research a question and provide a comprehensive answer.
    
    Args:
        question: The question to research
        
    Returns:
        A dictionary containing the answer and metadata
    """
    # Define system prompt for embedded reasoning
    system_prompt = """
    You are a research assistant with access to internal tools.
    Use these tools to thoroughly research the question.
    """
    
    # Run embedded reasoning
    result = await run_embedded_reasoning(
        system_prompt=system_prompt,
        user_prompt=f"Research this question: {{question}}"
    )
    
    # Return a clean, structured response
    return {{
        "answer": result["content"],
        "confidence": 0.9,
        "sources": ["source1", "source2"]
    }}
```

### Best Practices

- Keep the interface simple and focused on the user's needs
- Hide implementation complexity from the consuming LLM
- Use embedded reasoning for complex multi-step tasks
- Return structured data that is easy for the consuming LLM to process
- Provide clear error messages that help the user understand what went wrong
- Document the tool's purpose, parameters, and return values clearly
'''

        # 5. Prompt engineering rule
        prompt_engineering = f"""---
description: Guidelines for writing effective prompts with proper frontmatter
globs: ["{name}/prompts/**/*.md", "{name}/prompts/**/*.yaml"]
alwaysApply: true
---

# Prompt Engineering Guidelines

## Overview

Prompts are a critical part of working with LLMs. Follow these guidelines for creating effective prompts.

### Prompt Structure

1. Store prompts in the `{name}/prompts/` directory, organized by purpose
2. Use frontmatter for tool and configuration specifications
3. Include a clear description of the prompt's purpose
4. Specify which tools the prompt should have access to

### Example

```markdown
---
name: research_prompt
description: A prompt for the embedded LLM to perform research
model: gpt-4
temperature: 0.3
tools:
  - search_database
  - analyze_data
---
You are a research assistant with access to internal tools.
Use the available tools to thoroughly research the given question.
```

### Best Practices

- Be specific about the role and capabilities of the LLM
- Clearly define the task and expected output format
- Provide examples of good responses when helpful
- Keep prompts focused on a single responsibility
- Use a consistent style across similar prompts
- Organize prompts by their purpose and function
- Use lower temperatures (0.0-0.3) for more deterministic tasks
- Use higher temperatures (0.5-0.7) for more creative tasks
"""

        # Write the rule files with explicit UTF-8 encoding and Unix line endings
        for rule_name, content in [
            ("general-coding-standards.mdc", general_coding_standards),
            ("two-tier-architecture.mdc", two_tier_architecture),
            ("embedded-tools.mdc", embedded_tools),
            ("external-tools.mdc", external_tools),
            ("prompt-engineering.mdc", prompt_engineering),
        ]:
            file_path = os.path.join(cursor_rules_dir, rule_name)
            # First, write the frontmatter separately to ensure it's formatted correctly
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                # Write the frontmatter
                frontmatter_lines = content.split("---\n", 2)
                if len(frontmatter_lines) >= 3:
                    f.write("---\n")
                    f.write(frontmatter_lines[1])
                    f.write("---\n\n")
                    # Write the content
                    f.write(frontmatter_lines[2])
                else:
                    # Fallback if the splitting didn't work as expected
                    f.write(content)

        print(f"Successfully created Cursor rules in {cursor_rules_dir}")

    except Exception as e:
        print(f"Error creating Cursor rules: {str(e)}")
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
