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
Progress indicator templates for the kb-for-prompt CLI application.

This module provides functions for displaying progress bars, spinners, and
status updates during conversion processes using the Rich library and Halo.
"""

import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from rich.console import Console
from rich.progress import (
    Progress, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    TimeRemainingColumn,
    SpinnerColumn
)
from halo import Halo


@contextmanager
def display_spinner(
    text: str,
    success_text: Optional[str] = None,
    console: Optional[Console] = None
) -> Generator[Halo, None, None]:
    """
    Display a spinner with text during a long-running operation.
    
    Args:
        text: The text to display next to the spinner.
        success_text: The text to display upon successful completion.
            If None, defaults to the original text with "Done" prefix.
        console: Not used directly but included for consistent API.
    
    Yields:
        Halo: The spinner instance that can be updated during operation.
    
    Example:
        ```python
        with display_spinner("Processing document") as spinner:
            # Do some work
            spinner.text = "Document loaded, converting..."
            # Do more work
        # Spinner automatically shows success message when context exits
        ```
    """
    spinner = Halo(text=text, spinner="dots")
    spinner.start()
    
    try:
        yield spinner
        # On successful exit from context
        if success_text:
            spinner.succeed(success_text)
        else:
            spinner.succeed(f"Done: {text}")
    except Exception as e:
        # On error exit from context
        spinner.fail(f"Failed: {text} ({str(e)})")
        raise


def display_processing_update(
    message: str,
    status: str = "processing",
    console: Optional[Console] = None
) -> None:
    """
    Display an inline processing status update.
    
    Args:
        message: The message describing what's being processed.
        status: The current status (processing, success, error).
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Define status styles
    status_styles = {
        "processing": "[yellow]⟳[/yellow]",
        "success": "[green]✓[/green]",
        "error": "[red]✗[/red]",
        "warning": "[yellow]⚠[/yellow]",
        "info": "[blue]ℹ[/blue]"
    }
    
    # Get the style or default to info
    status_icon = status_styles.get(status.lower(), status_styles["info"])
    
    # Print the update
    console.print(f"{status_icon} {message}")


def display_completion(
    message: str,
    success: bool = True,
    console: Optional[Console] = None
) -> None:
    """
    Display a completion message for an operation.
    
    Args:
        message: The completion message to display.
        success: Whether the operation was successful.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Choose style based on success
    if success:
        console.print(f"[bold green]✓ {message}[/bold green]")
    else:
        console.print(f"[bold red]✗ {message}[/bold red]")


@contextmanager
def display_progress_bar(
    description: str,
    total: int,
    console: Optional[Console] = None
) -> Generator[Progress, None, None]:
    """
    Display a progress bar for tracking multiple operations.
    
    Args:
        description: The description of the overall task.
        total: The total number of items to process.
        console: The Rich console to print to. If None, a new console is created.
    
    Yields:
        Progress: The Rich Progress instance that can be updated.
    
    Example:
        ```python
        with display_progress_bar("Converting documents", len(docs)) as progress:
            task_id = progress.add_task("Starting...", total=len(docs))
            for i, doc in enumerate(docs):
                # Process document
                progress.update(task_id, 
                               description=f"Converting {doc.name}",
                               advance=1)
        ```
    """
    console = console or Console()
    
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    )
    
    try:
        with progress:
            # Add the main task
            task_id = progress.add_task(description, total=total)
            
            # Extend the Progress object with task_id for convenience
            progress.task_id = task_id
            
            yield progress
    except Exception as e:
        console.print(f"[bold red]Error during progress operation:[/bold red] {str(e)}")
        raise