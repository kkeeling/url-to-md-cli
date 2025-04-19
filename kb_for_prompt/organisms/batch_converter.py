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
Batch conversion module for the kb-for-prompt CLI application.

This module provides functionality to handle batch conversion of multiple inputs
(URLs and local files) from a CSV file. It supports concurrent processing,
input validation, and provides detailed summary reporting.
"""

import os
import csv
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from rich.console import Console

# Import core converters
from kb_for_prompt.molecules.url_converter import convert_url_to_markdown
from kb_for_prompt.molecules.doc_converter import convert_doc_to_markdown
from kb_for_prompt.molecules.pdf_converter import convert_pdf_to_markdown

# Import utilities
from kb_for_prompt.atoms.type_detector import (
    detect_input_type,
    detect_file_type,
    is_url,
    is_file_path
)
from kb_for_prompt.atoms.path_utils import (
    generate_output_filename,
    ensure_directory_exists,
    resolve_path
)
from kb_for_prompt.atoms.input_validator import (
    validate_input_item,
    validate_url,
    validate_file_path,
    validate_file_type,
    validate_directory_path
)
from kb_for_prompt.atoms.error_utils import (
    ConversionError,
    ValidationError,
    FileIOError
)

# Import display templates
from kb_for_prompt.templates.progress import (
    display_spinner,
    display_processing_update,
    display_completion,
    display_progress_bar
)
from kb_for_prompt.templates.summary import (
    display_conversion_summary,
    display_dataframe_summary
)


class BatchConverter:
    """
    Handler for batch conversion workflow.
    
    This class provides methods to handle the conversion of multiple
    inputs (URLs and local files) from a CSV file, including input
    detection, output file generation, and concurrent processing.
    """
    
    def __init__(self, console: Optional[Console] = None, max_workers: int = 5):
        """
        Initialize the batch converter.
        
        Args:
            console: The Rich console to print to. If None, a new console is created.
            max_workers: Maximum number of worker threads for concurrent processing.
        """
        self.console = console or Console()
        self.max_workers = max_workers
        self.max_retries = 3  # Maximum number of retries for conversion
    
    def run(
        self,
        csv_path: Union[str, Path],
        output_directory: Union[str, Path]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run the complete batch conversion workflow.
        
        This method orchestrates the entire batch conversion process from CSV
        parsing to output generation with concurrent processing and summary reporting.
        
        Args:
            csv_path: Path to the CSV file containing inputs
            output_directory: Directory where to save the converted markdown files
        
        Returns:
            A tuple containing (success, result_data) where:
            - success is a boolean indicating whether the batch process completed
            - result_data is a dictionary with information about the conversions:
              - total: Total number of inputs processed
              - successful: List of successful conversion details
              - failed: List of failed conversion details
              - output_dir: Path to the output directory
        """
        result_data = {
            "total": 0,
            "successful": [],
            "failed": [],
            "output_dir": str(output_directory)
        }
        
        try:
            # Validate and resolve the output directory
            output_dir = ensure_directory_exists(output_directory)
            result_data["output_dir"] = str(output_dir)
            
            # Read and parse the CSV file
            inputs = self.read_inputs_from_csv(csv_path)
            result_data["total"] = len(inputs)
            
            if not inputs:
                display_processing_update(
                    "No valid inputs found in the CSV file", 
                    status="warning",
                    console=self.console
                )
                return False, result_data
            
            # Display a summary of the inputs
            self._display_input_summary(inputs)
            
            # Process the inputs concurrently
            successful, failed = self._process_batch(inputs, output_dir)
            
            # Update result data
            result_data["successful"] = successful
            result_data["failed"] = failed
            
            # Display the conversion summary
            display_conversion_summary(
                successful=successful,
                failed=failed,
                output_dir=output_dir,
                console=self.console
            )
            
            # Return success if at least one conversion was successful
            return len(successful) > 0, result_data
            
        except ValidationError as e:
            # Input validation error
            display_processing_update(
                f"Validation error: {e.message}",
                status="error",
                console=self.console
            )
            return False, result_data
            
        except FileIOError as e:
            # File I/O error
            display_processing_update(
                f"File error: {e.message}",
                status="error",
                console=self.console
            )
            return False, result_data
            
        except Exception as e:
            # Unexpected error
            display_processing_update(
                f"Unexpected error: {str(e)}",
                status="error",
                console=self.console
            )
            return False, result_data
    
    def read_inputs_from_csv(self, csv_path: Union[str, Path]) -> List[str]:
        """
        Read and parse inputs from a CSV file.
        
        The CSV file can contain URLs or file paths in one or multiple columns,
        potentially across multiple rows. It prioritizes the standard `csv` module.
        
        Args:
            csv_path: Path to the CSV file to read
        
        Returns:
            A list of unique input strings (URLs or file paths) found in the CSV.
        
        Raises:
            ValidationError: If the CSV file path is invalid.
            FileIOError: If there are issues reading the file.
        """
        with display_spinner(
            f"Reading inputs from {csv_path}...",
            console=self.console
        ) as spinner:
            try:
                # Validate and resolve the file path
                file_path = validate_file_path(csv_path)
                
                inputs = []
                spinner.text = f"Parsing CSV file: {file_path}"
                
                # --- Use standard CSV reader first ---
                try:
                    with open(file_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        for i, row in enumerate(reader):
                            spinner.text = f"Reading row {i+1} from {file_path}"
                            for value in row:
                                value_str = str(value).strip()
                                if value_str:
                                    inputs.append(value_str)
                    spinner.text = "Finished reading CSV."
                except csv.Error as e:
                    # If csv.reader fails, raise a FileIOError
                    raise FileIOError(
                        message=f"Failed to parse CSV file with standard reader: {str(e)}",
                        file_path=str(file_path),
                        operation="read"
                    )
                except Exception as e:
                    # Catch other potential file reading errors
                    raise FileIOError(
                        message=f"Failed to read CSV file: {str(e)}",
                        file_path=str(file_path),
                        operation="read"
                    )
                
                # --- Original pandas code (commented out for now) ---
                # try:
                #     # First, try to read as a pandas DataFrame
                #     df = pd.read_csv(file_path)
                #
                #     # Extract non-empty values from all columns
                #     for column in df.columns:
                #         for value in df[column].dropna():
                #             value_str = str(value).strip()
                #             if value_str:
                #                 inputs.append(value_str)
                #
                #     # Display a summary of the DataFrame
                #     spinner.text = "CSV file loaded, analyzing data..."
                #     display_dataframe_summary(df, title="CSV Input Summary", console=self.console)
                #
                # except Exception as e:
                #     # If pandas fails, fall back to the standard CSV reader
                #     spinner.text = "Falling back to basic CSV parsing..."
                #
                #     with open(file_path, 'r', newline='', encoding='utf-8') as f:
                #         reader = csv.reader(f)
                #         for row in reader:
                #             for value in row:
                #                 value_str = str(value).strip()
                #                 if value_str:
                #                     inputs.append(value_str)
                
                # Filter out duplicates while preserving order
                unique_inputs = []
                seen: Set[str] = set() # Explicitly type hint seen
                for item in inputs:
                    if item not in seen:
                        seen.add(item)
                        unique_inputs.append(item)
                
                if not unique_inputs:
                    spinner.text = "No inputs found in CSV."
                else:
                    spinner.text = f"Found {len(unique_inputs)} unique inputs."
                
                return unique_inputs
                
            except ValidationError as e:
                # Re-raise validation errors related to the file path itself
                raise ValidationError(
                    message=f"Invalid CSV file path: {e.message}",
                    input_value=str(csv_path),
                    validation_type="csv_input"
                )
                
            except FileIOError as e:
                # Re-raise FileIOErrors encountered during reading/parsing
                raise e
                
            except Exception as e:
                # Catch any other unexpected errors during the process
                raise FileIOError(
                    message=f"Unexpected error reading CSV file: {str(e)}",
                    file_path=str(csv_path),
                    operation="read"
                )
    
    def validate_and_classify_inputs(
        self, 
        inputs: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate and classify inputs by type.
        
        Args:
            inputs: List of input strings to validate and classify
        
        Returns:
            A tuple containing (valid_inputs, invalid_inputs) where:
            - valid_inputs is a list of dictionaries with validated input details
            - invalid_inputs is a list of dictionaries with validation error details
        """
        with display_spinner(
            "Validating and classifying inputs...",
            console=self.console
        ) as spinner:
            valid_inputs = []
            invalid_inputs = []
            
            for i, input_str in enumerate(inputs):
                spinner.text = f"Validating input {i+1}/{len(inputs)}..."
                
                try:
                    # Try to validate and classify the input
                    input_type, validated_input = validate_input_item(input_str)
                    
                    # For file inputs, get the specific file type
                    if input_type == "file":
                        file_type = detect_file_type(validated_input)
                        if file_type:
                            input_type = file_type
                        else:
                            # This should not happen since validate_input_item checks file type
                            raise ValidationError(
                                message="Unsupported file type",
                                input_value=input_str,
                                validation_type="file_type"
                            )
                    
                    valid_inputs.append({
                        "original": input_str,
                        "validated": validated_input,
                        "type": input_type
                    })
                    
                except ValidationError as e:
                    invalid_inputs.append({
                        "original": input_str,
                        "error": e.message,
                        "details": e.details if hasattr(e, 'details') else None
                    })
            
            return valid_inputs, invalid_inputs
    
    def _process_batch(
        self,
        inputs: List[str],
        output_dir: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process a batch of inputs concurrently.
        
        Args:
            inputs: List of input strings to process
            output_dir: Directory where to save the converted markdown files
        
        Returns:
            A tuple containing (successful, failed) where:
            - successful is a list of successful conversion details
            - failed is a list of failed conversion details
        """
        # First, validate and classify all inputs
        valid_inputs, invalid_inputs = self.validate_and_classify_inputs(inputs)
        
        # Initialize results lists
        successful = []
        failed = invalid_inputs.copy()  # Start with invalid inputs
        
        # If no valid inputs, return early
        if not valid_inputs:
            display_processing_update(
                "No valid inputs to process",
                status="warning",
                console=self.console
            )
            return successful, failed
        
        # Setup progress tracking
        with display_progress_bar(
            f"Converting {len(valid_inputs)} inputs",
            total=len(valid_inputs),
            console=self.console
        ) as progress:
            # Process valid inputs concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_input = {
                    executor.submit(self._process_single_input, input_data, output_dir): input_data
                    for input_data in valid_inputs
                }
                
                # Process results as they complete
                for i, future in enumerate(concurrent.futures.as_completed(future_to_input)):
                    input_data = future_to_input[future]
                    
                    # Update progress
                    progress.update(
                        progress.task_id,
                        description=f"Processing {i+1}/{len(valid_inputs)}",
                        advance=1
                    )
                    
                    try:
                        # Get the result from the future
                        result = future.result()
                        
                        if result["success"]:
                            successful.append({
                                "file": result["output_path"],
                                "original": input_data["original"],
                                "type": input_data["type"]
                            })
                        else:
                            failed.append({
                                "original": input_data["original"],
                                "error": result["error"]["message"],
                                "type": input_data["type"]
                            })
                    
                    except Exception as e:
                        # Handle any unexpected exceptions from the future
                        failed.append({
                            "original": input_data["original"],
                            "error": f"Unexpected error: {str(e)}",
                            "type": input_data["type"]
                        })
        
        return successful, failed
    
    def _process_single_input(
        self,
        input_data: Dict[str, Any],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Process a single input item for conversion.
        
        This method is designed to be run in a separate thread as part of
        concurrent batch processing.
        
        Args:
            input_data: Dictionary with input details (original, validated, type)
            output_dir: Directory where to save the converted markdown file
        
        Returns:
            A dictionary with the conversion result:
            - success: Boolean indicating if conversion was successful
            - original: The original input string
            - type: The input type
            - output_path: Path to the output file (if successful)
            - error: Error details (if failed)
        """
        result = {
            "success": False,
            "original": input_data["original"],
            "type": input_data["type"],
            "output_path": None,
            "error": None
        }
        
        try:
            input_type = input_data["type"]
            validated_input = input_data["validated"]
            
            # Generate output filename
            output_path = generate_output_filename(validated_input, output_dir)
            
            # Perform the conversion based on input type
            if input_type == "url":
                markdown_content, _ = convert_url_to_markdown(
                    validated_input,
                    max_retries=self.max_retries
                )
            elif input_type in ["doc", "docx"]:
                markdown_content, _ = convert_doc_to_markdown(
                    validated_input,
                    max_retries=self.max_retries
                )
            elif input_type == "pdf":
                markdown_content, _ = convert_pdf_to_markdown(
                    validated_input,
                    max_retries=self.max_retries
                )
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            # Write the markdown content to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Update result with success
            result["success"] = True
            result["output_path"] = str(output_path)
            
        except Exception as e:
            # Handle any errors during conversion
            error_message = str(e)
            
            # Determine error type
            if isinstance(e, ConversionError):
                error_type = "conversion"
            else:
                error_type = "unexpected"
            
            result["error"] = {
                "type": error_type,
                "message": error_message
            }
        
        return result
    
    def _display_input_summary(self, inputs: List[str]) -> None:
        """
        Display a summary of the inputs to be processed.
        
        Args:
            inputs: List of input strings
        """
        url_count = 0
        file_count = 0
        
        # Count URLs and files
        for input_str in inputs:
            if is_url(input_str):
                url_count += 1
            else:
                file_count += 1
        
        display_processing_update(
            f"Loaded {len(inputs)} inputs: {url_count} URLs and {file_count} files",
            status="info",
            console=self.console
        )