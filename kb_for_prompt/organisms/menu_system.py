# /// script
# requires-python = ">=3.11"
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
import logging # Added import
from enum import Enum, auto
from pathlib import Path # Added import
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
    prompt_for_continue, # Keep for potential future use
    prompt_for_retry,
    prompt_for_toc_generation, # Import new prompts
    prompt_for_kb_generation,
    prompt_save_confirmation,
    prompt_overwrite_rename, # Import for file saving logic
    prompt_retry_generation, # Import for TOC/KB retry functionality
    MenuOption
)
from kb_for_prompt.templates.errors import (
    display_error,
    display_validation_error,
    display_exception
)
# Added import for spinner
from kb_for_prompt.templates.progress import display_spinner

# Import errors
from kb_for_prompt.atoms.error_utils import (
    KbForPromptError,
    ValidationError,
    ConversionError
)
# Import LlmGenerator
from kb_for_prompt.organisms.llm_generator import LlmGenerator
# Import Condenser function
from kb_for_prompt.organisms.condenser import condense_knowledge_base


class MenuState(Enum):
    """Enumeration of possible menu states."""
    MAIN_MENU = auto()
    SINGLE_ITEM_MENU = auto()
    BATCH_MENU = auto()
    URL_INPUT = auto()
    FILE_INPUT = auto()
    OUTPUT_DIR_INPUT = auto()
    CONFIRMATION = auto()
    BATCH_CONFIRMATION = auto()
    PROCESSING = auto()
    BATCH_PROCESSING = auto()
    RESULTS = auto()
    # TOC states
    TOC_PROMPT = auto()
    TOC_PROCESSING = auto()
    TOC_CONFIRM_SAVE = auto()
    # KB states
    KB_PROMPT = auto()
    KB_PROCESSING = auto()
    KB_CONFIRM_SAVE = auto()
    # KB Condense states
    KB_CONDENSE_PROMPT = auto()
    KB_CONDENSE_PROCESSING = auto()
    EXIT = auto()


