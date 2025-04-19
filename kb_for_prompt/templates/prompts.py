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
Interactive prompt templates for the kb-for-prompt CLI application.

This module provides functions for displaying menus, input prompts, and
confirmation dialogs using the Rich library and Click.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm


class MenuOption(Enum):
    """Enumeration of main menu options."""
    SINGLE_ITEM = "1"
    BATCH = "2"
    EXIT = "0"


def display_main_menu(console: Optional[Console] = None) -> str:
    """
    Display a styled main menu with options for batch and single item conversion.
    
    Args:
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        str: The selected menu option (from MenuOption enum).
    """
    console = console or Console()
    
    # Create a table for menu options
    table = Table(show_header=False, box=None)
    table.add_column("Option", style="green", justify="right")
    table.add_column("Description", style="white")
    
    # Add menu options
    table.add_row(MenuOption.SINGLE_ITEM.value, "Convert a single URL or file")
    table.add_row(MenuOption.BATCH.value, "Convert multiple items from a CSV file")
    table.add_row(MenuOption.EXIT.value, "Exit the application")
    
    # Create the menu panel
    panel = Panel(
        table,
        title="[bold]Main Menu[/bold]",
        border_style="green",
        expand=False
    )
    
    # Print the menu
    console.print(panel)
    
    # Get user input
    while True:
        choice = Prompt.ask(
            "Please select an option",
            choices=[option.value for option in MenuOption],
            default=MenuOption.SINGLE_ITEM.value
        )
        
        if choice in [option.value for option in MenuOption]:
            return choice


def prompt_for_file(
    message: str = "Enter the path to the file",
    default: Optional[str] = None,
    must_exist: bool = True,
    file_types: Optional[List[str]] = None,
    console: Optional[Console] = None
) -> Path:
    """
    Prompt the user for a file path with validation.
    
    Args:
        message: The prompt message to display.
        default: Optional default value to suggest.
        must_exist: Whether the file must already exist.
        file_types: Optional list of allowed file extensions (without dot).
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        Path: The validated file path.
    """
    console = console or Console()
    
    # Format file types for display
    file_types_str = ""
    if file_types:
        file_types_str = f" ({', '.join(f'.{ft}' for ft in file_types)})"
    
    while True:
        # Prompt for input
        path_str = Prompt.ask(
            f"[bold green]{message}{file_types_str}[/bold green]",
            default=default or ""
        )
        
        # Convert to Path
        path = Path(path_str)
        
        # Check if file exists (if required)
        if must_exist and not path.is_file():
            console.print(f"[bold red]Error:[/bold red] File {path} does not exist. Please enter a valid file path.")
            continue
        
        # Check file extension (if specified)
        if file_types and path.suffix.lower()[1:] not in [ft.lower() for ft in file_types]:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] File {path} does not have an expected extension "
                f"({', '.join(f'.{ft}' for ft in file_types)}). Do you want to continue?"
            )
            if not Confirm.ask("Continue with this file?"):
                continue
        
        return path


def prompt_for_directory(
    message: str = "Enter the directory path",
    default: Optional[str] = None,
    must_exist: bool = True,
    create_if_missing: bool = False,
    console: Optional[Console] = None
) -> Path:
    """
    Prompt the user for a directory path with validation.
    
    Args:
        message: The prompt message to display.
        default: Optional default value to suggest.
        must_exist: Whether the directory must already exist.
        create_if_missing: Whether to create the directory if it doesn't exist.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        Path: The validated directory path.
    """
    console = console or Console()
    
    while True:
        # Prompt for input
        path_str = Prompt.ask(
            f"[bold green]{message}[/bold green]",
            default=default or ""
        )
        
        # Convert to Path
        path = Path(path_str)
        
        # Check if directory exists
        if not path.exists():
            if must_exist and not create_if_missing:
                console.print(f"[bold red]Error:[/bold red] Directory {path} does not exist. Please enter a valid directory path.")
                continue
            elif create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    console.print(f"[green]Created directory:[/green] {path}")
                except Exception as e:
                    console.print(f"[bold red]Error creating directory:[/bold red] {str(e)}")
                    continue
        elif not path.is_dir():
            console.print(f"[bold red]Error:[/bold red] {path} is not a directory. Please enter a valid directory path.")
            continue
        
        return path


def prompt_for_output_directory(
    message: str = "Enter the output directory for markdown files",
    default: Optional[str] = None,
    console: Optional[Console] = None
) -> Path:
    """
    Prompt the user for an output directory with automatic creation.
    
    This is a specialized version of prompt_for_directory that always creates
    the directory if it doesn't exist.
    
    Args:
        message: The prompt message to display.
        default: Optional default value to suggest.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        Path: The validated output directory path.
    """
    return prompt_for_directory(
        message=message,
        default=default,
        must_exist=False,
        create_if_missing=True,
        console=console
    )


