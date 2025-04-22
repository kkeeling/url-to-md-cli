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
#     "litellm",
# ]
# ///

"""
KB for Prompt - Document to Markdown Converter

This script provides a CLI tool to convert online and local documents
(URLs, Word, and PDF files) into Markdown files using the docling library.
It supports both batch conversion (using a CSV file with a mix of URLs and
file paths) and single item conversion modes via an interactive menu.
It also includes optional LLM-based generation of Table of Contents (TOC)
and Knowledge Base (KB) summaries, and KB condensation.

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
# This allows importing modules from the kb_for_prompt package
# when running the script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import click
from rich.console import Console
from rich.prompt import Confirm # Import Confirm

# Import necessary components from the package
from kb_for_prompt.organisms.menu_system import MenuSystem
from kb_for_prompt.organisms.single_item_converter import SingleItemConverter
from kb_for_prompt.organisms.batch_converter import BatchConverter
from kb_for_prompt.organisms.llm_client import LiteLlmClient # Import the new client
from kb_for_prompt.organisms.condenser import condense_knowledge_base # Import condenser
from kb_for_prompt.templates.banner import display_banner
from kb_for_prompt.templates.progress import display_spinner # Import spinner

# Define version directly to avoid import issues during direct execution
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
    into Markdown files using the docling library. Includes optional LLM-based
    Table of Contents and Knowledge Base generation, and KB condensation.

    Run without options to use the interactive menu interface.
    """
    console = Console()

    try:
        # Display the application banner
        display_banner(console=console)

        # If command-line options are provided, handle direct conversion
        if url or file or batch:
            # Note: Direct conversion currently bypasses LLM features (TOC/KB)
            # except for the newly added condensation step for single items.
            # Future enhancement could add flags like --generate-toc, --generate-kb
            return handle_direct_conversion(url, file, batch, output_dir, console)

        # --- Interactive Menu Flow ---
        # Instantiate the LLM client (using the simple simulator for now)
        # In a real application, you might load API keys or configure a real client here.
        llm_client = LiteLlmClient()

        # Instantiate the menu system, passing the console and the LLM client
        menu_system = MenuSystem(console=console, llm_client=llm_client)

        # Run the interactive menu system
        exit_code = menu_system.run()

        # Exit with the appropriate code returned by the menu system
        return exit_code

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        console.print("\n\n[yellow]Operation cancelled by user.[/yellow]")
        return 0
    except Exception as e:
        # Handle any unexpected exceptions during setup or execution
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        # Consider adding logging here for better diagnostics
        # import traceback
        # console.print(traceback.format_exc()) # For detailed debugging
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

    For single item conversions (URL/file), it offers an optional LLM-based
    condensation step after successful conversion. Batch conversion does not
    currently include LLM steps.

    Args:
        url: URL to convert (if provided).
        file: File path to convert (if provided).
        batch: CSV file with batch inputs (if provided).
        output_dir: Output directory (optional, defaults to current dir).
        console: Console instance for output.

    Returns:
        int: Exit code (0 for success of initial conversion, non-zero for error).
             The success/failure of the optional condensation step does not
             affect the return code.
    """
    # Determine the output path, defaulting to the current working directory if not specified
    output_path = Path(output_dir).resolve() if output_dir else Path.cwd()

    # Ensure the output directory exists
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[bold red]Error creating output directory '{output_path}': {e}[/bold red]")
        return 1

    # Prioritize batch conversion if the --batch option is used
    if batch:
        console.print(f"[bold]Starting batch conversion from CSV file:[/bold] {batch}")
        console.print(f"Output directory: [cyan]{output_path}[/cyan]")

        # Create batch converter and run it
        batch_converter = BatchConverter(console=console)
        success, result = batch_converter.run(batch, output_path)

        # Print summary from results
        if success:
            console.print(f"[bold green]✓ Batch conversion completed successfully.[/bold green]")
            console.print(f"  Total items processed: {result.get('total', 0)}")
            console.print(f"  Successful conversions: {len(result.get('successful', []))}")
            console.print(f"  Failed conversions: {len(result.get('failed', []))}")
        else:
            console.print(f"[bold red]✗ Batch conversion failed or partially failed.[/bold red]")
            error_info = result.get('error', {})
            if error_info:
                 console.print(f"  Error Type: {error_info.get('type', 'Unknown')}")
                 console.print(f"  Error Message: {error_info.get('message', 'No details provided')}")

        return 0 if success else 1

    # Handle single item conversion (URL or file)
    elif url or file:
        input_source = url if url else file
        source_type = "URL" if url else "File"
        original_conversion_success = False # Track initial conversion status

        console.print(f"[bold]Converting {source_type} to Markdown:[/bold] {input_source}")
        console.print(f"Output directory: [cyan]{output_path}[/cyan]")

        # Create single item converter and run it
        converter = SingleItemConverter(console=console)
        # Pass the determined output_path, not the potentially None output_dir
        success, result = converter.run(input_source, output_path)

        # Print summary from results
        if success:
            original_conversion_success = True # Mark initial conversion as successful
            console.print(f"[bold green]✓ Conversion successful.[/bold green]")
            console.print(f"  Output file: [cyan]{result.get('output_path', 'N/A')}[/cyan]")

            # --- Condensation Step ---
            original_kb_path_str = result.get('output_path')
            if original_kb_path_str:
                try:
                    # Ask user if they want to condense
                    if Confirm.ask("\n[bold yellow]?[/bold yellow] Do you want to generate a condensed version using an LLM?", default=False):
                        original_kb_path = Path(original_kb_path_str)
                        condensed_file_path: Optional[Path] = None

                        spinner_text = f"Condensing knowledge base: {original_kb_path.name}"
                        with display_spinner(text=spinner_text, console=console) as spinner:
                            try:
                                # Call the condensation function
                                condensed_file_path = condense_knowledge_base(original_kb_path)
                                # Update spinner text upon completion (handled by context manager on success/fail)
                            except Exception as condense_e:
                                # display_spinner handles logging the failure text
                                console.print(f"[bold red]An unexpected error occurred during condensation:[/bold red] {str(condense_e)}")
                                # No need to re-raise, spinner handles fail state

                        # Check result and print messages
                        if condensed_file_path:
                            console.print(f"[bold green]✓ Condensation successful.[/bold green]")
                            console.print(f"  Condensed file: [cyan]{condensed_file_path}[/cyan]")
                        else:
                            # condense_knowledge_base logs specific errors, so just indicate failure here
                            console.print(f"[bold red]✗ Condensation failed.[/bold red] Check logs for details.")

                except Exception as e:
                    console.print(f"\n[bold red]An error occurred during the condensation prompt or process:[/bold red] {str(e)}")
            else:
                 console.print("[yellow]Skipping condensation step as output path was not found in conversion result.[/yellow]")
            # --- End Condensation Step ---

        else:
            console.print(f"[bold red]✗ Conversion failed.[/bold red]")
            error_info = result.get('error', {})
            if error_info:
                 console.print(f"  Error Type: {error_info.get('type', 'Unknown')}")
                 console.print(f"  Error Message: {error_info.get('message', 'No details provided')}")

        # Return code based on the *original* conversion success
        return 0 if original_conversion_success else 1

    # This case should not be reached if validation occurs correctly upstream,
    # but included for completeness.
    else:
        console.print("[bold red]Error: No input specified (URL, file, or batch).[/bold red]")
        return 1


if __name__ == "__main__":
    # Use sys.exit() to ensure the exit code is propagated correctly
    sys.exit(main())
