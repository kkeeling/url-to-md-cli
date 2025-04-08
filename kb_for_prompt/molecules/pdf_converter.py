"""
PDF document to Markdown converter module.

This module provides functionality to convert PDF documents to Markdown format
using the docling library. It includes file validation, error handling,
and retry mechanisms for reliable conversion.

Example:
    ```python
    from kb_for_prompt.molecules.pdf_converter import convert_pdf_to_markdown
    
    # Convert a PDF document to markdown
    markdown_content, original_path = convert_pdf_to_markdown("/path/to/document.pdf")
    
    # Convert with custom retry settings
    markdown_content, original_path = convert_pdf_to_markdown(
        "/path/to/document.pdf", 
        max_retries=5,
        timeout=10
    )
    ```
"""

import os
import time
from pathlib import Path
from typing import Union, Tuple, Optional, Dict, Any

# Import docling for document conversion
from docling.document_converter import DocumentConverter

# Import utility functions
from kb_for_prompt.atoms.error_utils import ConversionError, ValidationError
from kb_for_prompt.atoms.input_validator import validate_file_path, validate_file_type
from kb_for_prompt.atoms.path_utils import create_file_url


def convert_pdf_to_markdown(
    file_path: Union[str, Path], 
    max_retries: int = 3, 
    timeout: int = 30,
    retry_delay: float = 1.0
) -> Tuple[str, str]:
    """
    Convert a PDF document to markdown content using docling.
    
    This function takes a file path, validates it, and converts its content to markdown
    format using the docling library. It includes a retry mechanism for handling
    temporary conversion failures.
    
    Args:
        file_path: The path to the PDF document (str or Path object)
        max_retries: Maximum number of conversion attempts (default: 3)
        timeout: Timeout in seconds for the conversion process (default: 30)
        retry_delay: Delay between retries in seconds (default: 1.0)
    
    Returns:
        A tuple containing (markdown_content, original_file_path)
        
    Raises:
        ValidationError: If the file path is invalid or the file is not a PDF document
        ConversionError: If conversion fails after all retry attempts or encounters
                         a non-recoverable error
    """
    # Validate file path and ensure it exists
    resolved_path = validate_file_path(file_path)
    
    # Validate that the file is a PDF document
    file_type = validate_file_type(resolved_path, allowed_types=["pdf"])
    
    # Convert file path to file URL for docling
    file_url = create_file_url(resolved_path)
    
    # Set up retry mechanism
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            # Create a DocumentConverter instance
            converter = DocumentConverter()
            
            # Convert the document with timeout
            result = converter.convert(file_url)
            
            # Check if conversion was successful and document was created
            if result.document:
                # Check if the document has content
                markdown_content = result.document.export_to_markdown()
                
                # Validate markdown content is not empty
                if markdown_content and len(markdown_content.strip()) > 0:
                    return markdown_content, str(resolved_path)
                else:
                    raise ConversionError(
                        message="Conversion produced empty markdown content",
                        input_path=str(resolved_path),
                        conversion_type=file_type,
                        details={"status": str(result.status)}
                    )
            else:
                # Handle case where document is None but result is returned
                error_details = {
                    "status": str(result.status),
                    "errors": [str(err) for err in (result.errors or [])]
                }
                
                raise ConversionError(
                    message=f"Failed to convert {file_type} document",
                    input_path=str(resolved_path),
                    conversion_type=file_type,
                    details=error_details
                )
                
        except (OSError, IOError) as e:
            # File access errors
            last_error = ConversionError(
                message=f"File access error: {str(e)}",
                input_path=str(resolved_path),
                conversion_type=file_type,
                details={"os_error": str(e)}
            )
        except ConversionError as e:
            # Re-raise conversion errors that we've already formatted properly
            last_error = e
        except Exception as e:
            # Catch-all for unexpected errors
            last_error = ConversionError(
                message=f"Unexpected conversion error: {str(e)}",
                input_path=str(resolved_path),
                conversion_type=file_type,
                details={"error_type": e.__class__.__name__}
            )
        
        # If we reach here, there was an error
        retries += 1
        
        # If we haven't reached max retries, wait before trying again
        if retries <= max_retries:
            # Exponential backoff with jitter
            sleep_time = retry_delay * (2 ** (retries - 1))
            time.sleep(sleep_time)
        else:
            # We've exhausted our retries, raise the last error
            if last_error:
                # Add retry information to error details
                if last_error.details:
                    last_error.details.update({"retries": retries - 1})
                else:
                    last_error.details = {"retries": retries - 1}
                raise last_error
            else:
                # This should never happen, but just in case
                raise ConversionError(
                    message=f"Failed to convert {file_type} document after multiple attempts",
                    input_path=str(resolved_path),
                    conversion_type=file_type,
                    details={"retries": retries - 1}
                )