# /// script
# requires-python = "==3.12"
# dependencies = [
#     "click",
#     "rich",
#     "halo",
#     "requests",
#     "pandas",
#     "docling",
# ]
# ///

"""
Interactive menu system for the kb-for-prompt CLI application.

This module provides a menu system to navigate between conversion modes
and handle user inputs with robust error recovery. It implements a state-based
navigation flow with history tracking to enable going back to previous states.
"""

import sys
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from rich.console import Console

# Import menu components from templates
from kb_for_prompt.templates.banner import display_banner, display_section_header
from kb_for_prompt.templates.prompts import (
    display_main_menu, 
    prompt_for_url, 
    prompt_for_file, 
    prompt_for_directory,
    prompt_for_output_directory,
    prompt_for_continue,
    prompt_for_retry,
    MenuOption
)
from kb_for_prompt.templates.errors import (
    display_error,
    display_validation_error,
    display_exception
)

# Import errors
from kb_for_prompt.atoms.error_utils import (
    KbForPromptError,
    ValidationError,
    ConversionError
)


class MenuState(Enum):
    """Enumeration of possible menu states."""
    MAIN_MENU = auto()
    SINGLE_ITEM_MENU = auto()
    BATCH_MENU = auto()
    URL_INPUT = auto()
    FILE_INPUT = auto()
    OUTPUT_DIR_INPUT = auto()
    CONFIRMATION = auto()
    PROCESSING = auto()
    RESULTS = auto()
    EXIT = auto()


