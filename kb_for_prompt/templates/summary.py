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
Summary display templates for the kb-for-prompt CLI application.

This module provides functions for displaying summaries of conversion results,
including success/failure counts and tables with detailed information.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def display_conversion_summary(
    successful: List[Dict[str, Any]],
    failed: List[Dict[str, Any]],
    output_dir: Path,
    console: Optional[Console] = None
) -> None:
    """
    Display a summary of conversion results with success/failure counts and detailed tables.
    
    Args:
        successful: List of dictionaries with details of successful conversions.
            Each dict should have at least 'file' and 'original' keys.
        failed: List of dictionaries with details of failed conversions.
            Each dict should have at least 'original' and 'error' keys.
        output_dir: The directory where output files were saved.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    console.print("\n")
    
    # Create a summary panel
    total = len(successful) + len(failed)
    success_rate = (len(successful) / total) * 100 if total > 0 else 0
    
    summary_text = Text()
    summary_text.append("Conversion Summary\n", style="bold")
    summary_text.append(f"Total items processed: {total}\n")
    summary_text.append(f"Successfully converted: ", style="green")
    summary_text.append(f"{len(successful)} ({success_rate:.1f}%)\n")
    summary_text.append(f"Failed conversions: ", style="red")
    summary_text.append(f"{len(failed)} ({100-success_rate:.1f}%)\n")
    summary_text.append(f"Output directory: {output_dir}")
    
    console.print(Panel(summary_text, border_style="blue"))
    
    # If there were successful conversions, show them in a table
    if successful:
        success_table = Table(title="Successfully Converted Items", title_style="bold green")
        success_table.add_column("File", style="green")
        success_table.add_column("Original Source")
        success_table.add_column("Type", style="dim")
        
        for result in successful:
            file_name = result.get("file", "N/A")
            original = result.get("original", "N/A")
            item_type = result.get("type", "Unknown")
            success_table.add_row(file_name, original, item_type)
        
        console.print(success_table)
    
    # If there were failures, show them in a table
    if failed:
        failed_table = Table(title="Failed Conversions", title_style="bold red")
        failed_table.add_column("Original Source", style="red")
        failed_table.add_column("Error")
        failed_table.add_column("Type", style="dim")
        
        for result in failed:
            original = result.get("original", "N/A")
            error = result.get("error", "Unknown error")
            item_type = result.get("type", "Unknown")
            failed_table.add_row(original, error, item_type)
        
        console.print(failed_table)


def display_dataframe_summary(
    df: pd.DataFrame,
    title: str = "Data Summary",
    console: Optional[Console] = None
) -> None:
    """
    Display a summary of a pandas DataFrame as a Rich table.
    
    This is useful for showing summaries of batch conversion data from CSV files.
    
    Args:
        df: The pandas DataFrame to display.
        title: The title for the summary table.
        console: The Rich console to print to. If None, a new console is created.
    """
    console = console or Console()
    
    # Create a Rich table from the DataFrame
    table = Table(title=title, title_style="bold blue")
    
    # Add columns
    for column in df.columns:
        table.add_column(column, style="blue")
    
    # Add rows (limit to first 10 rows if more)
    row_limit = 10
    display_rows = df.head(row_limit)
    for _, row in display_rows.iterrows():
        # Convert all values to strings
        row_values = [str(value) for value in row.values]
        table.add_row(*row_values)
    
    # Add a note if the DataFrame has more rows
    if len(df) > row_limit:
        remaining = len(df) - row_limit
        console.print(f"[dim]Showing first {row_limit} of {len(df)} rows. {remaining} rows not shown...[/dim]")
    
    # Print the table
    console.print(table)
    
    # Print row and column count
    console.print(f"[dim]DataFrame contains {len(df)} rows and {len(df.columns)} columns.[/dim]")