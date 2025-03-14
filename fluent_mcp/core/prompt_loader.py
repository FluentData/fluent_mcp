"""
Prompt loader for MCP.

This module provides functionality for loading and managing prompts
for language models.
"""

import os
import json
from typing import Dict, Any, Optional


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
        
        # TODO: Load prompts from directory if it exists
        if os.path.exists(self.prompt_dir):
            print(f"Loading prompts from {self.prompt_dir}")
        
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
            with open(prompt_path, "r") as f:
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
            with open(template_path, "r") as f:
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
