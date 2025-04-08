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
KB for Prompt - Document to Markdown Converter

This script provides a CLI tool to convert online and local documents
(URLs, Word, and PDF files) into Markdown files using the docling library.
It supports both batch conversion (using a CSV file with a mix of URLs and
file paths) and single item conversion modes via an interactive menu.

Usage:
    # Install and run with uv
    uv run --script kb_for_prompt.py
    
    # If installed locally
    python kb_for_prompt.py
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import click
from rich.console import Console

from kb_for_prompt.organisms.menu_system import MenuSystem

# Define version directly to avoid import issues
__version__ = "0.1.0"


@click.command()
@click.version_option(version=__version__)
def main():
    """KB for Prompt - Document to Markdown Converter.
    
    A CLI tool that converts online and local documents (URLs, Word, and PDF files)
    into Markdown files using the docling library.
    """
    console = Console()
    
    try:
        # Create and run the menu system
        menu_system = MenuSystem(console=console)
        exit_code = menu_system.run()
        
        # Exit with the appropriate code
        return exit_code
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        console.print("\n\n[yellow]Operation cancelled by user.[/yellow]")
        return 0
    except Exception as e:
        # Handle any unexpected exceptions
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())