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
URL to Markdown Converter

This script takes a CSV file containing URLs and converts each URL's content
into a markdown document, saving them to a specified output directory.

Usage:
    # Install and run with uv
    uv run url_to_md.py --input INPUT.csv --output OUTPUT_DIR
    uv run url_to_md.py  # Will prompt for input and output
    
    # If installed locally
    python url_to_md.py --input INPUT.csv --output OUTPUT_DIR
    python url_to_md.py  # Will prompt for input and output
"""

import os
import sys
import time
import csv
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from halo import Halo

# Import docling for document conversion (required)
try:
    import docling
    from docling.converter import convert_document_from_url
except ImportError:
    print("Error: docling library is required but not installed.")
    print("Please install it using: pip install docling")
    sys.exit(1)


class ConversionError(Exception):
    """Exception raised when a URL conversion fails."""
    pass


def read_urls_from_csv(file_path: Path) -> List[str]:
    """
    Read URLs from a CSV file.
    
    Tries to intelligently determine the format: if the file has headers,
    it looks for columns that might contain URLs. If not, it assumes
    the first column contains URLs.
    """
    console = Console()
    
    try:
        with Halo(text=f"Reading URLs from {file_path}", spinner="dots") as spinner:
            # Try reading with pandas to auto-detect format
            df = pd.read_csv(file_path)
            spinner.succeed(f"Successfully read CSV with {len(df)} rows")
        
        # Look for columns that might contain URLs
        url_columns = []
        for col in df.columns:
            # Check if column name contains typical URL-related terms
            if any(term in col.lower() for term in ['url', 'link', 'href', 'web', 'site', 'http']):
                url_columns.append(col)
        
        # If we found likely URL columns, use the first one
        if url_columns:
            urls = df[url_columns[0]].dropna().tolist()
            console.print(f"Using column [bold green]{url_columns[0]}[/bold green] for URLs")
        # Otherwise, assume the first column contains URLs
        else:
            urls = df.iloc[:, 0].dropna().tolist()
            console.print(f"Using first column [bold yellow]{df.columns[0]}[/bold yellow] for URLs")
        
        # Validate URLs by checking if they have a scheme and netloc
        valid_urls = []
        for url in urls:
            url = str(url).strip()
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                valid_urls.append(url)
        
        if len(valid_urls) < len(urls):
            console.print(f"[bold yellow]Warning:[/bold yellow] Found {len(urls) - len(valid_urls)} invalid URLs that will be skipped")
        
        if not valid_urls:
            console.print("[bold red]Error:[/bold red] No valid URLs found in the CSV file")
            sys.exit(1)
            
        return valid_urls
        
    except Exception as e:
        console.print(f"[bold red]Error reading CSV file:[/bold red] {str(e)}")
        sys.exit(1)


def convert_url_to_markdown(url: str, index: int) -> Tuple[str, str]:
    """
    Convert a URL to markdown content using docling.
    
    Returns:
        Tuple[str, str]: (markdown_content, url)
        
    Raises:
        ConversionError: If conversion fails
    """
    try:
        # Convert document using docling
        doc = convert_document_from_url(url)
        return doc.to_markdown(), url
    except requests.RequestException as e:
        raise ConversionError(f"Request failed: {str(e)}")
    except Exception as e:
        raise ConversionError(f"Conversion failed: {str(e)}")


def process_urls(urls: List[str], output_dir: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a list of URLs and convert them to markdown files.
    
    Args:
        urls: List of URLs to process
        output_dir: Directory to save markdown files
    
    Returns:
        Tuple of (successful conversions, failed conversions)
    """
    console = Console()
    
    # Make sure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    successful = []
    failed = []
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        overall_task = progress.add_task(f"[green]Converting {len(urls)} URLs to markdown...", total=len(urls))
        
        # Process URLs with a thread pool for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all URL conversion tasks
            future_to_url = {executor.submit(convert_url_to_markdown, url, i): (i, url) for i, url in enumerate(urls)}
            
            # Process results as they complete
            for future in as_completed(future_to_url):
                index, url = future_to_url[future]
                file_name = f"{index+1:02d}.md"
                file_path = output_dir / file_name
                
                try:
                    markdown_content, original_url = future.result()
                    
                    # Write markdown to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    successful.append({
                        "index": index + 1,
                        "url": url,
                        "file": file_path.name
                    })
                    
                    # Update progress bar description with current file
                    progress.update(overall_task, 
                                   description=f"[green]Converted ({index+1}/{len(urls)}): {urlparse(url).netloc}",
                                   advance=1)
                    
                except ConversionError as e:
                    failed.append({
                        "index": index + 1,
                        "url": url,
                        "error": str(e)
                    })
                    
                    # Update progress bar description with error
                    progress.update(overall_task, 
                                   description=f"[red]Failed ({index+1}/{len(urls)}): {urlparse(url).netloc}",
                                   advance=1)
                except Exception as e:
                    failed.append({
                        "index": index + 1,
                        "url": url,
                        "error": str(e)
                    })
                    
                    # Update progress bar description with error
                    progress.update(overall_task, 
                                   description=f"[red]Failed ({index+1}/{len(urls)}): {urlparse(url).netloc}",
                                   advance=1)
    
    return successful, failed


