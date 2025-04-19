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
Banner templates for the kb-for-prompt CLI application.

This module provides functions for displaying application banners and headers
using the Rich library.
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def display_banner(
    console: Optional[Console] = None,
    version: str = "0.1.0",
    subtitle: Optional[str] = None
) -> None:
    """
    Display a styled application banner.
    
    Creates a Rich Panel with the application name "kb-for-prompt" and
    optional version and subtitle information.
    
    Args:
        console: The Rich console to print to. If None, a new console is created.
        version: The application version to display.
        subtitle: An optional subtitle to display below the application name.
    """
    console = console or Console()
    
    # Create a text object for formatting
    text = Text()
    
    # Add title with gradient styling
    text.append("kb-for-prompt", style="bold blue")
    text.append("\n")
    
    # Add version information
    text.append(f"v{version}", style="dim blue")
    text.append("\n\n")
    
    # Add subtitle if provided
    if subtitle:
        text.append(subtitle, style="italic")
    else:
        text.append("Document to Markdown Converter", style="italic")
    
    # Create a panel with the formatted text
    panel = Panel(
        text,
        title="[bold]Welcome[/bold]",
        border_style="blue",
        expand=False,
        padding=(1, 2)
    )
    
    # Print the panel
    console.print(panel)


def display_section_header(
    title: str,
    console: Optional[Console] = None
) -> None:
    """
    Display a section header with consistent styling.
    
    Args:
        title: The title text for the section header.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Create a styled section header
    text = Text(title, style="bold cyan")
    
    # Print the header with some spacing
    console.print()
    console.print(text)
    console.print("─" * min(len(title), 50), style="cyan")