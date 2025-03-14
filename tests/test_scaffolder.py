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

    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_scaffold_server(self, mock_print, mock_file, mock_makedirs, mock_exists):
        """Test scaffolding a server."""
        server_name = "test_server"

        # Mock the path.exists to return False (directory doesn't exist)
        expected_path = os.path.join(os.getcwd(), server_name)

        # Call the function
        path = scaffold_server(name=server_name)

        # Verify the function returned the expected path
        self.assertEqual(path, expected_path)

        # Verify makedirs was called multiple times
        self.assertTrue(mock_makedirs.call_count >= 1)

        # Verify open was called to create files
        self.assertTrue(mock_file.call_count >= 1)

    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_scaffold_server_with_config(self, mock_print, mock_file, mock_makedirs, mock_exists):
        """Test scaffolding a server with a config."""
        server_name = "test_server"
        config = {"server": {"host": "localhost", "port": 9000}}

        # Mock the path.exists to return False (directory doesn't exist)
        expected_path = os.path.join(os.getcwd(), server_name)

        # Call the function
        path = scaffold_server(name=server_name, config=config)

        # Verify the function returned the expected path
        self.assertEqual(path, expected_path)

        # Verify makedirs was called multiple times
        self.assertTrue(mock_makedirs.call_count >= 1)

        # Verify open was called to create files
        self.assertTrue(mock_file.call_count >= 1)


if __name__ == "__main__":
    unittest.main()
