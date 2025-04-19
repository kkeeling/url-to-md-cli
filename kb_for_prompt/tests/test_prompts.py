# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "rich",
#     "halo",
#     "requests",
#     "pandas",
#     "docling",
#     "pytest",
# ]
# ///

"""
Tests for the prompt template functions in kb_for_prompt/templates/prompts.py.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel

from kb_for_prompt.templates.prompts import (
    prompt_for_toc_generation,
    prompt_for_kb_generation,
    prompt_save_confirmation,
    prompt_overwrite_rename,
    prompt_retry_generation,
)


def test_prompt_for_toc_generation_exists():
    """Test that prompt_for_toc_generation function exists with correct signature."""
    assert callable(prompt_for_toc_generation)
    # Check default parameter (console=None)
    assert prompt_for_toc_generation.__defaults__ == (None,)


@patch('kb_for_prompt.templates.prompts.Confirm.ask')
def test_prompt_for_toc_generation_returns_boolean(mock_ask):
    """Test that prompt_for_toc_generation returns a boolean value."""
    # Set up mock
    mock_ask.return_value = True
    
    # Call the function
    result = prompt_for_toc_generation()
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is True
    
    # Set the mock to return False
    mock_ask.return_value = False
    
    # Call the function again
    result = prompt_for_toc_generation()
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is False


def test_prompt_for_kb_generation_exists():
    """Test that prompt_for_kb_generation function exists with correct signature."""
    assert callable(prompt_for_kb_generation)
    # Check default parameter (console=None)
    assert prompt_for_kb_generation.__defaults__ == (None,)


@patch('kb_for_prompt.templates.prompts.Confirm.ask')
def test_prompt_for_kb_generation_returns_boolean(mock_ask):
    """Test that prompt_for_kb_generation returns a boolean value."""
    # Set up mock
    mock_ask.return_value = True
    
    # Call the function
    result = prompt_for_kb_generation()
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is True
    
    # Set the mock to return False
    mock_ask.return_value = False
    
    # Call the function again
    result = prompt_for_kb_generation()
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is False


def test_prompt_save_confirmation_exists():
    """Test that prompt_save_confirmation function exists with correct signature."""
    assert callable(prompt_save_confirmation)
    # Check default parameter (console=None)
    assert prompt_save_confirmation.__defaults__ == (None,)


@patch('kb_for_prompt.templates.prompts.Confirm.ask')
@patch('kb_for_prompt.templates.prompts.Console')
def test_prompt_save_confirmation_returns_boolean(mock_console, mock_ask):
    """Test that prompt_save_confirmation returns a boolean value."""
    # Mock the console print method
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    # Set up mock for Confirm.ask
    mock_ask.return_value = True
    
    # Call the function
    result = prompt_save_confirmation("Some content preview")
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is True
    mock_console_instance.print.assert_called_once() # Check that preview was printed
    
    # Set the mock to return False
    mock_ask.return_value = False
    
    # Call the function again
    result = prompt_save_confirmation("Another preview")
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is False


def test_prompt_overwrite_rename_exists():
    """Test that prompt_overwrite_rename function exists with correct signature."""
    assert callable(prompt_overwrite_rename)
    # Check default parameter (console=None)
    assert prompt_overwrite_rename.__defaults__ == (None,)


@patch('kb_for_prompt.templates.prompts.Prompt.ask')
@patch('kb_for_prompt.templates.prompts.Console')
def test_prompt_overwrite_rename_returns_tuple(mock_console, mock_prompt_ask):
    """Test that prompt_overwrite_rename returns the correct tuple."""
    # Mock the console print method
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance
    
    # Test 'overwrite' case
    mock_prompt_ask.return_value = 'o'
    result = prompt_overwrite_rename("existing_file.txt")
    assert isinstance(result, tuple)
    assert result == ("overwrite", None)
    mock_console_instance.print.assert_called_once() # Check warning was printed

    # Reset mocks for next case
    mock_console_instance.reset_mock()
    mock_prompt_ask.reset_mock()

    # Test 'rename' case
    # First ask returns 'r', second ask returns the new name
    mock_prompt_ask.side_effect = ['r', 'new_file_name.txt']
    result = prompt_overwrite_rename("existing_file.txt")
    assert isinstance(result, tuple)
    assert result == ("rename", "new_file_name.txt")
    assert mock_prompt_ask.call_count == 2
    mock_console_instance.print.assert_called_once() # Check warning was printed

    # Reset mocks for next case
    mock_console_instance.reset_mock()
    mock_prompt_ask.reset_mock()
    mock_prompt_ask.side_effect = None # Clear side effect

    # Test 'cancel' case
    mock_prompt_ask.return_value = 'c'
    result = prompt_overwrite_rename("existing_file.txt")
    assert isinstance(result, tuple)
    assert result == ("cancel", None)
    mock_console_instance.print.assert_called_once() # Check warning was printed


def test_prompt_retry_generation_exists():
    """Test that prompt_retry_generation function exists with correct signature."""
    assert callable(prompt_retry_generation)
    # Check default parameters (process_name="generation", console=None)
    assert prompt_retry_generation.__defaults__ == ("generation", None)


@patch('kb_for_prompt.templates.prompts.Confirm.ask')
def test_prompt_retry_generation_returns_boolean(mock_ask):
    """Test that prompt_retry_generation returns a boolean value."""
    # Set up mock
    mock_ask.return_value = True
    
    # Call the function
    result = prompt_retry_generation()
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is True
    
    # Set the mock to return False
    mock_ask.return_value = False
    
    # Call the function again with a custom process name
    result = prompt_retry_generation(process_name="TOC creation")
    
    # Verify the result is a boolean
    assert isinstance(result, bool)
    assert result is False
    # Check that the custom process name was used in the prompt message
    mock_ask.assert_called_with(
        "[bold green]Do you want to retry the TOC creation process? (y/n)[/bold green]",
        default=True
    )
