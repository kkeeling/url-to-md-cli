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
from pathlib import Path # Import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import necessary components AFTER adjusting sys.path
from kb_for_prompt.organisms.menu_system import MenuSystem, MenuState
from kb_for_prompt.atoms.error_utils import ValidationError, ConversionError
# Import Confirm for patching target reference if needed, although string target is preferred
from rich.prompt import Confirm


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

        # Verify banner and section header were displayed (banner is called in run(), not here)
        # mock_display_banner.assert_called_once() # Banner is called in run()
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
        self.menu_system.current_state = MenuState.SINGLE_ITEM_MENU # Set current state

        # Set up the mock to return the back option
        self.mock_console.input.side_effect = ["b"]  # Back option

        # Run the single item menu handler
        self.menu_system._handle_single_item_menu()

        # Check that the state goes back to the main menu
        assert self.menu_system.current_state == MenuState.MAIN_MENU
        assert len(self.menu_system.state_history) == 0 # History is popped by _go_back

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
        # Set up the mock to return a file path object
        mock_path = MagicMock(spec=Path)
        mock_path.suffix = ".pdf"
        mock_path.__str__.return_value = "/path/to/document.pdf"
        mock_prompt_for_file.return_value = mock_path

        # Run the file input handler
        self.menu_system._handle_file_input()

        # Check that the file info is stored in user data
        assert self.menu_system.user_data["input_type"] == "pdf"
        assert self.menu_system.user_data["input_path"] == "/path/to/document.pdf"

        # Check that the state transitions correctly
        assert self.menu_system.current_state == MenuState.OUTPUT_DIR_INPUT

    # Patch the function *where it is imported* within the handler
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('kb_for_prompt.templates.prompts.prompt_for_output_directory') # Corrected patch target
    def test_output_dir_input(self, mock_prompt_for_output_directory, mock_display_section_header):
        """Test output directory input handling for single item flow."""
        # Set up the mock to return a real Path object
        test_path = Path("/path/to/output")
        mock_prompt_for_output_directory.return_value = test_path

        # Simulate coming from a single item input state (e.g., URL_INPUT)
        # This ensures the non-batch path is taken in _handle_output_dir_input
        initial_history = [MenuState.MAIN_MENU, MenuState.SINGLE_ITEM_MENU, MenuState.URL_INPUT]
        self.menu_system.state_history = initial_history.copy()
        self.menu_system.current_state = MenuState.OUTPUT_DIR_INPUT # Set current state before handler runs

        # Run the output directory input handler
        self.menu_system._handle_output_dir_input()

        # Check that the mock was called correctly
        mock_prompt_for_output_directory.assert_called_once_with(console=self.mock_console)

        # Check that the output directory is stored in user data
        assert "output_dir" in self.menu_system.user_data # Check key exists
        assert self.menu_system.user_data["output_dir"] == "/path/to/output" # Check value

        # Check that the state transitions correctly to CONFIRMATION for single item
        assert self.menu_system.current_state == MenuState.CONFIRMATION

        # Check history was updated correctly by the transition
        # The _transition_to method should add the previous state (OUTPUT_DIR_INPUT) to history
        expected_history = initial_history + [MenuState.OUTPUT_DIR_INPUT]
        assert self.menu_system.state_history == expected_history

    # Patch Confirm.ask directly to prevent actual stdin read
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('rich.prompt.Confirm.ask')
    def test_confirmation_proceed(self, mock_confirm_ask, mock_display_section_header):
        """Test confirmation with proceed option."""
        # Set up the mock for Confirm.ask to return True (proceed)
        mock_confirm_ask.return_value = True

        # Set up history and current state before calling the handler
        initial_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT
        ]
        self.menu_system.state_history = initial_history.copy()
        self.menu_system.current_state = MenuState.CONFIRMATION

        # Run the confirmation handler
        self.menu_system._handle_confirmation()

        # Check that the state transitions correctly to PROCESSING
        assert self.menu_system.current_state == MenuState.PROCESSING

        # Check history was updated correctly by the transition
        # The _transition_to method should add the previous state (CONFIRMATION) to history
        expected_history = initial_history + [MenuState.CONFIRMATION]
        assert self.menu_system.state_history == expected_history

        # Verify Confirm.ask was called (it's called by prompt_for_continue)
        mock_confirm_ask.assert_called_once()

    # Patch Confirm.ask directly to prevent actual stdin read
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    @patch('rich.prompt.Confirm.ask')
    def test_confirmation_go_back(self, mock_confirm_ask, mock_display_section_header):
        """Test confirmation with go back option."""
        # Set up the mock for Confirm.ask to return False (go back)
        mock_confirm_ask.return_value = False

        # Set up the menu system with a history matching the single-item flow
        initial_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU, # Target state to go back to
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT
        ]
        self.menu_system.state_history = initial_history.copy()
        # Set the state *before* calling the handler
        self.menu_system.current_state = MenuState.CONFIRMATION

        # Run the confirmation handler
        self.menu_system._handle_confirmation()

        # Check that the state goes back correctly to SINGLE_ITEM_MENU
        # The handler finds SINGLE_ITEM_MENU at i=2 in reversed list, calls _go_back(steps=3)
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU

        # Check history after _go_back(3) - it should remove the last 3 states
        expected_history = initial_history[:-3] # Removes last 3 elements
        assert self.menu_system.state_history == expected_history

        # Verify Confirm.ask was called (it's called by prompt_for_continue)
        mock_confirm_ask.assert_called_once()

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
        initial_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT
        ]
        self.menu_system.state_history = initial_history.copy()
        self.menu_system.current_state = MenuState.OUTPUT_DIR_INPUT

        # Go back one step
        self.menu_system._go_back()

        # Check that we went back to URL_INPUT
        assert self.menu_system.current_state == MenuState.URL_INPUT
        expected_history = initial_history[:-1] # Removes last element
        assert self.menu_system.state_history == expected_history

        # Go back another step
        self.menu_system._go_back()

        # Check that we went back to SINGLE_ITEM_MENU
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
        expected_history = initial_history[:-2] # Removes last 2 elements
        assert self.menu_system.state_history == expected_history

    def test_go_back_multiple_steps(self):
        """Test going back multiple steps at once."""
        # Set up some history
        initial_history = [
            MenuState.MAIN_MENU,
            MenuState.SINGLE_ITEM_MENU,
            MenuState.URL_INPUT,
            MenuState.OUTPUT_DIR_INPUT
        ]
        self.menu_system.state_history = initial_history.copy()
        self.menu_system.current_state = MenuState.CONFIRMATION

        # Go back two steps
        self.menu_system._go_back(steps=2)

        # Check that we went back to URL_INPUT (history[-2])
        assert self.menu_system.current_state == MenuState.URL_INPUT
        expected_history = initial_history[:-2] # Removes last 2 elements
        assert self.menu_system.state_history == expected_history

    def test_go_back_insufficient_history(self):
        """Test going back more steps than available in history."""
        # Set up minimal history
        self.menu_system.state_history = [MenuState.MAIN_MENU]
        self.menu_system.current_state = MenuState.SINGLE_ITEM_MENU

        # Try to go back two steps when only one is available
        self.menu_system._go_back(steps=2)

        # Should fallback to main menu and clear history
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

        # Set up the console input for recovery (mocking console.input directly)
        self.mock_console.input.return_value = "2"  # Go to main menu

        # Handle the error
        result = self.menu_system._handle_error(error)

        # Check that the error was displayed
        mock_display_validation_error.assert_called_once()

        # Check that recovery was successful
        assert result is True

        # Check that we transitioned to the main menu
        assert self.menu_system.current_state == MenuState.MAIN_MENU
        assert self.menu_system.state_history == [] # History cleared on transition to main menu

    @patch('kb_for_prompt.organisms.menu_system.display_error')
    def test_handle_conversion_error(self, mock_display_error):
        """Test handling of conversion errors."""
        # Create a conversion error
        error = ConversionError(
            message="Failed to convert document",
            input_path="/path/to/document.pdf",
            conversion_type="pdf"
        )
        # Set up some history to go back to
        initial_history = [MenuState.MAIN_MENU, MenuState.SINGLE_ITEM_MENU]
        self.menu_system.state_history = initial_history.copy()
        self.menu_system.current_state = MenuState.PROCESSING # Assume error happened during processing

        # Set up the console input for recovery (mocking console.input directly)
        self.mock_console.input.return_value = "1"  # Go back to previous menu

        # Handle the error
        result = self.menu_system._handle_error(error)

        # Check that the error was displayed
        mock_display_error.assert_called_once()

        # Check that recovery was successful
        assert result is True
        # Check that we went back one step
        assert self.menu_system.current_state == MenuState.SINGLE_ITEM_MENU
        assert self.menu_system.state_history == [MenuState.MAIN_MENU]

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
        # History contains the states *before* the transition occurred
        # states[0] -> states[1] (history=[0])
        # states[1] -> states[2] (history=[0, 1])
        # states[2] -> states[3] (history=[0, 1, 2])
        # states[3] -> states[4] (history=[1, 2, 3]) - limit kicks in, [0] is dropped
        assert len(self.menu_system.state_history) == 3

        # Check that only the most recent states are kept
        expected_history = states[1:4] # states[1], states[2], states[3]
        assert self.menu_system.state_history == expected_history
