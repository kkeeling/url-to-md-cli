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

import click
from rich.console import Console

# Package version
from kb_for_prompt import __version__


@click.command()
@click.version_option(version=__version__)
def main():
    """KB for Prompt - Document to Markdown Converter.
    
    A CLI tool that converts online and local documents (URLs, Word, and PDF files)
    into Markdown files using the docling library.
    """
    console = Console()
    
    # Display banner
    console.print("[bold blue]KB for Prompt - Document to Markdown Converter[/bold blue]")
    console.print(f"Version: {__version__}")
    console.print("")
    
    # TODO: Implement the interactive menu system and conversion logic
    console.print("[yellow]This is a skeleton implementation. Further functionality will be added in future tasks.[/yellow]")
    

if __name__ == "__main__":
    main()