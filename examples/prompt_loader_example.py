"""
Example usage of the prompt loader in Fluent MCP.

This script demonstrates how to:
1. Load prompts from a directory
2. Create an MCP server with loaded prompts
3. Access and use the loaded prompts
"""

import json
import logging
import os
import shutil
import tempfile
from typing import Any, Dict, List

from fluent_mcp import create_mcp_server
from fluent_mcp.core.prompt_loader import load_prompts

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prompt_loader_example")


def create_example_prompts(prompts_dir: str) -> None:
    """
    Create example prompt files in the specified directory.

    Args:
        prompts_dir: Directory to create prompt files in
    """
    # Create the directory if it doesn't exist
    os.makedirs(prompts_dir, exist_ok=True)

    # Create a basic prompt
    basic_prompt_path = os.path.join(prompts_dir, "basic_prompt.md")
    with open(basic_prompt_path, "w", encoding="utf-8") as f:
        f.write(
            """---
name: Basic Prompt
description: A simple example prompt
model: gpt-4
temperature: 0.7
---

This is a basic prompt template.

Please provide a response to the following question: {{question}}
"""
        )

    # Create a system prompt
    system_prompt_path = os.path.join(prompts_dir, "system_prompt.md")
    with open(system_prompt_path, "w", encoding="utf-8") as f:
        f.write(
            """---
name: System Prompt
description: A system prompt for setting the assistant's behavior
model: gpt-4
temperature: 0.2
role: system
---

You are a helpful AI assistant that specializes in {{domain}} knowledge.
Always provide accurate and helpful information to the user.
"""
        )

    # Create a prompt with more complex frontmatter
    complex_prompt_path = os.path.join(prompts_dir, "complex_prompt.md")
    with open(complex_prompt_path, "w", encoding="utf-8") as f:
        f.write(
            """---
name: Complex Prompt
description: A prompt with more complex frontmatter
model: gpt-4
temperature: 0.5
max_tokens: 500
stop_sequences:
  - "###"
  - "END"
parameters:
  format: json
  style: concise
tags:
  - example
  - complex
---

Generate a {{format}} response about {{topic}} in a {{style}} style.

Include the following information:
- Definition
- Key characteristics
- Common examples

###
"""
        )

    # Create a subdirectory with additional prompts
    subdir = os.path.join(prompts_dir, "category")
    os.makedirs(subdir, exist_ok=True)

    # Create a prompt in the subdirectory
    subdir_prompt_path = os.path.join(subdir, "specialized_prompt.md")
    with open(subdir_prompt_path, "w", encoding="utf-8") as f:
        f.write(
            """---
name: Specialized Prompt
description: A specialized prompt in a subdirectory
category: specialized
model: gpt-4
---

This is a specialized prompt for {{purpose}}.

Please provide detailed information about {{subject}} with a focus on {{aspect}}.
"""
        )


def main():
    """Main entry point."""
    logger.info("Prompt Loader Example")

    # Create a temporary directory for example prompts
    with tempfile.TemporaryDirectory() as temp_dir:
        prompts_dir = os.path.join(temp_dir, "prompts")

        # Create example prompts
        create_example_prompts(prompts_dir)
        logger.info(f"Created example prompts in {prompts_dir}")

        # Load prompts from the directory
        prompts = load_prompts(prompts_dir)
        logger.info(f"Loaded {len(prompts)} prompts from {prompts_dir}")

        # Print information about the loaded prompts
        for prompt in prompts:
            logger.info(f"Prompt: {prompt['config']['name']}")
            logger.info(f"  Path: {prompt['path']}")
            logger.info(f"  Description: {prompt['config']['description']}")
            logger.info(f"  Model: {prompt['config'].get('model', 'default')}")
            logger.info(f"  Temperature: {prompt['config'].get('temperature', 'default')}")
            logger.info(f"  Template length: {len(prompt['template'])} characters")
            logger.info("")

        # Create an MCP server with the loaded prompts
        logger.info("Creating MCP server with loaded prompts")

        # Create the server
        server = create_mcp_server(
            server_name="prompt_example_server",
            prompts=prompts,  # Pass the loaded prompts
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

        # Example of creating a server with prompts_dir parameter
        logger.info("Creating another server with prompts_dir parameter")

        server2 = create_mcp_server(
            server_name="prompt_dir_example_server",
            prompts_dir=prompts_dir,  # Pass the prompts directory
            config={
                "debug": True,
                "provider": "ollama",
                "model": "llama2",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
            },
        )

        logger.info("Second server created successfully")
        logger.info("In a real application, you would call server.run() here")


if __name__ == "__main__":
    main()
