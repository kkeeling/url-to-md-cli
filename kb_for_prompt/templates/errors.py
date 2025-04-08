# /// script
# requires-python = ">=3.12"
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
Error message templates for the kb-for-prompt CLI application.

This module provides functions for displaying validation errors, conversion errors,
and other exception types with appropriate styling using the Rich library.
"""

import sys
import traceback
from typing import Any, Dict, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback


def display_error(
    message: str,
    title: str = "Error",
    exit_code: Optional[int] = None,
    console: Optional[Console] = None
) -> None:
    """
    Display a formatted error message.
    
    Args:
        message: The error message to display.
        title: The title for the error message.
        exit_code: If provided, exit the program with this code.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Create an error panel
    panel = Panel(
        message,
        title=f"[bold]{title}[/bold]",
        border_style="red",
        expand=False
    )
    
    # Print the error panel
    console.print(panel)
    
    # Exit if requested
    if exit_code is not None:
        sys.exit(exit_code)


def display_validation_error(
    error_type: str,
    input_value: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    console: Optional[Console] = None
) -> None:
    """
    Display a formatted validation error message.
    
    Args:
        error_type: The type of validation error (e.g., "File not found").
        input_value: The invalid input value.
        message: The error message explaining the validation failure.
        details: Optional dictionary with additional error details.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Format the message
    error_message = f"[bold red]{error_type}[/bold red]\n\n"
    error_message += f"Input: [yellow]{input_value}[/yellow]\n"
    error_message += f"Error: {message}\n"
    
    # Add details if provided
    if details:
        error_message += "\n[bold]Details:[/bold]\n"
        for key, value in details.items():
            error_message += f"- {key}: {value}\n"
    
    # Create and print the panel
    panel = Panel(
        error_message.strip(),
        title="[bold]Validation Error[/bold]",
        border_style="red",
        expand=False
    )
    
    console.print(panel)


def display_exception(
    exception: Exception,
    show_traceback: bool = False,
    exit_program: bool = False,
    console: Optional[Console] = None
) -> None:
    """
    Display a formatted exception message.
    
    Args:
        exception: The exception to display.
        show_traceback: Whether to show the full traceback.
        exit_program: Whether to exit the program after displaying the error.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Extract exception class name
    exception_type = exception.__class__.__name__
    
    if show_traceback:
        # Show rich formatted traceback
        console.print(
            Traceback.from_exception(
                exc_type=type(exception),
                exc_value=exception,
                traceback=exception.__traceback__,
                width=100,
                show_locals=False
            )
        )
    else:
        # Show simple error message
        error_message = f"[bold red]{exception_type}:[/bold red] {str(exception)}"
        console.print(error_message)
    
    # Exit if requested
    if exit_program:
        sys.exit(1)