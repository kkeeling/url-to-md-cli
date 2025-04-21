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

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.runner = CliRunner()

    @patch('kb_for_prompt.pages.kb_for_prompt.display_spinner', return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base')
    @patch('kb_for_prompt.pages.kb_for_prompt.Confirm.ask', return_value=True) # Mock user confirming 'yes'
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_integration_success_path(self, mock_converter_cls, mock_confirm_ask, mock_condense, mock_spinner, tmp_path):
        """
        Test successful file conversion followed by successful condensation via CLI.
        """
        # --- Arrange ---
        input_file = tmp_path / "input.txt"
        output_dir = tmp_path / "out"
        converted_file_path = output_dir / "input.md"
        condensed_file_path = output_dir / "knowledge_base_condensed.md" # Example name

        mock_converter_instance = mock_converter_cls.return_value
        mock_converter_instance.run.return_value = (True, {'output_path': str(converted_file_path)})
        mock_condense.return_value = condensed_file_path

        # --- Act ---
        result = self.runner.invoke(main, [
            '--file', str(input_file),
            '--output-dir', str(output_dir)
        ], catch_exceptions=False)

        # --- Assert ---
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}. Output:\n{result.output}"
        mock_converter_cls.assert_called_once()
        expected_output_path_resolved = output_dir.resolve()
        mock_converter_instance.run.assert_called_once_with(str(input_file), expected_output_path_resolved)
        mock_confirm_ask.assert_called_once_with(
            "\n[bold yellow]?[/bold yellow] Do you want to generate a condensed version using an LLM?",
            default=False
        )
        mock_spinner.assert_called_once()
        mock_condense.assert_called_once_with(converted_file_path)
        assert "✓ Conversion successful." in result.output
        assert f"Output file: {converted_file_path}" in result.output
        assert "✓ Condensation successful." in result.output
        assert f"Condensed file: {condensed_file_path}" in result.output

    @patch('kb_for_prompt.pages.kb_for_prompt.display_spinner', return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base', return_value=None) # Mock condensation returning None
    @patch('kb_for_prompt.pages.kb_for_prompt.Confirm.ask', return_value=True)
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_integration_condensation_returns_none(self, mock_converter_cls, mock_confirm_ask, mock_condense, mock_spinner, tmp_path):
        """
        Test successful conversion, but condensation returns None (failure).
        """
        # --- Arrange ---
        input_file = tmp_path / "input.txt"
        output_dir = tmp_path / "out"
        converted_file_path = output_dir / "input.md"

        mock_converter_instance = mock_converter_cls.return_value
        mock_converter_instance.run.return_value = (True, {'output_path': str(converted_file_path)})
        # mock_condense is already configured via decorator to return None

        # --- Act ---
        result = self.runner.invoke(main, [
            '--file', str(input_file),
            '--output-dir', str(output_dir)
        ], catch_exceptions=False)

        # --- Assert ---
        # Exit code should still be 0 because the *initial* conversion succeeded
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}. Output:\n{result.output}"
        mock_converter_cls.assert_called_once()
        expected_output_path_resolved = output_dir.resolve()
        mock_converter_instance.run.assert_called_once_with(str(input_file), expected_output_path_resolved)
        mock_confirm_ask.assert_called_once()
        mock_spinner.assert_called_once() # Spinner is still called
        mock_condense.assert_called_once_with(converted_file_path) # Condensation is attempted
        assert "✓ Conversion successful." in result.output
        assert f"Output file: {converted_file_path}" in result.output
        assert "✗ Condensation failed." in result.output # Check for failure message
        assert "Condensed file:" not in result.output # Ensure success message isn't shown

    @patch('kb_for_prompt.pages.kb_for_prompt.display_spinner', return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base') # Mock the function itself
    @patch('kb_for_prompt.pages.kb_for_prompt.Confirm.ask', return_value=True)
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_integration_condensation_raises_exception(self, mock_converter_cls, mock_confirm_ask, mock_condense, mock_spinner, tmp_path):
        """
        Test successful conversion, but condensation raises an exception.
        """
        # --- Arrange ---
        input_file = tmp_path / "input.txt"
        output_dir = tmp_path / "out"
        converted_file_path = output_dir / "input.md"
        test_exception = Exception("LLM API Error")

        mock_converter_instance = mock_converter_cls.return_value
        mock_converter_instance.run.return_value = (True, {'output_path': str(converted_file_path)})
        mock_condense.side_effect = test_exception # Configure mock to raise exception

        # --- Act ---
        result = self.runner.invoke(main, [
            '--file', str(input_file),
            '--output-dir', str(output_dir)
        ], catch_exceptions=False) # Catching exceptions might hide the error we want to test handling for

        # --- Assert ---
        # Exit code should still be 0 because the *initial* conversion succeeded
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}. Output:\n{result.output}"
        mock_converter_cls.assert_called_once()
        expected_output_path_resolved = output_dir.resolve()
        mock_converter_instance.run.assert_called_once_with(str(input_file), expected_output_path_resolved)
        mock_confirm_ask.assert_called_once()
        mock_spinner.assert_called_once() # Spinner is still called
        mock_condense.assert_called_once_with(converted_file_path) # Condensation is attempted
        assert "✓ Conversion successful." in result.output
        assert f"Output file: {converted_file_path}" in result.output
        # Check that the specific exception message is logged (or a generic one if caught)
        assert "An unexpected error occurred during condensation:" in result.output
        assert str(test_exception) in result.output
        assert "✗ Condensation failed." in result.output # Check for failure message

    @patch('kb_for_prompt.pages.kb_for_prompt.display_spinner') # Mock spinner to ensure it's not called for condensation
    @patch('kb_for_prompt.pages.kb_for_prompt.condense_knowledge_base')
    @patch('kb_for_prompt.pages.kb_for_prompt.Confirm.ask')
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_integration_primary_conversion_fails(self, mock_converter_cls, mock_confirm_ask, mock_condense, mock_spinner, tmp_path):
        """
        Test the scenario where the initial file conversion fails.
        """
        # --- Arrange ---
        input_file = tmp_path / "input.txt"
        output_dir = tmp_path / "out"
        error_details = {'type': 'ConversionError', 'message': 'Failed to process file'}

        mock_converter_instance = mock_converter_cls.return_value
        # Mock converter run to return failure
        mock_converter_instance.run.return_value = (False, {'error': error_details})

        # --- Act ---
        result = self.runner.invoke(main, [
            '--file', str(input_file),
            '--output-dir', str(output_dir)
        ], catch_exceptions=False)

        # --- Assert ---
        # Exit code should be non-zero because the primary conversion failed
        assert result.exit_code == 1, f"CLI exited with code {result.exit_code}. Output:\n{result.output}"
        mock_converter_cls.assert_called_once()
        expected_output_path_resolved = output_dir.resolve()
        mock_converter_instance.run.assert_called_once_with(str(input_file), expected_output_path_resolved)

        # Ensure condensation steps were NOT taken
        mock_confirm_ask.assert_not_called()
        mock_spinner.assert_not_called() # Spinner for condensation should not be called
        mock_condense.assert_not_called()

        # Check for failure messages
        assert "✗ Conversion failed." in result.output
        assert f"Error Type: {error_details['type']}" in result.output
        assert f"Error Message: {error_details['message']}" in result.output
        assert "✓ Conversion successful." not in result.output
        assert "Condensation" not in result.output # No condensation messages should appear