class MenuSystem:
    """
    Interactive menu system for navigating between conversion modes.

    This class manages the application's menu states, transitions between states,
    and user input handling. It uses a state machine approach with history tracking
    to enable navigation backwards through menus.
    """

    def __init__(self, console: Optional[Console] = None, llm_client: Optional[Any] = None):
        """
        Initialize the menu system.

        Args:
            console: The Rich console to print to. If None, a new console is created.
            llm_client: Optional LLM client to pass to LlmGenerator.
        """
        self.console = console or Console()
        self.current_state = MenuState.MAIN_MENU
        self.state_history = []
        self.user_data: Dict[str, Any] = {}
        self.max_history = 10  # Maximum number of states to keep in history
        # Instantiate LlmGenerator, passing console and optional llm_client
        self.llm_generator = LlmGenerator(console=self.console, llm_client=llm_client)


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
        elif self.current_state == MenuState.BATCH_CONFIRMATION:
            self._handle_batch_confirmation()
        elif self.current_state == MenuState.PROCESSING:
            self._handle_processing()
        elif self.current_state == MenuState.BATCH_PROCESSING:
            self._handle_batch_processing()
        elif self.current_state == MenuState.RESULTS:
            self._handle_results()
        # TOC states
        elif self.current_state == MenuState.TOC_PROMPT:
            self._handle_toc_prompt()
        elif self.current_state == MenuState.TOC_PROCESSING:
            self._handle_toc_processing()
        elif self.current_state == MenuState.TOC_CONFIRM_SAVE:
            self._handle_toc_confirm_save()
        # KB states
        elif self.current_state == MenuState.KB_PROMPT:
            self._handle_kb_prompt()
        elif self.current_state == MenuState.KB_PROCESSING:
            self._handle_kb_processing()
        elif self.current_state == MenuState.KB_CONFIRM_SAVE:
            self._handle_kb_confirm_save()
        # KB Condense states
        elif self.current_state == MenuState.KB_CONDENSE_PROMPT:
            self._handle_kb_condense_prompt()
        elif self.current_state == MenuState.KB_CONDENSE_PROCESSING:
            self._handle_kb_condense_processing()

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

        Prompt for a CSV file containing inputs and then transition
        to the output directory input state.
        """
        display_section_header("Batch Conversion", console=self.console)

        # Prompt for CSV file
        self.console.print("\nPlease provide a CSV file containing URLs and/or file paths to convert.")
        self.console.print("The CSV file can have one or multiple columns with inputs.")

        # Import the prompt_for_file function from templates
        from kb_for_prompt.templates.prompts import prompt_for_file

        try:
            # Get CSV file path from user
            csv_path = prompt_for_file(
                message="Enter the path to the CSV file",
                file_types=["csv"],
                console=self.console
            )

            # Store CSV path in user data
            self.user_data["csv_path"] = str(csv_path)

            # Transition to output directory input state and return
            # This allows the main loop to handle the next state correctly.
            self._transition_to(MenuState.OUTPUT_DIR_INPUT)
            return # <-- ENSURE THIS RETURN IS HERE

        except Exception as e:
            # Handle potential errors during file prompt (e.g., user cancels)
            # For now, just go back to the main menu. More specific error handling
            # could be added here if needed.
            self.console.print(f"\n[yellow]Operation cancelled or failed: {e}[/yellow]")
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)
            return

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

        Prompt for an output directory, create it if needed, store it,
        and then transition to the appropriate confirmation state based on
        whether we are doing a single item or batch conversion.
        """
        display_section_header("Output Directory", console=self.console)
        # Import prompt functions needed
        from kb_for_prompt.templates.prompts import prompt_for_output_directory

        try:
            # Get output directory from user
            output_dir = prompt_for_output_directory(console=self.console)

            # Store output directory in user data
            self.user_data["output_dir"] = str(output_dir)

            # Determine if we came from BATCH_MENU
            is_batch_conversion = any(state == MenuState.BATCH_MENU for state in self.state_history)

            if is_batch_conversion:
                # If it's a batch conversion, transition to BATCH_CONFIRMATION state
                self._transition_to(MenuState.BATCH_CONFIRMATION)
            else:
                # Otherwise, assume single item conversion and go to standard CONFIRMATION
                self._transition_to(MenuState.CONFIRMATION)

        except Exception as e:
            # Handle potential errors during directory prompt
            self.console.print(f"\n[yellow]Operation cancelled or failed: {e}[/yellow]")
            # Go back to the previous state safely
            self._go_back()

    def _handle_confirmation(self) -> None:
        """
        Handle the confirmation state for SINGLE ITEM conversions.

        Display a summary of the conversion parameters and ask for confirmation.
        """
        # Import prompt functions needed
        from kb_for_prompt.templates.prompts import prompt_for_continue # Re-import for this scope

        display_section_header("Confirmation", console=self.console)

        # Display conversion details for single item
        self.console.print("\nConversion details:")
        self.console.print(f"Input type: [cyan]{self.user_data.get('input_type', 'unknown')}[/cyan]")
        self.console.print(f"Input path: [cyan]{self.user_data.get('input_path', 'unknown')}[/cyan]")
        self.console.print(f"Output directory: [cyan]{self.user_data.get('output_dir', 'unknown')}[/cyan]")

        # Ask for confirmation
        if prompt_for_continue("Proceed with conversion?", console=self.console):
            self._transition_to(MenuState.PROCESSING) # Transition to single item processing
        else:
            # Calculate the correct steps to go back for single item flow
            # Find the position of SINGLE_ITEM_MENU in the history
            for i, state in enumerate(reversed(self.state_history)):
                if state == MenuState.SINGLE_ITEM_MENU:
                    # Go back to that state
                    self._go_back(steps=i+1)
                    return

            # If SINGLE_ITEM_MENU not found, go back to the main menu as a fallback
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)

    def _handle_batch_confirmation(self) -> None:
        """
        Handle the confirmation state specifically for BATCH conversions.

        Display batch details and ask for confirmation before processing.
        """
        # Import prompt functions needed
        from kb_for_prompt.templates.prompts import prompt_for_continue # Re-import for this scope

        display_section_header("Batch Conversion Confirmation", console=self.console)

        # Display conversion details
        self.console.print("\nBatch conversion details:")
        self.console.print(f"CSV File: [cyan]{self.user_data.get('csv_path', 'unknown')}[/cyan]")
        self.console.print(f"Output directory: [cyan]{self.user_data.get('output_dir', 'unknown')}[/cyan]")

        # Ask for confirmation
        if prompt_for_continue("Proceed with batch conversion?", console=self.console):
            # If confirmed, transition to BATCH_PROCESSING state
            self._transition_to(MenuState.BATCH_PROCESSING)
        else:
            # User cancelled, go back to main menu
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)

    def _handle_processing(self) -> None:
        """
        Handle the processing state for SINGLE ITEM conversions.

        Perform the conversion using the SingleItemConverter.
        """
        display_section_header("Processing Single Item", console=self.console) # Clarify title

        # Import SingleItemConverter
        from kb_for_prompt.organisms.single_item_converter import SingleItemConverter

        # Create converter
        converter = SingleItemConverter(console=self.console)

        # Get data from user_data
        input_path = self.user_data.get("input_path")
        output_dir = self.user_data.get("output_dir")

        if not input_path or not output_dir:
             # Handle error: missing necessary data
            self.console.print("[bold red]Error: Missing input path or output directory for single item.[/bold red]")
            self._transition_to(MenuState.MAIN_MENU, clear_history=True) # Go back safely
            return

        # Run the single item conversion
        success, result_data = converter.run(input_path, output_dir)

        # Store results in user_data for the results screen
        self.user_data["single_conversion_success"] = success # Use unique key
        self.user_data["single_conversion_results"] = result_data # Use unique key

        # Transition to the RESULTS state
        self._transition_to(MenuState.RESULTS)

    def _handle_batch_processing(self) -> None:
        """
        Handle the processing state specifically for BATCH conversions.

        Perform the batch conversion using the BatchConverter.
        """
        display_section_header("Batch Processing", console=self.console)

        # Import BatchConverter
        from kb_for_prompt.organisms.batch_converter import BatchConverter

        # Create batch converter
        batch_converter = BatchConverter(console=self.console)

        # Get data from user_data
        csv_path = self.user_data.get("csv_path")
        output_dir = self.user_data.get("output_dir")

        if not csv_path or not output_dir:
            # Handle error: missing necessary data
            self.console.print("[bold red]Error: Missing CSV path or output directory for batch.[/bold red]")
            self._transition_to(MenuState.MAIN_MENU, clear_history=True) # Go back safely
            return

        # Run the batch conversion
        success, result_data = batch_converter.run(csv_path, output_dir)

        # Store results in user_data for the results screen
        self.user_data["batch_conversion_success"] = success # Use unique key
        self.user_data["batch_conversion_results"] = result_data # Use unique key

        # Transition to the RESULTS state
        self._transition_to(MenuState.RESULTS)

    def _handle_results(self) -> None:
        """
        Handle the results state for both single and batch conversions.

        Display the conversion results and transition to TOC prompt.
        """
        # Check if it was a batch conversion by looking for specific keys in user_data
        is_batch_conversion = "batch_conversion_success" in self.user_data

        if is_batch_conversion:
            display_section_header("Batch Conversion Results", console=self.console)
            results = self.user_data.get("batch_conversion_results", {})
            success = self.user_data.get("batch_conversion_success", False)
            total = results.get("total", 0)
            successful = results.get("successful", [])
            failed = results.get("failed", [])
            output_dir_res = results.get("output_dir", "") # Use different var name

            # Display summary
            if success:
                self.console.print(f"\n[bold green]✓ Batch Conversion Completed[/bold green]")
                self.console.print(f"Total inputs: [cyan]{total}[/cyan]")
                self.console.print(f"Successfully converted: [green]{len(successful)}[/green]")
                self.console.print(f"Failed conversions: [yellow]{len(failed)}[/yellow]")
                self.console.print(f"Output directory: [cyan]{output_dir_res}[/cyan]")
            else:
                self.console.print(f"\n[bold red]✗ Batch Conversion Failed[/bold red]")
                if total > 0:
                    self.console.print(f"Total inputs: [cyan]{total}[/cyan]")
                    self.console.print(f"Successfully converted: [green]{len(successful)}[/green]")
                    self.console.print(f"Failed conversions: [yellow]{len(failed)}[/yellow]")

                error_type = results.get("error", {}).get("type", "unknown")
                error_message = results.get("error", {}).get("message", "Unknown error occurred")
                if error_type != "unknown" and error_message: # Check if error info exists
                     self.console.print(f"Error type: [yellow]{error_type}[/yellow]")
                     self.console.print(f"Error message: [yellow]{error_message}[/yellow]")

        else:
            # Assume single item conversion (Check for single item keys)
            is_single_conversion = "single_conversion_success" in self.user_data
            if is_single_conversion:
                display_section_header("Conversion Result", console=self.console)
                results = self.user_data.get("single_conversion_results", {})
                success = self.user_data.get("single_conversion_success", False)
                input_path = results.get("input_path", "unknown")
                output_path_res = results.get("output_path", "") # Use different var name
                error = results.get("error")

                if success:
                    self.console.print(f"\n[bold green]✓ Conversion Successful[/bold green]")
                    self.console.print(f"Input: [cyan]{input_path}[/cyan]")
                    self.console.print(f"Output: [cyan]{output_path_res}[/cyan]")
                else:
                    self.console.print(f"\n[bold red]✗ Conversion Failed[/bold red]")
                    self.console.print(f"Input: [cyan]{input_path}[/cyan]")
                    if error:
                        self.console.print(f"Error type: [yellow]{error.get('type', 'unknown')}[/yellow]")
                        self.console.print(f"Error message: [yellow]{error.get('message', 'Unknown error')}[/yellow]")
            else:
                # Fallback if neither batch nor single keys are found
                self.console.print("[bold yellow]Warning: Could not determine conversion type for results.[/bold yellow]")


        # --- MODIFIED PART ---
        # Instead of asking to continue, directly transition to TOC prompt
        self.console.print("\n[bold]Proceeding to Table of Contents generation...[/bold]")
        self._transition_to(MenuState.TOC_PROMPT)
        # --- END MODIFIED PART ---

    # --- TOC HANDLERS ---

    def _handle_toc_prompt(self) -> None:
        """
        Handle prompting the user whether to generate a Table of Contents (TOC).

        This method explains the TOC generation step and uses the
        `prompt_for_toc_generation` function to get the user's choice.
        Based on the response, it transitions to either the TOC processing state
        or skips directly to the Knowledge Base (KB) prompt state.
        """
        display_section_header("Generate Table of Contents", console=self.console)
        self.console.print("\nAfter conversion, you can optionally generate a Table of Contents (TOC)")
        self.console.print("for the Markdown files in the output directory using an LLM.")
        self.console.print("This helps organize the converted documents.")

        # Ask if user wants TOC
        if prompt_for_toc_generation(console=self.console):
            self._transition_to(MenuState.TOC_PROCESSING)
        else:
            # If no TOC, skip to KB prompt
            self._transition_to(MenuState.KB_PROMPT)

    def _handle_toc_processing(self) -> None:
        """
        Handle the TOC generation process using LlmGenerator.

        Retrieves the output directory, calls the LLM generator, handles
        potential errors, stores the result, and transitions to the next state.
        """
        display_section_header("Generating Table of Contents", console=self.console)

        # Retrieve output directory from user data
        output_dir_str = self.user_data.get('output_dir')
        if not output_dir_str:
            self.console.print("[bold red]Error: Output directory not found in user data. Skipping TOC generation.[/bold red]")
            logging.error("Output directory missing in user_data during TOC processing.")
            self._transition_to(MenuState.KB_PROMPT) # Skip to KB prompt
            return

        try:
            output_dir = Path(output_dir_str)
        except Exception as e:
            self.console.print(f"[bold red]Error: Invalid output directory path '{output_dir_str}'. Skipping TOC generation.[/bold red]")
            logging.error(f"Invalid output directory path '{output_dir_str}': {e}", exc_info=True)
            self._transition_to(MenuState.KB_PROMPT) # Skip to KB prompt
            return

        toc_content = None # Initialize toc_content
        try:
            # Use spinner while calling the LLM
            with display_spinner("Calling LLM for TOC generation...", console=self.console) as spinner:
                # Call the LlmGenerator to generate the TOC
                # Note: This requires self.llm_generator to be initialized with a working client
                # or it will likely return None based on LlmGenerator's internal checks.
                toc_content = self.llm_generator.generate_toc(output_dir)
                if toc_content is None:
                    spinner.fail("TOC generation failed or returned no content.")
                else:
                    spinner.succeed("TOC generation successful.")

        except Exception as e:
            # Log the exception and inform the user
            logging.error(f"An unexpected error occurred during TOC generation: {e}", exc_info=True)
            self.console.print(f"\n[bold red]An error occurred during TOC generation: {e}[/bold red]")
            toc_content = None # Ensure toc_content is None on error

        # Store the generated content (or None if failed/error)
        self.user_data['generated_toc_content'] = toc_content

        # Transition based on whether TOC content was generated
        if toc_content is not None:
            self._transition_to(MenuState.TOC_CONFIRM_SAVE)
        else:
            # If generation failed or an error occurred, skip confirmation and go to KB prompt
            self.console.print("[yellow]Skipping TOC saving due to generation failure or error.[/yellow]")
            self._transition_to(MenuState.KB_PROMPT)


    def _save_content_to_file(self, content: str, target_path: Path) -> Optional[Path]:
        """
        Save content to a file, handling existing files and potential errors.

        Args:
            content: The string content to save.
            target_path: The Path object representing the desired save location.

        Returns:
            Optional[Path]: The Path object of the successfully saved file (which might
                            be different from target_path if renamed), or None if saving
                            failed or was cancelled.
        """
        current_target_path = target_path # Keep track of the path we intend to write to

        try:
            # Check if the file already exists
            if current_target_path.exists():
                choice, new_filename = prompt_overwrite_rename(str(current_target_path), console=self.console)

                if choice == "overwrite":
                    self.console.print(f"Overwriting existing file: {current_target_path}")
                elif choice == "rename":
                    if new_filename:
                        # Construct the new path in the same directory
                        new_path = current_target_path.parent / new_filename
                        self.console.print(f"Renaming file to: {new_path}")
                        current_target_path = new_path # Update the target path
                    else:
                        # Should not happen if prompt_overwrite_rename works correctly, but handle defensively
                        self.console.print("[bold red]Error:[/bold red] Rename chosen but no new filename provided. Save cancelled.")
                        return None
                elif choice == "cancel":
                    self.console.print("Save operation cancelled by user.")
                    return None
                else:
                    # Should not happen
                    self.console.print(f"[bold red]Error:[/bold red] Unexpected choice '{choice}' from prompt. Save cancelled.")
                    return None

            # Ensure the parent directory exists (might be needed for renamed files too)
            current_target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content to the final target file
            current_target_path.write_text(content, encoding="utf-8")
            logging.info(f"Successfully saved content to {current_target_path}")
            self.console.print(f"[green]Content successfully saved to:[/green] {current_target_path}") # Added success message here
            return current_target_path # Return the actual path saved

        except (IOError, OSError) as e:
            logging.error(f"Failed to save content to {current_target_path}: {e}", exc_info=True)
            self.console.print(f"[bold red]Error saving file {current_target_path}:[/bold red] {e}")
            return None
        except Exception as e:
            # Catch any other unexpected errors during the process
            logging.error(f"An unexpected error occurred during file save to {current_target_path}: {e}", exc_info=True)
            self.console.print(f"[bold red]An unexpected error occurred while saving file {current_target_path}:[/bold red] {e}")
            return None

    def _handle_toc_confirm_save(self) -> None:
        """
        Handle confirming and saving the generated TOC.

        Retrieves generated TOC content and output directory from user_data,
        creates a preview, asks for confirmation, and either saves the file
        or asks if the user wants to retry generation. Then transitions to
        the appropriate next state.
        """
        display_section_header("Save Table of Contents", console=self.console)

        # Retrieve the content from user_data
        toc_content = self.user_data.get("generated_toc_content")
        output_dir_str = self.user_data.get("output_dir")

        # Handle missing content case
        if toc_content is None:
            self.console.print("[bold red]Error:[/bold red] TOC content not found in user data. Cannot proceed with saving.")
            self._transition_to(MenuState.KB_PROMPT)  # Skip to KB prompt
            return

        # Handle missing output_dir case
        if not output_dir_str:
            self.console.print("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
            self._transition_to(MenuState.KB_PROMPT)  # Skip to KB prompt
            return

        # Generate preview (first 50 lines)
        lines = toc_content.splitlines()[:50]
        preview = "\n".join(lines)

        # Add indicator if content was truncated for preview
        if len(toc_content.splitlines()) > 50:
            preview += "\n[italic](... preview truncated ...)[/italic]"

        # Ask user whether to save
        if prompt_save_confirmation(preview, console=self.console):
            # User confirmed save - determine target path
            try:
                output_dir = Path(output_dir_str)
                target_path = output_dir / "toc.md"

                self.console.print(f"Preparing to save TOC to: {target_path}")

                # Call the enhanced save method
                saved_path = self._save_content_to_file(toc_content, target_path)

                # Handle save result
                if saved_path:
                    # Success message handled by save function
                    pass
                else:
                    # Failure or cancellation message handled by save function
                    pass

                # Transition to KB prompt regardless of save outcome
                self._transition_to(MenuState.KB_PROMPT)

            except Exception as e:
                logging.error(f"Error preparing to save TOC: {e}", exc_info=True)
                self.console.print(f"[bold red]Error preparing to save TOC:[/bold red] {e}")
                self._transition_to(MenuState.KB_PROMPT) # Still transition
        else:
            # User declined to save - ask about retrying
            self.console.print("Save confirmation declined by user.")

            if prompt_retry_generation("TOC generation", console=self.console):
                # User wants to retry
                self.console.print("Retrying TOC generation...")
                self._transition_to(MenuState.TOC_PROCESSING)
            else:
                # User doesn't want to retry
                self.console.print("Skipping TOC generation retry.")
                self._transition_to(MenuState.KB_PROMPT)

    # --- KB HANDLERS ---

    def _ask_convert_another(self) -> None:
        """
        Ask the user if they want to perform another conversion.

        Transitions to MAIN_MENU if yes, EXIT if no.
        """
        if prompt_for_continue("Would you like to perform another conversion?", console=self.console):
            self.user_data = {} # Clear data for next run
            self._transition_to(MenuState.MAIN_MENU, clear_history=True)
        else:
            self._transition_to(MenuState.EXIT)

    def _handle_kb_prompt(self) -> None:
        """
        Handle prompting the user whether to generate a Knowledge Base (KB).

        Asks the user and transitions to KB processing or asks to start over/exit.
        """
        # Display the section header
        display_section_header("Knowledge Base Generation", console=self.console)
        # Print explanatory text
        self.console.print("\nOptionally, generate a Knowledge Base (KB) in Markdown format") # Updated format
        self.console.print("from the Markdown files using an LLM.")
        self.console.print("This can be useful for further processing or RAG systems.")

        # Ask if user wants KB generation using the imported prompt function
        if prompt_for_kb_generation(console=self.console):
            # If yes, transition to KB processing state
            self._transition_to(MenuState.KB_PROCESSING)
        else:
            # If no, ask if they want to perform another conversion using the helper method
            self._ask_convert_another()


    def _handle_kb_processing(self) -> None:
        """
        Handle the Knowledge Base (KB) generation process using LlmGenerator.

        Retrieves the output directory, calls the LLM generator, handles
        potential errors, stores the result, and transitions to the next state.
        """
        display_section_header("Generating Knowledge Base", console=self.console)

        # Retrieve output directory from user data
        output_dir_str = self.user_data.get('output_dir')
        if not output_dir_str:
            self.console.print("[bold red]Error: Output directory not found in user data. Skipping KB generation.[/bold red]")
            logging.error("Output directory missing in user_data during KB processing.")
            self._ask_convert_another() # Ask to continue/exit
            return

        try:
            output_dir = Path(output_dir_str)
        except Exception as e:
            self.console.print(f"[bold red]Error: Invalid output directory path '{output_dir_str}'. Skipping KB generation.[/bold red]")
            logging.error(f"Invalid output directory path '{output_dir_str}': {e}", exc_info=True)
            self._ask_convert_another() # Ask to continue/exit
            return

        kb_content = None # Initialize kb_content
        try:
            # Use spinner while calling the LLM
            with display_spinner("Calling LLM for KB generation...", console=self.console) as spinner:
                # Call the LlmGenerator to generate the KB
                # Assuming LlmGenerator has a generate_kb method similar to generate_toc
                # If not, this needs adjustment based on LlmGenerator's actual interface
                kb_content = self.llm_generator.generate_kb(output_dir) # Assuming generate_kb exists
                if kb_content is None:
                    spinner.fail("KB generation failed or returned no content.")
                else:
                    spinner.succeed("KB generation successful.")

        except AttributeError:
             # Handle case where generate_kb doesn't exist on llm_generator
            logging.error("LlmGenerator does not have a 'generate_kb' method.", exc_info=True)
            self.console.print("[bold red]Error: KB generation functionality is not available.[/bold red]")
            kb_content = None
        except Exception as e:
            # Log the exception and inform the user
            logging.error(f"An unexpected error occurred during KB generation: {e}", exc_info=True)
            self.console.print(f"\n[bold red]An error occurred during KB generation: {e}[/bold red]")
            kb_content = None # Ensure kb_content is None on error

        # Store the generated content (or None if failed/error)
        self.user_data['generated_kb_content'] = kb_content

        # Transition based on whether KB content was generated
        if kb_content is not None:
            self._transition_to(MenuState.KB_CONFIRM_SAVE)
        else:
            # If generation failed or an error occurred, skip confirmation and ask to continue/exit
            self.console.print("[yellow]Skipping KB saving due to generation failure or error.[/yellow]")
            self._ask_convert_another()


    def _handle_kb_confirm_save(self) -> None:
        """
        Handle confirming and saving the generated Knowledge Base (KB).

        Retrieves generated KB content and output directory from user_data,
        creates a preview, asks for confirmation, saves the file (handling overwrite/rename),
        stores the final KB path in user_data, and transitions to the KB condensation prompt.
        If saving is declined or fails, it handles retries or transitions appropriately.
        """
        display_section_header("Save Knowledge Base", console=self.console)

        # Retrieve the content from user_data
        kb_content = self.user_data.get("generated_kb_content")
        output_dir_str = self.user_data.get("output_dir")

        # Handle missing content case
        if kb_content is None:
            self.console.print("[bold red]Error:[/bold red] KB content not found in user data. Cannot proceed with saving.")
            self._ask_convert_another() # Ask to continue/exit
            return

        # Handle missing output_dir case
        if not output_dir_str:
            self.console.print("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
            self._ask_convert_another() # Ask to continue/exit
            return

        # Generate preview (first 50 lines)
        lines = kb_content.splitlines()[:50]
        preview = "\n".join(lines)

        # Add indicator if content was truncated for preview
        if len(kb_content.splitlines()) > 50:
            preview += "\n[italic](... preview truncated ...)[/italic]"

        # Determine the default target path
        try:
            output_dir = Path(output_dir_str)
            default_target_path = output_dir / "knowledge_base.md"
        except Exception as e:
            logging.error(f"Error creating default KB path from '{output_dir_str}': {e}", exc_info=True)
            self.console.print(f"[bold red]Error determining default save path for KB:[/bold red] {e}")
            self._ask_convert_another() # Ask to continue/exit on error
            return

        # Ask user whether to save
        if prompt_save_confirmation(preview, console=self.console):
            # User confirmed save
            self.console.print(f"Preparing to save KB to: {default_target_path}")

            # Call the enhanced save method
            saved_kb_path = self._save_content_to_file(kb_content, default_target_path)

            # Handle save result
            if saved_kb_path:
                # Store the actual saved path (might be renamed)
                self.user_data['kb_file_path'] = saved_kb_path
                # Transition to condensation prompt
                self._transition_to(MenuState.KB_CONDENSE_PROMPT)
            else:
                # Save failed or was cancelled by user during overwrite/rename prompt
                self.console.print("[yellow]KB saving failed or was cancelled.[/yellow]")
                # Ask to convert another, as condensation requires the file
                self._ask_convert_another()

        else:
            # User declined to save initially - ask about retrying generation
            self.console.print("Save confirmation declined by user.")

            if prompt_retry_generation("KB generation", console=self.console):
                # User wants to retry generation
                self.console.print("Retrying KB generation...")
                self._transition_to(MenuState.KB_PROCESSING)
            else:
                # User doesn't want to retry generation, but we still have the content.
                # Store the *intended* path so condensation *might* still work if the file
                # somehow exists from a previous run (less likely, but allows the flow).
                # Or, maybe we should just skip condensation if they decline saving?
                # Let's skip condensation if they decline saving the KB.
                self.console.print("Skipping KB generation retry and condensation as save was declined.")
                self._ask_convert_another() # Ask to continue/exit

    # --- KB CONDENSE HANDLERS ---

    def _handle_kb_condense_prompt(self) -> None:
        """
        Handle prompting the user whether to condense the generated Knowledge Base.
        """
        display_section_header("Condense Knowledge Base", console=self.console)

        # Check if we have a KB file path from the previous step
        kb_file_path_obj = self.user_data.get('kb_file_path')
        if not kb_file_path_obj or not isinstance(kb_file_path_obj, Path):
            self.console.print("[bold yellow]Warning:[/bold yellow] Knowledge base file path not found or invalid. Skipping condensation.")
            logging.warning("kb_file_path missing or not a Path object in user_data for condensation prompt.")
            self._ask_convert_another()
            return

        # Check if the file actually exists (it should if save was successful)
        if not kb_file_path_obj.is_file():
             self.console.print(f"[bold yellow]Warning:[/bold yellow] Knowledge base file '{kb_file_path_obj}' not found. Skipping condensation.")
             logging.warning(f"KB file '{kb_file_path_obj}' not found before asking for condensation.")
             self._ask_convert_another()
             return

        self.console.print("\nYou can now optionally condense the generated Knowledge Base file")
        self.console.print(f"('{kb_file_path_obj.name}') using an LLM.")
        self.console.print("This creates a more concise version focused on key information.")

        # Ask if user wants to condense using a generic confirmation prompt
        if prompt_for_continue("Condense the Knowledge Base?", console=self.console):
            self._transition_to(MenuState.KB_CONDENSE_PROCESSING)
        else:
            self.console.print("Skipping Knowledge Base condensation.")
            self._ask_convert_another()

    def _handle_kb_condense_processing(self) -> None:
        """
        Handle the Knowledge Base (KB) condensation process using the condenser function.
        """
        display_section_header("Condensing Knowledge Base", console=self.console)

        # Retrieve the KB file path from user data
        kb_file_path = self.user_data.get('kb_file_path')
        if not kb_file_path or not isinstance(kb_file_path, Path):
            self.console.print("[bold red]Error:[/bold red] Knowledge base file path not found in user data. Cannot condense.")
            logging.error("kb_file_path missing or invalid in user_data during KB condensation processing.")
            self._ask_convert_another()
            return

        condensed_kb_path: Optional[Path] = None
        try:
            # Use spinner while calling the condenser function
            with display_spinner(f"Calling LLM to condense '{kb_file_path.name}'...", console=self.console) as spinner:
                # Call the condense_knowledge_base function
                condensed_kb_path = condense_knowledge_base(kb_file_path)

                if condensed_kb_path:
                    spinner.succeed(f"KB condensation successful. Output: {condensed_kb_path.name}")
                else:
                    # condense_knowledge_base logs errors internally, so just fail spinner
                    spinner.fail("KB condensation failed. Check logs for details.")

        except Exception as e:
            # Catch unexpected errors during the call or context management
            logging.error(f"An unexpected error occurred during KB condensation: {e}", exc_info=True)
            self.console.print(f"\n[bold red]An unexpected error occurred during condensation: {e}[/bold red]")
            condensed_kb_path = None # Ensure path is None on error

        # Store the path of the condensed file (or None if failed)
        self.user_data['condensed_kb_file_path'] = condensed_kb_path

        # Always transition to ask if user wants to convert another item
        self._ask_convert_another()

    # --- END KB CONDENSE HANDLERS ---

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