def prompt_for_url(
    message: str = "Enter the URL to convert",
    console: Optional[Console] = None
) -> str:
    """
    Prompt the user for a URL with basic validation.
    
    Args:
        message: The prompt message to display.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        str: The validated URL.
    """
    console = console or Console()
    
    while True:
        # Prompt for input
        url = Prompt.ask(f"[bold green]{message}[/bold green]")
        
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            console.print("[bold yellow]Warning:[/bold yellow] URL should start with http:// or https://.")
            
            # Add prefix if user confirms
            if Confirm.ask("Add 'https://' prefix?"):
                url = f"https://{url}"
            elif not Confirm.ask("Continue with this URL anyway?"):
                continue
        
        return url


def prompt_for_retry(
    error_message: str,
    retry_count: int = 0,
    max_retries: int = 3,
    console: Optional[Console] = None
) -> bool:
    """
    Ask the user if they want to retry a failed operation.
    
    Args:
        error_message: The error message to display.
        retry_count: Current retry count.
        max_retries: Maximum number of retries allowed.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to retry, False otherwise.
    """
    console = console or Console()
    
    # Display error message
    console.print(f"[bold red]Error:[/bold red] {error_message}")
    
    # Check if max retries reached
    retries_remaining = max_retries - retry_count
    if retries_remaining <= 0:
        console.print("[yellow]Maximum retry attempts reached.[/yellow]")
        return False
    
    # Prompt for retry
    return Confirm.ask(
        f"Would you like to retry? ({retries_remaining} {'attempts' if retries_remaining > 1 else 'attempt'} remaining)",
        default=True
    )


def prompt_for_continue(
    message: str = "Would you like to convert another file?",
    console: Optional[Console] = None
) -> bool:
    """
    Ask the user if they want to continue with another operation.
    
    Args:
        message: The prompt message to display.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to continue, False otherwise.
    """
    console = console or Console()
    
    return Confirm.ask(f"[bold green]{message}[/bold green]", default=True)


def prompt_for_toc_generation(console: Optional[Console] = None) -> bool:
    """
    Ask the user if they want to generate a table of contents.
    
    Args:
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to generate TOC, False otherwise.
    """
    console = console or Console()
    
    return Confirm.ask(
        "[bold green]Would you like to generate a table of contents? (y/n)[/bold green]",
        default=True
    )


def prompt_for_kb_generation(console: Optional[Console] = None) -> bool:
    """
    Ask the user if they want to generate a single-file knowledge base.
    
    Args:
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to generate KB, False otherwise.
    """
    console = console or Console()
    
    return Confirm.ask(
        "[bold green]Would you like to generate a single-file knowledge base from the documents? (y/n)[/bold green]",
        default=True
    )


def prompt_save_confirmation(content_preview: str, console: Optional[Console] = None) -> bool:
    """
    Display a preview of generated content and ask for confirmation to save.
    
    Args:
        content_preview: The content to preview (first 50 lines).
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to save the content, False otherwise.
    """
    console = console or Console()
    
    # Display preview in a panel
    preview_panel = Panel(
        content_preview,
        title="[bold]Content Preview[/bold]",
        border_style="green",
        expand=False
    )
    console.print(preview_panel)
    
    # Get confirmation
    return Confirm.ask(
        "[bold green]Do you want to save this file? (y/n)[/bold green]",
        default=True
    )


def prompt_overwrite_rename(filename: str, console: Optional[Console] = None) -> Tuple[str, Optional[str]]:
    """
    Handle the case where a file already exists.
    
    Args:
        filename: The name of the file that already exists.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        Tuple containing:
            - choice: 'overwrite', 'rename', or 'cancel'
            - new_filename: If 'rename' is chosen, the new filename; otherwise None
    """
    console = console or Console()
    
    # Inform the user
    console.print(f"[bold yellow]Warning:[/bold yellow] File {filename} already exists.")
    
    # Get user choice
    choice = Prompt.ask(
        "Overwrite, Rename, or Cancel?",
        choices=["o", "r", "c"],
        default="o"
    ).lower()
    
    # Process choice
    if choice == "o":
        return ("overwrite", None)
    elif choice == "r":
        # Suggest a default new name (append _1 before extension)
        path = Path(filename)
        default_new_name = f"{path.stem}_1{path.suffix}"
        
        # Ask for new filename
        while True:
            new_name = Prompt.ask(
                "Enter new filename",
                default=default_new_name
            )
            
            if new_name.strip():
                return ("rename", new_name)
            else:
                console.print("[bold red]Error:[/bold red] Filename cannot be empty.")
    else:  # choice == "c"
        return ("cancel", None)


def prompt_retry_generation(process_name: str = "generation", console: Optional[Console] = None) -> bool:
    """
    Ask the user if they want to retry a generation process.
    
    Args:
        process_name: Name of the process to retry.
        console: The Rich console to print to. If None, a new console is created.
    
    Returns:
        bool: True if user wants to retry, False otherwise.
    """
    console = console or Console()
    
    return Confirm.ask(
        f"[bold green]Do you want to retry the {process_name} process? (y/n)[/bold green]",
        default=True
    )