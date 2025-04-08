# /// script
# requires-python = "==3.12"
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

# Run pytest if executed directly
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))

"""
Tests for kb_for_prompt.organisms.menu_system module.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kb_for_prompt.organisms.menu_system import MenuSystem, MenuState
from kb_for_prompt.atoms.error_utils import ValidationError, ConversionError


class TestMenuSystem:
    """Test cases for the menu system module."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create a mock console
        self.mock_console = MagicMock()
        self.mock_console.input = MagicMock()
        self.mock_console.print = MagicMock()
        
        # Create the menu system with the mock console
        self.menu_system = MenuSystem(console=self.mock_console)
    
    @patch('kb_for_prompt.organisms.menu_system.display_banner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.display_main_menu')
    def test_main_menu_single_item(self, mock_display_main_menu, mock_display_section_header, mock_display_banner):
        """Test main menu with single item selection."""
        # Set up the mock to return the single item option
        mock_display_main_menu.return_value = "1"  # SINGLE_ITEM
        
        # Run the main menu handler
        self.menu_system._handle_main_menu()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
        
        # Verify banner and section header were displayed
        mock_display_section_header.assert_called_once()
        mock_display_main_menu.assert_called_once()
    
    @patch('kb_for_prompt.organisms.menu_system.display_banner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.display_main_menu')
    def test_main_menu_batch(self, mock_display_main_menu, mock_display_section_header, mock_display_banner):
        """Test main menu with batch selection."""
        # Set up the mock to return the batch option
        mock_display_main_menu.return_value = "2"  # BATCH
        
        # Run the main menu handler
        self.menu_system._handle_main_menu()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.BATCH_MENU
    
    @patch('kb_for_prompt.organisms.menu_system.display_banner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.display_main_menu')
    def test_main_menu_exit(self, mock_display_main_menu, mock_display_section_header, mock_display_banner):
        """Test main menu with exit selection."""
        # Set up the mock to return the exit option
        mock_display_main_menu.return_value = "0"  # EXIT
        
        # Run the main menu handler
        self.menu_system._handle_main_menu()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.EXIT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_single_item_menu(self, mock_display_section_header):
        """Test single item menu with URL selection."""
        # Set up the mock to return the URL option
        self.mock_console.input.side_effect = ["1"]  # URL option
        
        # Run the single item menu handler
        self.menu_system._handle_single_item_menu()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.URL_INPUT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_single_item_menu_file(self, mock_display_section_header):
        """Test single item menu with file selection."""
        # Set up the mock to return the file option
        self.mock_console.input.side_effect = ["2"]  # File option
        
        # Run the single item menu handler
        self.menu_system._handle_single_item_menu()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.FILE_INPUT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_single_item_menu_back(self, mock_display_section_header):
        """Test single item menu with back selection."""
        # Set up the menu system with a history entry
        self.menu_system.state_history = [MenuState.MAIN_MENU]
        
        # Set up the mock to return the back option
        self.mock_console.input.side_effect = ["b"]  # Back option
        
        # Run the single item menu handler
        self.menu_system._handle_single_item_menu()
        
        # Check that the state goes back to the main menu
        assert self.menu_system.current_state == MenuState.MAIN_MENU
        assert len(self.menu_system.state_history) == 0
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_single_item_menu_invalid_then_valid(self, mock_display_section_header):
        """Test single item menu with invalid input followed by valid input."""
        # Set up the mock to return an invalid option followed by a valid option
        self.mock_console.input.side_effect = ["invalid", "1"]  # Invalid, then URL option
        
        # Run the single item menu handler
        self.menu_system._handle_single_item_menu()
        
        # Verify warning was printed for invalid input
        self.mock_console.print.assert_any_call("[bold yellow]Invalid option. Please try again.[/bold yellow]")
        
        # Check that the state transitions correctly after valid input
        assert self.menu_system.current_state == MenuState.URL_INPUT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.prompt_for_url')
    def test_url_input(self, mock_prompt_for_url, mock_display_section_header):
        """Test URL input handling."""
        # Set up the mock to return a URL
        test_url = "https://example.com"
        mock_prompt_for_url.return_value = test_url
        
        # Run the URL input handler
        self.menu_system._handle_url_input()
        
        # Check that the URL is stored in user data
        assert self.menu_system.user_data["input_type"] == "url"
        assert self.menu_system.user_data["input_path"] == test_url
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.OUTPUT_DIR_INPUT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.prompt_for_file')
    def test_file_input(self, mock_prompt_for_file, mock_display_section_header):
        """Test file input handling."""
        # Set up the mock to return a file path
        test_file = MagicMock()
        test_file.suffix = ".pdf"
        test_file.__str__.return_value = "/path/to/document.pdf"
        mock_prompt_for_file.return_value = test_file
        
        # Run the file input handler
        self.menu_system._handle_file_input()
        
        # Check that the file info is stored in user data
        assert self.menu_system.user_data["input_type"] == "pdf"
        assert self.menu_system.user_data["input_path"] == "/path/to/document.pdf"
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.OUTPUT_DIR_INPUT
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.prompt_for_output_directory')
    def test_output_dir_input(self, mock_prompt_for_output_directory, mock_display_section_header):
        """Test output directory input handling."""
        # Set up the mock to return an output directory
        test_dir = MagicMock()
        test_dir.__str__.return_value = "/path/to/output"
        mock_prompt_for_output_directory.return_value = test_dir
        
        # Run the output directory input handler
        self.menu_system._handle_output_dir_input()
        
        # Check that the output directory is stored in user data
        assert self.menu_system.user_data["output_dir"] == "/path/to/output"
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.CONFIRMATION
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.prompt_for_continue')
    def test_confirmation_proceed(self, mock_prompt_for_continue, mock_display_section_header):
        """Test confirmation with proceed option."""
        # Set up the mock to return True (proceed)
        mock_prompt_for_continue.return_value = True
        
        # Run the confirmation handler
        self.menu_system._handle_confirmation()
        
        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.PROCESSING
    
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.organisms.menu_system.prompt_for_continue')
    def test_confirmation_go_back(self, mock_prompt_for_continue, mock_display_section_header):
        """Test confirmation with go back option."""
        # Set up the mock to return False (go back)
        mock_prompt_for_continue.return_value = False
        
        # Set up the menu system with a history
        self.menu_system.state_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT
        ]
        
        # Run the confirmation handler
        self.menu_system._handle_confirmation()
        
        # Check that the state goes back correctly (2 steps)
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
    
    def test_transition_to(self):
        """Test transition to a new state."""
        # Start in main menu
        self.menu_system.current_state = MenuState.MAIN_MENU
        
        # Transition to single item menu
        self.menu_system._transition_to(MenuState.SINGLE_ITEM_MENU)
        
        # Check that the state changed and history was updated
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
        assert self.menu_system.state_history == [MenuState.MAIN_MENU]
        
        # Transition to URL input
        self.menu_system._transition_to(MenuState.URL_INPUT)
        
        # Check that the state changed and history was updated
        assert self.menu_system.current_state == MenuState.URL_INPUT
        assert self.menu_system.state_history == [MenuState.MAIN_MENU, MenuState.SINGLE_ITEM_MENU]
    
    def test_transition_to_clear_history(self):
        """Test transition to a new state with history clearing."""
        # Set up some history
        self.menu_system.state_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU
        ]
        
        # Transition to URL input with history clearing
        self.menu_system._transition_to(MenuState.URL_INPUT, clear_history=True)
        
        # Check that the state changed and history was cleared
        assert self.menu_system.current_state == MenuState.URL_INPUT
        assert self.menu_system.state_history == []
    
    def test_go_back(self):
        """Test going back to a previous state."""
        # Set up some history
        self.menu_system.state_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT
        ]
        self.menu_system.current_state = MenuState.OUTPUT_DIR_INPUT
        
        # Go back one step
        self.menu_system._go_back()
        
        # Check that we went back to URL_INPUT
        assert self.menu_system.current_state == MenuState.URL_INPUT
        assert len(self.menu_system.state_history) == 2
        
        # Go back another step
        self.menu_system._go_back()
        
        # Check that we went back to SINGLE_ITEM_MENU
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
        assert len(self.menu_system.state_history) == 1
    
    def test_go_back_multiple_steps(self):
        """Test going back multiple steps at once."""
        # Set up some history
        self.menu_system.state_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT
        ]
        self.menu_system.current_state = MenuState.CONFIRMATION
        
        # Go back two steps
        self.menu_system._go_back(steps=2)
        
        # Check that we went back to URL_INPUT
        assert self.menu_system.current_state == MenuState.URL_INPUT
        assert len(self.menu_system.state_history) == 2
    
    def test_go_back_insufficient_history(self):
        """Test going back more steps than available in history."""
        # Set up minimal history
        self.menu_system.state_history = [MenuState.MAIN_MENU]
        self.menu_system.current_state = MenuState.SINGLE_ITEM_MENU
        
        # Try to go back two steps when only one is available
        self.menu_system._go_back(steps=2)
        
        # Should fallback to main menu
        assert self.menu_system.current_state == MenuState.MAIN_MENU
        assert len(self.menu_system.state_history) == 0
    
    @patch('kb_for_prompt.organisms.menu_system.display_validation_error')
    def test_handle_validation_error(self, mock_display_validation_error):
        """Test handling of validation errors."""
        # Create a validation error
        error = ValidationError(
            message="Invalid URL format",
            input_value="invalid-url",
            validation_type="url"
        )
        
        # Set up the console input for recovery
        self.mock_console.input.return_value = "2"  # Go to main menu
        
        # Handle the error
        result = self.menu_system._handle_error(error)
        
        # Check that the error was displayed
        mock_display_validation_error.assert_called_once()
        
        # Check that recovery was successful
        assert result is True
        
        # Check that we transitioned to the main menu
        assert self.menu_system.current_state == MenuState.MAIN_MENU
    
    @patch('kb_for_prompt.organisms.menu_system.display_error')
    def test_handle_conversion_error(self, mock_display_error):
        """Test handling of conversion errors."""
        # Create a conversion error
        error = ConversionError(
            message="Failed to convert document",
            input_path="/path/to/document.pdf",
            conversion_type="pdf"
        )
        
        # Set up the console input for recovery
        self.mock_console.input.return_value = "1"  # Go back to previous menu
        
        # Handle the error
        result = self.menu_system._handle_error(error)
        
        # Check that the error was displayed
        mock_display_error.assert_called_once()
        
        # Check that recovery was successful
        assert result is True
    
    def test_limit_history_size(self):
        """Test that history size is limited."""
        # Set a small max history
        self.menu_system.max_history = 3
        
        # Add states beyond the limit
        states = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT,
            MenuState.CONFIRMATION
        ]
        
        # Reset the menu system's history (to ensure clean test state)
        self.menu_system.state_history = []
        self.menu_system.current_state = states[0]
        
        # Transition through all states
        for state in states[1:]:
            self.menu_system._transition_to(state)
        
        # Check that history was limited to max_history
        assert len(self.menu_system.state_history) == 3
        
        # Check that only the most recent states are kept (the last 3 states from our transitions)
        expected_history = states[-4:-1]  # The last 3 items added to history
        assert self.menu_system.state_history == expected_history