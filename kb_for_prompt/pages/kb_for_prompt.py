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
    uv run kb_for_prompt/pages/kb_for_prompt.py
    
    # If installed locally
    python kb_for_prompt/pages/kb_for_prompt.py
    
    # Run with command-line options
    uv run kb_for_prompt/pages/kb_for_prompt.py --url https://example.com
    uv run kb_for_prompt/pages/kb_for_prompt.py --file /path/to/document.pdf
    uv run kb_for_prompt/pages/kb_for_prompt.py --batch /path/to/inputs.csv
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import click
from rich.console import Console

from kb_for_prompt.organisms.menu_system import MenuSystem
from kb_for_prompt.organisms.single_item_converter import SingleItemConverter
from kb_for_prompt.organisms.batch_converter import BatchConverter
from kb_for_prompt.templates.banner import display_banner

# Define version directly to avoid import issues
__version__ = "0.1.0"


@click.command()
@click.version_option(version=__version__)
@click.option('--url', help='URL to convert to Markdown')
@click.option('--file', help='Local file path to convert to Markdown')
@click.option('--batch', help='CSV file containing URLs and/or file paths to convert')
@click.option('--output-dir', help='Directory to save the converted Markdown files')
def main(url: Optional[str], file: Optional[str], batch: Optional[str], 
         output_dir: Optional[str]):
    """KB for Prompt - Document to Markdown Converter.
    
    A CLI tool that converts online and local documents (URLs, Word, and PDF files)
    into Markdown files using the docling library.
    
    Run without options to use the interactive menu interface.
    """
    console = Console()
    
    try:
        # Display the banner
        display_banner(console=console)
        
        # If command-line options are provided, use them directly
        if url or file or batch:
            return handle_direct_conversion(url, file, batch, output_dir, console)
        
        # Otherwise, run the interactive menu system
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


def handle_direct_conversion(
    url: Optional[str], 
    file: Optional[str], 
    batch: Optional[str],
    output_dir: Optional[str],
    console: Console
) -> int:
    """
    Handle direct conversion based on command-line options.
    
    Args:
        url: URL to convert (if provided)
        file: File path to convert (if provided)
        batch: CSV file with batch inputs (if provided)
        output_dir: Output directory (optional)
        console: Console instance for output
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Create output directory object if provided
    output_path = Path(output_dir) if output_dir else None
    
    # Prioritize batch over single items
    if batch:
        # Batch conversion
        console.print(f"[bold]Starting batch conversion from CSV file:[/bold] {batch}")
        
        # Create batch converter and run it
        batch_converter = BatchConverter(console=console)
        success, result = batch_converter.run(batch, output_path or Path.cwd())
        
        return 0 if success else 1
        
    elif url:
        # URL conversion
        console.print(f"[bold]Converting URL to Markdown:[/bold] {url}")
        
        # Create single item converter and run it
        converter = SingleItemConverter(console=console)
        success, _ = converter.run(url, output_path)
        
        return 0 if success else 1
        
    elif file:
        # File conversion
        console.print(f"[bold]Converting file to Markdown:[/bold] {file}")
        
        # Create single item converter and run it
        converter = SingleItemConverter(console=console)
        success, _ = converter.run(file, output_path)
        
        return 0 if success else 1
    
    # Should never get here
    return 0


if __name__ == "__main__":
    sys.exit(main())