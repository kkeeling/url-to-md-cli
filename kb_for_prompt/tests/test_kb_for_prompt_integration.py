# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "rich",
#     "halo",
#     "requests",
#     "pandas",
#     "docling",
#     "pytest",
#     "pytest-mock",
#     "litellm", # Added as condensation involves LLM client
# ]
# ///

"""
Integration tests for the KB for Prompt CLI application,
focusing on the condensation workflow triggered via command-line options.

These tests verify the end-to-end flow when a user provides a single
input (URL or file) via CLI and opts into the condensation step.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock # Import MagicMock

import pytest
from click.testing import CliRunner

# Add the parent directory to sys.path to allow importing the main script
# This might be necessary depending on how tests are run.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the main entry point of the application
from kb_for_prompt.pages.kb_for_prompt import main


class TestCliCondensationIntegration:
    """
    Test suite for the CLI-driven condensation feature integration.
    """

    # Define dummy paths relative to a potential test directory
    # These will likely be managed by pytest fixtures (e.g., tmp_path) in actual tests
    # dummy_input_file = Path("dummy_input.md") # Replaced by tmp_path usage
    # dummy_output_dir = Path("output") # Replaced by tmp_path usage
    # dummy_condensed_file = Path("output/dummy_input_condensed.md") # Replaced by tmp_path usage

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.runner = CliRunner()

    # Test methods will be added here later to cover different scenarios:
    # - Successful condensation after file conversion (ADDED BELOW)
    # - Successful condensation after URL conversion
    # - User declining condensation
    # - Condensation failure handling
    # - Interaction with mocks for conversion and LLM calls

    @patch('kb_for_prompt.pages.kb_for_prompt.display_spinner', return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base')
    @patch('kb_for_prompt.pages.kb_for_prompt.Confirm.ask', return_value=True) # Mock user confirming 'yes'
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_integration_success_path(self, mock_converter_cls, mock_confirm_ask, mock_condense, mock_spinner, tmp_path):
        """
        Test successful file conversion followed by successful condensation via CLI.
        """
        # --- Arrange ---
        # Define paths using tmp_path fixture
        input_file = tmp_path / "input.txt"
        output_dir = tmp_path / "out"
        # Note: output_dir doesn't need to exist beforehand, handle_direct_conversion creates it.
        # input_file needs to exist for Path.resolve() if not mocked deeply, but CLI passes string.
        # Let's assume the CLI passes the string path correctly.

        # Expected path for the initially converted file
        converted_file_path = output_dir / "input.md"
        # Expected path for the final condensed file
        condensed_file_path = output_dir / "knowledge_base_condensed.md"

        # Configure SingleItemConverter mock
        mock_converter_instance = mock_converter_cls.return_value
        mock_converter_instance.run.return_value = (True, {'output_path': str(converted_file_path)})

        # Configure condense_knowledge_base mock
        mock_condense.return_value = condensed_file_path

        # --- Act ---
        # Invoke the CLI with file and output directory arguments
        result = self.runner.invoke(main, [
            '--file', str(input_file),
            '--output-dir', str(output_dir)
        ], catch_exceptions=False) # Set catch_exceptions=False for easier debugging

        # --- Assert ---
        # Check exit code
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}. Output:\n{result.output}"

        # Check SingleItemConverter instantiation and call
        mock_converter_cls.assert_called_once()
        # handle_direct_conversion resolves the output path before passing it
        expected_output_path_resolved = output_dir.resolve()
        mock_converter_instance.run.assert_called_once_with(str(input_file), expected_output_path_resolved)

        # Check Confirm.ask call
        mock_confirm_ask.assert_called_once_with(
            "\n[bold yellow]?[/bold yellow] Do you want to generate a condensed version using an LLM?",
            default=False
        )

        # Check display_spinner call (basic check)
        mock_spinner.assert_called_once()
        # You could add more specific checks on the spinner text if needed

        # Check condense_knowledge_base call
        mock_condense.assert_called_once_with(converted_file_path)

        # Check output messages
        assert "✓ Conversion successful." in result.output
        assert f"Output file: {converted_file_path}" in result.output
        assert "✓ Condensation successful." in result.output
        assert f"Condensed file: {condensed_file_path}" in result.output

    # Example placeholder for a test (to be implemented)
    # @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    # @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base')
    # @patch('rich.prompt.Confirm.ask', return_value=True) # Mock user confirming 'yes'
    # def test_cli_file_conversion_with_condensation_success(self, mock_confirm, mock_condense, mock_converter, tmp_path):
    #     """
    #     Test successful file conversion followed by successful condensation via CLI.
    #     """
    #     # Setup mocks and dummy files within tmp_path
    #     # ...
    #
    #     # Invoke the CLI
    #     result = self.runner.invoke(main, [
    #         '--file', str(self.dummy_input_file),
    #         '--output-dir', str(self.dummy_output_dir)
    #     ])
    #
    #     # Assertions
    #     assert result.exit_code == 0
    #     # ... check mocks were called, output messages, file existence etc.
    #     pass # Replace with actual test implementation
