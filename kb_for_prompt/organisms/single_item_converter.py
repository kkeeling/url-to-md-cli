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
Single item conversion module for the kb-for-prompt CLI application.

This module provides functionality to handle the single item conversion workflow
for URLs and local files (PDF, DOC, DOCX). It implements input detection,
file handling, conversion, and retry mechanisms with appropriate user feedback.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
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
    validate_file_type
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
    display_completion
)
from kb_for_prompt.templates.prompts import (
    prompt_for_retry,
    prompt_for_file,
    prompt_for_output_directory
)


class SingleItemConverter:
    """
    Handler for single item conversion workflow.
    
    This class provides methods to handle the conversion of a single
    URL or file (PDF, DOC, DOCX) to Markdown format, including input
    detection, output file generation, and retry mechanisms.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the single item converter.
        
        Args:
            console: The Rich console to print to. If None, a new console is created.
        """
        self.console = console or Console()
        self.max_retries = 3
    
    def run(
        self,
        input_item: str,
        output_directory: Optional[Union[str, Path]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run the complete single item conversion workflow.
        
        This method orchestrates the entire conversion process from input
        detection to output generation with appropriate user feedback.
        
        Args:
            input_item: The URL or file path to convert
            output_directory: Optional output directory for the markdown file.
                              If None, user will be prompted for output directory.
        
        Returns:
            A tuple containing (success, result_data) where:
            - success is a boolean indicating whether conversion was successful
            - result_data is a dictionary with information about the conversion:
              - input_path: Original input path or URL
              - input_type: Detected input type (url, pdf, doc, docx)
              - output_path: Path to the generated markdown file (if successful)
              - error: Error details (if conversion failed)
        """
        result_data = {
            "input_path": input_item,
            "input_type": None,
            "output_path": None,
            "error": None
        }
        
        try:
            # Detect and validate input type
            input_type, validated_input = self._detect_input_type(input_item)
            result_data["input_type"] = input_type
            result_data["input_path"] = validated_input
            
            # Get output directory (either provided or prompt user)
            output_dir = self._get_output_directory(output_directory)
            
            # Generate default output filename
            default_filename = self._generate_default_filename(validated_input, input_type)
            output_path = output_dir / default_filename
            
            # Perform the conversion with retry mechanism
            success, markdown_content, error = self._convert_with_retry(validated_input, input_type)
            
            if success:
                # Write the markdown content to file
                self._write_output_file(markdown_content, output_path)
                result_data["output_path"] = str(output_path)
                display_completion(
                    f"Successfully converted {input_type} to Markdown: {output_path}",
                    success=True,
                    console=self.console
                )
                return True, result_data
            else:
                # Conversion failed even after retries
                result_data["error"] = error
                display_completion(
                    f"Failed to convert {input_type} to Markdown after {self.max_retries} attempts",
                    success=False,
                    console=self.console
                )
                return False, result_data
                
        except ValidationError as e:
            # Input validation error
            result_data["error"] = {
                "type": "validation",
                "message": e.message,
                "details": e.details
            }
            display_completion(
                f"Validation error: {e.message}",
                success=False,
                console=self.console
            )
            return False, result_data
            
        except FileIOError as e:
            # File I/O error
            result_data["error"] = {
                "type": "file_io",
                "message": e.message,
                "details": e.details
            }
            display_completion(
                f"File error: {e.message}",
                success=False,
                console=self.console
            )
            return False, result_data
            
        except Exception as e:
            # Unexpected error
            result_data["error"] = {
                "type": "unexpected",
                "message": str(e)
            }
            display_completion(
                f"Unexpected error: {str(e)}",
                success=False,
                console=self.console
            )
            return False, result_data
    
    def _detect_input_type(self, input_item: str) -> Tuple[str, str]:
        """
        Detect and validate the input type.
        
        Args:
            input_item: The input item to analyze (URL or file path)
        
        Returns:
            A tuple of (type, validated_input) where:
            - type is the input type (url, pdf, doc, docx)
            - validated_input is the validated input path or URL
        
        Raises:
            ValidationError: If the input cannot be validated
        """
        display_processing_update("Detecting input type...", status="processing", console=self.console)
        
        # Use the validate_input_item utility to get the basic type (url or file)
        basic_type, validated_input = validate_input_item(input_item)
        
        if basic_type == "url":
            display_processing_update("Detected URL input", status="success", console=self.console)
            return "url", validated_input
        else:
            # For files, we need the specific file type
            file_path = Path(validated_input)
            file_type = validate_file_type(file_path)
            display_processing_update(f"Detected {file_type.upper()} file", status="success", console=self.console)
            return file_type, validated_input
    
    def _get_output_directory(self, output_directory: Optional[Union[str, Path]]) -> Path:
        """
        Get the output directory for the markdown file.
        
        If output_directory is None, prompt the user for a directory.
        
        Args:
            output_directory: Optional output directory path
        
        Returns:
            Path: The resolved output directory path
        
        Raises:
            FileIOError: If the directory cannot be created
        """
        if output_directory is not None:
            # Use provided directory
            output_dir = ensure_directory_exists(output_directory)
            display_processing_update(
                f"Using output directory: {output_dir}",
                status="info",
                console=self.console
            )
        else:
            # Prompt user for output directory
            display_processing_update(
                "No output directory specified, prompting user...",
                status="info",
                console=self.console
            )
            output_dir = prompt_for_output_directory(console=self.console)
        
        return output_dir
    
    def _generate_default_filename(self, input_path: str, input_type: str) -> str:
        """
        Generate a default output filename based on the input.
        
        Args:
            input_path: The input path or URL
            input_type: The input type (url, pdf, doc, docx)
        
        Returns:
            str: The default filename for the output (with .md extension)
        """
        display_processing_update(
            "Generating output filename...",
            status="processing",
            console=self.console
        )
        
        if input_type == "url":
            # Extract domain and path for URL
            from urllib.parse import urlparse
            parsed = urlparse(input_path)
            domain = parsed.netloc.replace('.', '_')
            path = parsed.path.replace('/', '_')
            
            # Create a clean filename
            filename = f"{domain}{path}".rstrip('_')
            
            # Remove common extensions
            if filename.endswith(('.html', '.htm', '.php')):
                filename = filename.rsplit('.', 1)[0]
        else:
            # Use the file name without its extension
            path_obj = Path(input_path)
            filename = path_obj.stem
        
        # Clean up any remaining special characters
        filename = "".join(c if c.isalnum() or c == '_' else '_' for c in filename)
        filename = filename.strip('_')
        
        # Ensure the filename isn't too long
        if len(filename) > 100:
            filename = filename[:100]
        
        # If filename is empty (rare case), use a default
        if not filename:
            filename = "document"
        
        # Add .md extension
        filename = f"{filename}.md"
        
        display_processing_update(
            f"Generated filename: {filename}",
            status="success",
            console=self.console
        )
        
        return filename
    
    def _convert_with_retry(
        self,
        input_path: str,
        input_type: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Perform the conversion with a retry mechanism.
        
        Args:
            input_path: The validated input path or URL
            input_type: The input type (url, pdf, doc, docx)
        
        Returns:
            A tuple of (success, content, error) where:
            - success is a boolean indicating if conversion was successful
            - content is the converted markdown content (if successful)
            - error is a dictionary with error details (if failed)
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                with display_spinner(
                    f"Converting {input_type} to Markdown...",
                    success_text=f"Successfully converted {input_type} to Markdown",
                    console=self.console
                ) as spinner:
                    # Choose the appropriate converter based on input type
                    if input_type == "url":
                        markdown_content, _ = convert_url_to_markdown(input_path)
                    elif input_type in ["doc", "docx"]:
                        markdown_content, _ = convert_doc_to_markdown(input_path)
                    elif input_type == "pdf":
                        markdown_content, _ = convert_pdf_to_markdown(input_path)
                    else:
                        raise ValueError(f"Unsupported input type: {input_type}")
                    
                    # Check if we got valid markdown content
                    if markdown_content and len(markdown_content.strip()) > 0:
                        return True, markdown_content, None
                    else:
                        raise ConversionError(
                            message="Conversion produced empty markdown content",
                            input_path=input_path,
                            conversion_type=input_type
                        )
            
            except Exception as e:
                # Track the last error
                if isinstance(e, ConversionError):
                    last_error = e
                else:
                    last_error = ConversionError(
                        message=f"Conversion failed: {str(e)}",
                        input_path=input_path,
                        conversion_type=input_type
                    )
                
                retries += 1
                
                # If we still have retries left, ask the user if they want to retry
                if retries <= self.max_retries:
                    error_message = str(last_error)
                    should_retry = prompt_for_retry(
                        error_message,
                        retry_count=retries,
                        max_retries=self.max_retries,
                        console=self.console
                    )
                    
                    if not should_retry:
                        # User chose not to retry
                        break
                
        # If we get here, all retries failed or user chose not to retry
        error_details = {
            "message": str(last_error) if last_error else "Unknown error",
            "retries": retries,
            "input_type": input_type,
            "input_path": input_path
        }
        
        # Add any additional details from the last error
        if last_error and isinstance(last_error, ConversionError) and last_error.details:
            error_details.update(last_error.details)
        
        return False, None, error_details
    
    def _write_output_file(self, content: str, output_path: Path) -> None:
        """
        Write the markdown content to the output file.
        
        Args:
            content: The markdown content to write
            output_path: The output file path
        
        Raises:
            FileIOError: If the file cannot be written
        """
        with display_spinner(
            f"Writing markdown to {output_path}...",
            success_text=f"Successfully wrote markdown to {output_path}",
            console=self.console
        ):
            try:
                # Ensure the parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the content to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                raise FileIOError(
                    message=f"Failed to write output file: {str(e)}",
                    file_path=str(output_path),
                    operation="write"
                )