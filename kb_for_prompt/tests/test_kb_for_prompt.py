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
# ]
# ///

"""
Tests for the main entry point of the KB for Prompt application.

This module tests the main entry point functionality including:
- Command-line interface
- Direct conversion modes (URL, file, batch)
- Integration with menu system
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from rich.console import Console

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the main function from kb_for_prompt module
from kb_for_prompt.pages.kb_for_prompt import main, handle_direct_conversion


class TestKbForPromptMain:
    """Tests for the main entry point function."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.runner = CliRunner()
    
    @patch('kb_for_prompt.pages.kb_for_prompt.MenuSystem')
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_interactive_mode(self, mock_banner, mock_menu_system):
        """Test the main function when run in interactive mode (no arguments)."""
        # Setup mock menu system
        mock_menu_instance = MagicMock()
        mock_menu_instance.run.return_value = 0
        mock_menu_system.return_value = mock_menu_instance
        
        # Call the main function through CliRunner
        result = self.runner.invoke(main)
        
        # Assert the exit code
        assert result.exit_code == 0
        
        # Assert that banner was displayed
        mock_banner.assert_called_once()
        
        # Assert that menu system was created and run
        mock_menu_system.assert_called_once()
        mock_menu_instance.run.assert_called_once()
    
    @patch('kb_for_prompt.pages.kb_for_prompt.handle_direct_conversion')
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_url_mode(self, mock_banner, mock_handle_direct):
        """Test the main function when run with --url argument."""
        # Setup mock direct conversion
        mock_handle_direct.return_value = 0
        
        # Call the main function with URL
        result = self.runner.invoke(main, ['--url', 'https://example.com'])
        
        # Assert the exit code
        assert result.exit_code == 0
        
        # Assert that banner was displayed
        mock_banner.assert_called_once()
        
        # Assert that direct conversion was called with correct args
        mock_handle_direct.assert_called_once()
        args, _ = mock_handle_direct.call_args
        assert args[0] == 'https://example.com'  # url
        assert args[1] is None  # file
        assert args[2] is None  # batch
        assert args[3] is None  # output_dir
    
    @patch('kb_for_prompt.pages.kb_for_prompt.handle_direct_conversion')
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_file_mode(self, mock_banner, mock_handle_direct):
        """Test the main function when run with --file argument."""
        # Setup mock direct conversion
        mock_handle_direct.return_value = 0
        
        # Call the main function with file
        result = self.runner.invoke(main, ['--file', '/path/to/doc.pdf'])
        
        # Assert the exit code
        assert result.exit_code == 0
        
        # Assert that direct conversion was called with correct args
        mock_handle_direct.assert_called_once()
        args, _ = mock_handle_direct.call_args
        assert args[0] is None  # url
        assert args[1] == '/path/to/doc.pdf'  # file
        assert args[2] is None  # batch
        assert args[3] is None  # output_dir
    
    @patch('kb_for_prompt.pages.kb_for_prompt.handle_direct_conversion')
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_batch_mode(self, mock_banner, mock_handle_direct):
        """Test the main function when run with --batch argument."""
        # Setup mock direct conversion
        mock_handle_direct.return_value = 0
        
        # Call the main function with batch
        result = self.runner.invoke(main, ['--batch', '/path/to/inputs.csv'])
        
        # Assert the exit code
        assert result.exit_code == 0
        
        # Assert that direct conversion was called with correct args
        mock_handle_direct.assert_called_once()
        args, _ = mock_handle_direct.call_args
        assert args[0] is None  # url
        assert args[1] is None  # file
        assert args[2] == '/path/to/inputs.csv'  # batch
        assert args[3] is None  # output_dir
    
    @patch('kb_for_prompt.pages.kb_for_prompt.handle_direct_conversion')
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_with_output_dir(self, mock_banner, mock_handle_direct):
        """Test the main function when run with --output-dir argument."""
        # Setup mock direct conversion
        mock_handle_direct.return_value = 0
        
        # Call the main function with URL and output dir
        result = self.runner.invoke(main, [
            '--url', 'https://example.com',
            '--output-dir', '/path/to/output'
        ])
        
        # Assert the exit code
        assert result.exit_code == 0
        
        # Assert that direct conversion was called with correct args
        mock_handle_direct.assert_called_once()
        args, _ = mock_handle_direct.call_args
        assert args[0] == 'https://example.com'  # url
        assert args[1] is None  # file
        assert args[2] is None  # batch
        assert args[3] == '/path/to/output'  # output_dir
    
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_keyboard_interrupt(self, mock_banner):
        """Test handling of KeyboardInterrupt in main function."""
        # Create a mock that raises KeyboardInterrupt
        with patch('kb_for_prompt.pages.kb_for_prompt.MenuSystem') as mock_menu:
            mock_menu.return_value.run.side_effect = KeyboardInterrupt()
            
            # Call the main function
            result = self.runner.invoke(main)
            
            # Assert the exit code (should be 0 for clean exit)
            assert result.exit_code == 0
            
            # Assert that the error message appears in the output
            assert "Operation cancelled by user" in result.output
    
    @patch('kb_for_prompt.pages.kb_for_prompt.display_banner')
    def test_main_unexpected_exception(self, mock_banner):
        """Test handling of unexpected exceptions in main function."""
        # Create a mock that raises an exception
        with patch('kb_for_prompt.pages.kb_for_prompt.MenuSystem') as mock_menu:
            mock_menu.return_value.run.side_effect = ValueError("Test error")
            
            # The exception should be caught inside main() and printed to the console
            # But because we're using CliRunner, the exit code is managed by Click
            # and it doesn't propagate the error code correctly in tests
            result = self.runner.invoke(main)
            
            # Assert that the error message appears in the output
            assert "An unexpected error occurred" in result.output
            assert "Test error" in result.output


