"""
Tests for the scaffolder module.
"""

import os
import tempfile
import unittest
from unittest.mock import mock_open, patch

from fluent_mcp.scaffolder import generate_config_template, scaffold_server


class TestScaffolder(unittest.TestCase):
    """Test cases for the scaffolder module."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_generate_config_template(self):
        """Test generating a config template."""
        template = generate_config_template()

        # Verify the template structure
        self.assertIsInstance(template, dict)
        self.assertIn("server", template)
        self.assertIn("llm", template)
        self.assertIn("tools", template)

    @patch("fluent_mcp.scaffolder.create_directory_structure")
    @patch("fluent_mcp.scaffolder.create_server_files")
    @patch("fluent_mcp.scaffolder.create_config_files")
    @patch("fluent_mcp.scaffolder.create_cursor_rules")
    def test_scaffold_server(
        self,
        mock_create_cursor_rules,
        mock_create_config_files,
        mock_create_server_files,
        mock_create_directory_structure,
    ):
        """Test scaffolding a server."""
        server_name = "test_server"
        expected_path = os.path.join(os.getcwd(), server_name)

        # Call the function
        result = scaffold_server(output_dir=os.getcwd(), server_name=server_name)

        # Verify the function returned a result with a path
        self.assertIsInstance(result, dict)
        self.assertIn("path", result)

        # Verify the mocked functions were called
        mock_create_directory_structure.assert_called_once_with(server_name, expected_path)
        mock_create_server_files.assert_called_once()
        mock_create_config_files.assert_called_once_with(server_name, expected_path)
        mock_create_cursor_rules.assert_not_called()

    @patch("fluent_mcp.scaffolder.create_directory_structure")
    @patch("fluent_mcp.scaffolder.create_server_files")
    @patch("fluent_mcp.scaffolder.create_config_files")
    @patch("fluent_mcp.scaffolder.create_cursor_rules")
    def test_scaffold_server_with_config(
        self,
        mock_create_cursor_rules,
        mock_create_config_files,
        mock_create_server_files,
        mock_create_directory_structure,
    ):
        """Test scaffolding a server with a config."""
        server_name = "test_server"
        description = "Test server description"
        author = "Test Author"
        email = "test@example.com"
        expected_path = os.path.join(os.getcwd(), server_name)

        # Call the function
        result = scaffold_server(
            output_dir=os.getcwd(),
            server_name=server_name,
            description=description,
            author=author,
            email=email,
        )

        # Verify the function returned a result with a path
        self.assertIsInstance(result, dict)
        self.assertIn("path", result)

        # Verify the mocked functions were called
        mock_create_directory_structure.assert_called_once_with(server_name, expected_path)
        mock_create_server_files.assert_called_once()
        mock_create_config_files.assert_called_once_with(server_name, expected_path)
        mock_create_cursor_rules.assert_not_called()

    def test_scaffold_server_integration(self):
        """Integration test for scaffolding a server."""
        server_name = "integration_test_server"
        description = "Integration test server"
        author = "Test Author"
        email = "test@example.com"

        # Create a real server
        path_dict = scaffold_server(
            output_dir=self.temp_dir.name,
            server_name=server_name,
            description=description,
            author=author,
            email=email,
        )

        server_path = path_dict["path"]

        # Check if the directory was created
        self.assertTrue(os.path.exists(server_path))

        # Check if configuration files were created
        pyproject_path = os.path.join(server_path, "pyproject.toml")
        self.assertTrue(os.path.exists(pyproject_path))

        flake8_path = os.path.join(server_path, ".flake8")
        self.assertTrue(os.path.exists(flake8_path))

        isort_path = os.path.join(server_path, ".isort.cfg")
        self.assertTrue(os.path.exists(isort_path))

        pre_commit_path = os.path.join(server_path, ".pre-commit-config.yaml")
        self.assertTrue(os.path.exists(pre_commit_path))

        readme_path = os.path.join(server_path, "README.md")
        self.assertTrue(os.path.exists(readme_path))

        # Verify pyproject.toml content
        with open(pyproject_path, "r") as f:
            content = f.read()
            self.assertIn(f'name = "{server_name}"', content)
            self.assertIn(f'description = "{description}"', content)
            self.assertIn(f'{{name = "{author}", email = "{email}"}}', content)
            self.assertIn("fluent_mcp>=0.1.0", content)
            self.assertIn("[project.optional-dependencies]", content)
            self.assertIn("dev = [", content)
            self.assertIn("pytest>=7.0.0", content)
            self.assertIn("pre-commit>=2.17.0", content)

        # Verify .flake8 content
        with open(flake8_path, "r") as f:
            content = f.read()
            self.assertIn("max-line-length = 100", content)
            self.assertIn("ignore = E203,W503", content)

        # Verify .isort.cfg content
        with open(isort_path, "r") as f:
            content = f.read()
            self.assertIn("profile = black", content)
            self.assertIn("line_length = 100", content)
            self.assertIn(f"known_first_party = {server_name}", content)

        # Verify .pre-commit-config.yaml content
        with open(pre_commit_path, "r") as f:
            content = f.read()
            self.assertIn("repo: https://github.com/psf/black", content)
            self.assertIn("repo: https://github.com/pycqa/isort", content)
            self.assertIn("repo: https://github.com/pycqa/flake8", content)

    def test_scaffold_server_with_cursor_rules(self):
        """Integration test for scaffolding a server with Cursor rules."""
        server_name = "cursor_rules_test_server"
        description = "Server with Cursor rules"
        author = "Test Author"
        email = "test@example.com"

        # Create a real server with Cursor rules
        path_dict = scaffold_server(
            output_dir=self.temp_dir.name,
            server_name=server_name,
            description=description,
            author=author,
            email=email,
            generate_cursor_rules=True,
        )

        server_path = path_dict["path"]

        # Check if the directory was created
        self.assertTrue(os.path.exists(server_path))

        # Check if Cursor rules directory was created
        cursor_rules_dir = os.path.join(server_path, ".cursor", "rules")
        self.assertTrue(os.path.exists(cursor_rules_dir))

        # Check if Cursor rule files were created
        rule_files = [
            "general-coding-standards.mdc",
            "two-tier-architecture.mdc",
            "embedded-tools.mdc",
            "external-tools.mdc",
            "prompt-engineering.mdc",
        ]

        for rule_file in rule_files:
            rule_path = os.path.join(cursor_rules_dir, rule_file)
            self.assertTrue(os.path.exists(rule_path), f"Rule file {rule_file} was not created")

            # Verify rule file content
            with open(rule_path, "r") as f:
                content = f.read()
                self.assertIn("description:", content)
                self.assertIn("globs:", content)

                # Check for server name in content where applicable
                if rule_file in ["embedded-tools.mdc", "external-tools.mdc", "prompt-engineering.mdc"]:
                    self.assertIn(f"{server_name}/", content)

    @patch("fluent_mcp.scaffolder.create_directory_structure")
    @patch("fluent_mcp.scaffolder.create_server_files")
    @patch("fluent_mcp.scaffolder.create_config_files")
    @patch("fluent_mcp.scaffolder.create_cursor_rules")
    def test_scaffold_server_with_cursor_rules_mock(
        self,
        mock_create_cursor_rules,
        mock_create_config_files,
        mock_create_server_files,
        mock_create_directory_structure,
    ):
        """Test scaffolding a server with Cursor rules using mocks."""
        server_name = "test_server"
        expected_path = os.path.join(os.getcwd(), server_name)

        # Call the function with generate_cursor_rules=True
        result = scaffold_server(output_dir=os.getcwd(), server_name=server_name, generate_cursor_rules=True)

        # Verify the function returned a result with a path
        self.assertIsInstance(result, dict)
        self.assertIn("path", result)

        # Verify the mocked functions were called
        mock_create_directory_structure.assert_called_once_with(server_name, expected_path)
        mock_create_server_files.assert_called_once()
        mock_create_config_files.assert_called_once_with(server_name, expected_path)
        mock_create_cursor_rules.assert_called_once_with(server_name, expected_path)


if __name__ == "__main__":
    unittest.main()