class MenuSystem:
    """
    Interactive menu system for navigating between conversion modes.
    
    This class manages the application's menu states, transitions between states,
    and user input handling. It uses a state machine approach with history tracking
    to enable navigation backwards through menus.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the menu system.
        
        Args:
            console: The Rich console to print to. If None, a new console is created.
        """
        self.console = console or Console()
        self.current_state = MenuState.MAIN_MENU
        self.state_history = []
        self.user_data: Dict[str, Any] = {}
        self.max_history = 10  # Maximum number of states to keep in history
        
    def run(self) -> int:
        """
        Start the menu system and handle the main loop.
        
        This is the main entry point for the menu system that runs the application loop
        until the user chooses to exit or an unrecoverable error occurs.
        
        Returns:
            int: Exit code (0 for normal exit, non-zero for error)
        """
        try:
            # Display the application banner
            display_banner(console=self.console)
            
            # Start the main loop
            while self.current_state != MenuState.EXIT:
                try:
                    self._handle_current_state()
                except KbForPromptError as e:
                    # Handle known application errors with recovery options
                    recovered = self._handle_error(e)
                    if not recovered:
                        # If recovery failed, exit with error
                        return 1
                except Exception as e:
                    # Handle unexpected exceptions
                    display_exception(e, show_traceback=True, console=self.console)
                    if not self._attempt_recovery(str(e)):
                        return 1
            
            # Clean exit
            self.console.print("\n[green]Thank you for using kb-for-prompt![/green]\n")
            return 0
            
        except KeyboardInterrupt:
            # Handle CTRL+C gracefully
            self.console.print("\n\n[yellow]Operation cancelled by user.[/yellow]")
            return 0
        except Exception as e:
            # Last-resort error handling for unexpected exceptions
            display_exception(
                e, 
                show_traceback=True, 
                exit_program=False,
                console=self.console
            )
            self.console.print("\n[bold red]An unexpected error occurred. The application will exit.[/bold red]")
            return 1
    
    def _handle_current_state(self) -> None:
        """
        Process the current menu state and determine the next state.
        
        This method uses a state machine approach to handle different menu states
        and transitions between them based on user input.
        """
        # Main state machine for navigation
        if self.current_state == MenuState.MAIN_MENU:
            self._handle_main_menu()
        elif self.current_state == MenuState.SINGLE_ITEM_MENU:
            self._handle_single_item_menu()
        elif self.current_state == MenuState.BATCH_MENU:
            self._handle_batch_menu()
        elif self.current_state == MenuState.URL_INPUT:
            self._handle_url_input()
        elif self.current_state == MenuState.FILE_INPUT:
            self._handle_file_input()
        elif self.current_state == MenuState.OUTPUT_DIR_INPUT:
            self._handle_output_dir_input()
        elif self.current_state == MenuState.CONFIRMATION:
            self._handle_confirmation()
        elif self.current_state == MenuState.PROCESSING:
            self._handle_processing()
        elif self.current_state == MenuState.RESULTS:
            self._handle_results()
    
    def _handle_main_menu(self) -> None:
        """
        Handle the main menu state.
        
        Display the main menu options and process the user's selection.
        """
        # Display a section header for the main menu
        display_section_header("Main Menu", console=self.console)
        
        # Display the main menu options and get user choice
        choice = display_main_menu(console=self.console)
        
        # Process the user's choice
        if choice == MenuOption.SINGLE_ITEM.value:
            self._transition_to(MenuState.SINGLE_ITEM_MENU)
        elif choice == MenuOption.BATCH.value:
            self._transition_to(MenuState.BATCH_MENU)
        elif choice == MenuOption.EXIT.value:
            self._transition_to(MenuState.EXIT)
    
    def _handle_single_item_menu(self) -> None:
        """
        Handle the single item conversion menu state.
        
        Present options for URL or file conversion and process the selection.
        """
        display_section_header("Single Item Conversion", console=self.console)
        
        # Present options for URL or file input
        self.console.print("\nWhat would you like to convert?")
        options = {
            "1": "URL",
            "2": "Document file (PDF, DOC, DOCX)",
            "b": "Go back to main menu",
            "0": "Exit application"
        }
        
        for key, value in options.items():
            self.console.print(f"[green]{key}[/green]: {value}")
        
        # Get user choice
        while True:
            choice = self.console.input("\nPlease select an option: ")
            
            if choice == "1":
                self._transition_to(MenuState.URL_INPUT)
                break
            elif choice == "2":
                self._transition_to(MenuState.FILE_INPUT)
                break
            elif choice == "b":
                self._go_back()
                break
            elif choice == "0":
                self._transition_to(MenuState.EXIT)
                break
            else:
                self.console.print("[bold yellow]Invalid option. Please try again.[/bold yellow]")
    
    def _handle_batch_menu(self) -> None:
        """
        Handle the batch conversion menu state.
        
        This is a placeholder for the batch conversion functionality.
        Will be implemented in a future task.
        """
        display_section_header("Batch Conversion", console=self.console)
        
        self.console.print("\n[yellow]Batch conversion is not implemented yet.[/yellow]")
        self.console.print("This feature will be available in a future update.")
        
        # Ask if user wants to go back to main menu
        if prompt_for_continue("Return to main menu?", console=self.console):
            self._go_back()
        else:
            self._transition_to(MenuState.EXIT)
    
    def _handle_url_input(self) -> None:
        """
        Handle the URL input state.
        
        Prompt for a URL to convert and validate the input.
        """
        display_section_header("URL Input", console=self.console)
        
        # Get URL from user
        url = prompt_for_url(console=self.console)
        
        # Store URL in user data
        self.user_data["input_type"] = "url"
        self.user_data["input_path"] = url
        
        # Transition to output directory selection
        self._transition_to(MenuState.OUTPUT_DIR_INPUT)
    
    def _handle_file_input(self) -> None:
        """
        Handle the file input state.
        
        Prompt for a file path to convert and validate the input.
        """
        display_section_header("File Input", console=self.console)
        
        # Get file path from user
        file_path = prompt_for_file(
            message="Enter the path to the document file",
            file_types=["pdf", "doc", "docx"],
            console=self.console
        )
        
        # Determine file type from extension
        file_type = file_path.suffix.lower()[1:]
        
        # Store file information in user data
        self.user_data["input_type"] = file_type
        self.user_data["input_path"] = str(file_path)
        
        # Transition to output directory selection
        self._transition_to(MenuState.OUTPUT_DIR_INPUT)
    
    def _handle_output_dir_input(self) -> None:
        """
        Handle the output directory input state.
        
        Prompt for an output directory and create it if needed.
        """
        display_section_header("Output Directory", console=self.console)
        
        # Get output directory from user
        output_dir = prompt_for_output_directory(console=self.console)
        
        # Store output directory in user data
        self.user_data["output_dir"] = str(output_dir)
        
        # Transition to confirmation
        self._transition_to(MenuState.CONFIRMATION)
    
    def _handle_confirmation(self) -> None:
        """
        Handle the confirmation state.
        
        Display a summary of the conversion parameters and ask for confirmation.
        """
        display_section_header("Confirmation", console=self.console)
        
        # Display conversion details
        self.console.print("\nConversion details:")
        self.console.print(f"Input type: [cyan]{self.user_data.get('input_type', 'unknown')}[/cyan]")
        self.console.print(f"Input path: [cyan]{self.user_data.get('input_path', 'unknown')}[/cyan]")
        self.console.print(f"Output directory: [cyan]{self.user_data.get('output_dir', 'unknown')}[/cyan]")
        
        # Ask for confirmation
        if prompt_for_continue("Proceed with conversion?", console=self.console):
            self._transition_to(MenuState.PROCESSING)
        else:
            # Calculate the correct steps to go back
            # Find the position of SINGLE_ITEM_MENU in the history
            for i, state in enumerate(reversed(self.state_history)):
                if state == MenuState.SINGLE_ITEM_MENU:
                    # Go back to that state
                    self._go_back(steps=i+1)
                    return
                    
            # If SINGLE_ITEM_MENU not found, go back to the main menu as a fallback
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)
    
    def _handle_processing(self) -> None:
        """
        Handle the processing state.
        
        Process the input using the appropriate converter based on
        the input type and store results for display.
        """
        display_section_header("Processing", console=self.console)
        
        # Get input data from user_data
        input_path = self.user_data.get("input_path")
        output_dir = self.user_data.get("output_dir")
        
        if not input_path:
            self.console.print("\n[bold red]Error:[/bold red] No input path specified.")
            self._attempt_recovery("No input path specified")
            return
        
        # Create a single item converter
        from kb_for_prompt.organisms.single_item_converter import SingleItemConverter
        converter = SingleItemConverter(console=self.console)
        
        # Run the conversion process
        success, result_data = converter.run(input_path, output_dir)
        
        # Store results in user_data for the results screen
        self.user_data["conversion_success"] = success
        self.user_data["conversion_results"] = result_data
        
        # Transition to results
        self._transition_to(MenuState.RESULTS)
    
    def _handle_results(self) -> None:
        """
        Handle the results state.
        
        Display conversion results and ask if the user wants to convert more items.
        """
        display_section_header("Results", console=self.console)
        
        # Get conversion results from user_data
        success = self.user_data.get("conversion_success", False)
        results = self.user_data.get("conversion_results", {})
        
        # Display appropriate results based on success/failure
        if success:
            input_type = results.get("input_type", "unknown")
            input_path = results.get("input_path", "unknown")
            output_path = results.get("output_path", "unknown")
            
            # Format the success message
            self.console.print("\n[bold green]✓ Conversion Successful[/bold green]")
            self.console.print(f"Input type: [cyan]{input_type}[/cyan]")
            self.console.print(f"Input: [cyan]{input_path}[/cyan]")
            self.console.print(f"Output: [cyan]{output_path}[/cyan]")
            
            # If it's a file, suggest opening it
            if output_path:
                self.console.print(f"\nYou can find your converted file at: [bold cyan]{output_path}[/bold cyan]")
        else:
            # Display error information
            error_data = results.get("error", {})
            error_type = error_data.get("type", "unknown")
            error_message = error_data.get("message", "Unknown error occurred")
            
            self.console.print("\n[bold red]✗ Conversion Failed[/bold red]")
            self.console.print(f"Error type: [yellow]{error_type}[/yellow]")
            self.console.print(f"Error message: [yellow]{error_message}[/yellow]")
        
        # Ask if user wants to convert more items
        if prompt_for_continue("Would you like to convert another item?", console=self.console):
            # Reset user data and go back to main menu
            self.user_data = {}
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)
        else:
            self._transition_to(MenuState.EXIT)
    
    def _transition_to(self, new_state: MenuState, clear_history: bool = False) -> None:
        """
        Transition to a new menu state.
        
        Args:
            new_state: The new state to transition to
            clear_history: Whether to clear the state history
        """
        # Add current state to history unless clearing history
        if not clear_history and self.current_state != MenuState.EXIT:
            self.state_history.append(self.current_state)
            
            # Limit history size
            while len(self.state_history) > self.max_history:
                self.state_history.pop(0)
        
        # Clear history if requested
        if clear_history:
            self.state_history = []
        
        # Set the new state
        self.current_state = new_state
    
    def _go_back(self, steps: int = 1) -> None:
        """
        Go back to a previous menu state.
        
        Args:
            steps: Number of steps to go back in the history
        """
        # Check if we have enough history to go back
        if len(self.state_history) >= steps:
            # Get the target state
            target_state = self.state_history[-(steps)]
            
            # Remove states from history
            for _ in range(steps):
                if self.state_history:
                    self.state_history.pop()
            
            # Set the current state to the target state
            self.current_state = target_state
        else:
            # Not enough history, go to main menu
            self.current_state = MenuState.MAIN_MENU
            self.state_history = []
    
    def _handle_error(self, error: KbForPromptError) -> bool:
        """
        Handle known application errors with recovery options.
        
        Args:
            error: The error that occurred
            
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        # Different error handling based on error type
        if isinstance(error, ValidationError):
            display_validation_error(
                error_type=error.validation_type or "Validation",
                input_value=error.input_value or "",
                message=error.message,
                details=error.details,
                console=self.console
            )
        elif isinstance(error, ConversionError):
            display_error(
                message=f"Conversion error: {error.message}",
                title=f"{error.conversion_type or 'Conversion'} Error",
                console=self.console
            )
        else:
            display_error(
                message=str(error),
                title="Error",
                console=self.console
            )
        
        # Attempt recovery
        return self._attempt_recovery(error.message)
    
    def _attempt_recovery(self, error_message: str) -> bool:
        """
        Attempt to recover from an error.
        
        Args:
            error_message: The error message to display
            
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        # Present recovery options
        self.console.print("\n[bold]Recovery options:[/bold]")
        options = {
            "1": "Go back to previous menu",
            "2": "Go to main menu",
            "0": "Exit application"
        }
        
        for key, value in options.items():
            self.console.print(f"[green]{key}[/green]: {value}")
        
        # Get user choice
        while True:
            choice = self.console.input("\nPlease select a recovery option: ")
            
            if choice == "1":
                self._go_back()
                return True
            elif choice == "2":
                self._transition_to(MenuState.MAIN_MENU, clear_history=True)
                return True
            elif choice == "0":
                self._transition_to(MenuState.EXIT)
                return True
            else:
                self.console.print("[bold yellow]Invalid option. Please try again.[/bold yellow]")