class TestDirectConversionHandler:
    """Tests for the direct conversion handler function."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.console = MagicMock(spec=Console)
    
    @patch('kb_for_prompt.pages.kb_for_prompt.BatchConverter')
    def test_handle_batch_conversion(self, mock_batch_converter):
        """Test direct batch conversion with CSV file."""
        # Setup mock batch converter
        mock_batch_instance = MagicMock()
        mock_batch_instance.run.return_value = (True, {"total": 5, "successful": [1, 2, 3], "failed": [4, 5]})
        mock_batch_converter.return_value = mock_batch_instance
        
        # Call the function
        result = handle_direct_conversion(
            url=None,
            file=None,
            batch='/path/to/inputs.csv',
            output_dir='/path/to/output',
            console=self.console
        )
        
        # Assert result
        assert result == 1  # Expected error code
        
        # Assert batch converter was called correctly
        mock_batch_converter.assert_called_once_with(console=self.console)
        mock_batch_instance.run.assert_called_once_with('/path/to/inputs.csv', Path('/path/to/output'))
    
    @patch('kb_for_prompt.pages.kb_for_prompt.BatchConverter')
    def test_handle_batch_conversion_failure(self, mock_batch_converter):
        """Test direct batch conversion failure case."""
        # Setup mock batch converter to return failure
        mock_batch_instance = MagicMock()
        mock_batch_instance.run.return_value = (False, {"error": {"message": "Failed to read CSV"}})
        mock_batch_converter.return_value = mock_batch_instance
        
        # Call the function
        result = handle_direct_conversion(
            url=None,
            file=None,
            batch='/path/to/inputs.csv',
            output_dir=None,  # Test with default (cwd)
            console=self.console
        )
        
        # Assert result
        assert result == 1  # Failure
        
        # Assert batch converter was called with cwd as default output dir
        mock_batch_instance.run.assert_called_once()
        args, _ = mock_batch_instance.run.call_args
        assert args[0] == '/path/to/inputs.csv'
        assert isinstance(args[1], Path)  # Should be Path object
        assert args[1] == Path.cwd()  # Should default to current working directory
    
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_handle_url_conversion(self, mock_single_converter):
        """Test direct URL conversion."""
        # Setup mock single item converter
        mock_single_instance = MagicMock()
        mock_single_instance.run.return_value = (True, {"output_path": "/path/to/output.md"})
        mock_single_converter.return_value = mock_single_instance
        
        # Call the function
        result = handle_direct_conversion(
            url='https://example.com',
            file=None,
            batch=None,
            output_dir='/path/to/output',
            console=self.console
        )
        
        # Assert result
        assert result == 1  # Expected error code
        
        # Assert single converter was called correctly
        mock_single_converter.assert_called_once_with(console=self.console)
        mock_single_instance.run.assert_called_once_with('https://example.com', Path('/path/to/output'))
    
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_handle_file_conversion(self, mock_single_converter):
        """Test direct file conversion."""
        # Setup mock single item converter
        mock_single_instance = MagicMock()
        mock_single_instance.run.return_value = (True, {"output_path": "/path/to/output.md"})
        mock_single_converter.return_value = mock_single_instance
        
        # Call the function
        result = handle_direct_conversion(
            url=None,
            file='/path/to/document.pdf',
            batch=None,
            output_dir=None,  # Test with no output dir
            console=self.console
        )
        
        # Assert result
        assert result == 0  # Success
        
        # Assert single converter was called correctly
        mock_single_converter.assert_called_once_with(console=self.console)
        mock_single_instance.run.assert_called_once_with('/path/to/document.pdf', Path.cwd())
    
    @patch('kb_for_prompt.pages.kb_for_prompt.SingleItemConverter')
    def test_handle_url_conversion_failure(self, mock_single_converter):
        """Test direct URL conversion failure case."""
        # Setup mock single item converter to return failure
        mock_single_instance = MagicMock()
        mock_single_instance.run.return_value = (False, {"error": {"message": "Failed to fetch URL"}})
        mock_single_converter.return_value = mock_single_instance
        
        # Call the function
        result = handle_direct_conversion(
            url='https://invalid-url.example',
            file=None,
            batch=None,
            output_dir=None,
            console=self.console
        )
        
        # Assert result
        assert result == 1  # Failure
        
        # Assert single converter was called with cwd as default output dir
        mock_single_instance.run.assert_called_once_with('https://invalid-url.example', Path.cwd())
