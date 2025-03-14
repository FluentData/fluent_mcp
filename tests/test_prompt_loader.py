"""
Tests for the prompt loader functionality.
"""

import os
import tempfile
import unittest
import logging
from typing import Dict, Any, List
import shutil

from fluent_mcp.core.prompt_loader import (
    load_prompts,
    parse_markdown_with_frontmatter,
    PromptLoaderError,
    InvalidFrontmatterError,
    MissingRequiredFieldError
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_prompt_loader")

class TestPromptLoader(unittest.TestCase):
    """Test cases for the prompt loader functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test prompts
        self.test_dir = tempfile.mkdtemp()
        
        # Create some test prompt files
        self.valid_prompt = os.path.join(self.test_dir, "valid_prompt.md")
        with open(self.valid_prompt, "w", encoding="utf-8") as f:
            f.write("""---
name: Test Prompt
description: A test prompt for unit testing
model: gpt-4
temperature: 0.7
tags:
  - test
  - example
---

This is a test prompt template.

You should respond with a greeting to {{name}}.
""")
        
        self.missing_fields_prompt = os.path.join(self.test_dir, "missing_fields.md")
        with open(self.missing_fields_prompt, "w", encoding="utf-8") as f:
            f.write("""---
name: Incomplete Prompt
# Missing description field
---

This prompt is missing required fields.
""")
        
        self.invalid_yaml_prompt = os.path.join(self.test_dir, "invalid_yaml.md")
        with open(self.invalid_yaml_prompt, "w", encoding="utf-8") as f:
            f.write("""---
name: Invalid YAML
description: This has invalid YAML
tags: [test, example  # Missing closing bracket
---

This prompt has invalid YAML in the frontmatter.
""")
        
        self.no_frontmatter_prompt = os.path.join(self.test_dir, "no_frontmatter.md")
        with open(self.no_frontmatter_prompt, "w", encoding="utf-8") as f:
            f.write("""This prompt has no frontmatter at all.
""")
        
        # Create a subdirectory with more prompts
        self.subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.subdir)
        
        self.subdir_prompt = os.path.join(self.subdir, "subdir_prompt.md")
        with open(self.subdir_prompt, "w", encoding="utf-8") as f:
            f.write("""---
name: Subdirectory Prompt
description: A prompt in a subdirectory
---

This prompt is in a subdirectory.
""")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_parse_markdown_with_frontmatter(self):
        """Test parsing a markdown file with frontmatter."""
        # Test valid prompt
        prompt = parse_markdown_with_frontmatter(self.valid_prompt)
        self.assertEqual(prompt["config"]["name"], "Test Prompt")
        self.assertEqual(prompt["config"]["description"], "A test prompt for unit testing")
        self.assertEqual(prompt["config"]["model"], "gpt-4")
        self.assertEqual(prompt["config"]["temperature"], 0.7)
        self.assertEqual(prompt["config"]["tags"], ["test", "example"])
        self.assertIn("This is a test prompt template.", prompt["template"])
        self.assertIn("You should respond with a greeting to {{name}}.", prompt["template"])
        
        # Test missing fields
        with self.assertRaises(MissingRequiredFieldError):
            parse_markdown_with_frontmatter(self.missing_fields_prompt)
        
        # Test invalid YAML
        with self.assertRaises(InvalidFrontmatterError):
            parse_markdown_with_frontmatter(self.invalid_yaml_prompt)
        
        # Test no frontmatter
        with self.assertRaises(InvalidFrontmatterError):
            parse_markdown_with_frontmatter(self.no_frontmatter_prompt)
    
    def test_load_prompts(self):
        """Test loading prompts from a directory."""
        prompts = load_prompts(self.test_dir)
        
        # We should have 2 valid prompts (valid_prompt.md and subdir/subdir_prompt.md)
        self.assertEqual(len(prompts), 2)
        
        # Check that we have the expected prompts
        prompt_names = [p["config"]["name"] for p in prompts]
        self.assertIn("Test Prompt", prompt_names)
        self.assertIn("Subdirectory Prompt", prompt_names)
        
        # Invalid prompts should be skipped
        self.assertNotIn("Incomplete Prompt", prompt_names)
        self.assertNotIn("Invalid YAML", prompt_names)
        
        # Test loading from a subdirectory
        subdir_prompts = load_prompts(self.subdir)
        self.assertEqual(len(subdir_prompts), 1)
        self.assertEqual(subdir_prompts[0]["config"]["name"], "Subdirectory Prompt")
        
        # Test loading from a non-existent directory
        non_existent_dir = os.path.join(self.test_dir, "non_existent")
        empty_prompts = load_prompts(non_existent_dir)
        self.assertEqual(len(empty_prompts), 0)

if __name__ == "__main__":
    unittest.main() 