def display_summary(successful: List[Dict], failed: List[Dict], output_dir: Path):
    """Display a summary of the conversion process."""
    console = Console()
    
    console.print("\n")
    
    # Create a summary panel
    total = len(successful) + len(failed)
    success_rate = (len(successful) / total) * 100 if total > 0 else 0
    
    summary_text = Text()
    summary_text.append("Conversion Summary\n", style="bold")
    summary_text.append(f"Total URLs processed: {total}\n")
    summary_text.append(f"Successfully converted: ", style="green")
    summary_text.append(f"{len(successful)} ({success_rate:.1f}%)\n")
    summary_text.append(f"Failed conversions: ", style="red")
    summary_text.append(f"{len(failed)} ({100-success_rate:.1f}%)\n")
    summary_text.append(f"Output directory: {output_dir}")
    
    console.print(Panel(summary_text))
    
    # If there were successful conversions, show them in a table
    if successful:
        success_table = Table(title="Successfully Converted URLs")
        success_table.add_column("File", style="green")
        success_table.add_column("URL")
        
        for result in successful:
            success_table.add_row(result["file"], result["url"])
        
        console.print(success_table)
    
    # If there were failures, show them in a table
    if failed:
        failed_table = Table(title="Failed Conversions")
        failed_table.add_column("URL", style="red")
        failed_table.add_column("Error")
        
        for result in failed:
            failed_table.add_row(result["url"], result["error"])
        
        console.print(failed_table)


@click.command()
@click.option("--input", "-i", type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
              help="Input CSV file containing URLs")
@click.option("--output", "-o", type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
              help="Output directory for markdown files")
def main(input: Optional[Path], output: Optional[Path]):
    """Convert URLs from a CSV file to markdown documents."""
    console = Console()
    
    # Banner
    console.print(Panel("[bold blue]URL to Markdown Converter[/bold blue]"))
    
    # Display docling version info
    console.print(f"Using docling version {docling.__version__}")
    console.print()
    
    # Prompt for input file if not provided
    if input is None:
        input_str = console.input("[bold green]Enter the path to the CSV file containing URLs:[/bold green] ")
        input = Path(input_str.strip())
        if not input.exists():
            console.print(f"[bold red]Error:[/bold red] File {input} does not exist")
            sys.exit(1)
    
    # Prompt for output directory if not provided
    if output is None:
        output_str = console.input("[bold green]Enter the output directory for markdown files:[/bold green] ")
        output = Path(output_str.strip())
    
    # Read URLs from CSV
    urls = read_urls_from_csv(input)
    console.print(f"Found [bold]{len(urls)}[/bold] URLs to process")
    
    # Process URLs
    successful, failed = process_urls(urls, output)
    
    # Display summary
    display_summary(successful, failed, output)
    
    # Exit with an error code if any conversions failed
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()