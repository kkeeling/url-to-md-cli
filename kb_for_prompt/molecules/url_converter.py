"""
URL to Markdown converter module.

This module provides functionality to convert web content from URLs to Markdown format
using the docling library. It includes robust error handling, validation, and retry
mechanisms for reliable conversion.

Example:
    ```python
    from kb_for_prompt.molecules.url_converter import convert_url_to_markdown
    
    # Convert a URL to markdown
    markdown_content, original_url = convert_url_to_markdown("https://example.com")
    
    # Convert with custom retry settings
    markdown_content, original_url = convert_url_to_markdown(
        "https://example.com", 
        max_retries=5,
        timeout=10
    )
    ```
"""

import time
from typing import Tuple, Optional, Dict, Any
import requests

# Import docling for document conversion
from docling.document_converter import DocumentConverter

# Import utility functions
from kb_for_prompt.atoms.error_utils import ConversionError
from kb_for_prompt.atoms.input_validator import validate_url


def convert_url_to_markdown(
    url: str, 
    max_retries: int = 3, 
    timeout: int = 30,
    retry_delay: float = 1.0
) -> Tuple[str, str]:
    """
    Convert a URL to markdown content using docling.
    
    This function takes a URL, validates it, and converts its content to markdown
    format using the docling library. It includes a retry mechanism for handling
    temporary network issues or service failures.
    
    Args:
        url: The URL to convert
        max_retries: Maximum number of conversion attempts (default: 3)
        timeout: Timeout in seconds for the conversion process (default: 30)
        retry_delay: Delay between retries in seconds (default: 1.0)
    
    Returns:
        A tuple containing (markdown_content, original_url)
        
    Raises:
        ConversionError: If conversion fails after all retry attempts or encounters
                         a non-recoverable error
    """
    # Validate URL format (will raise ValidationError if invalid)
    validate_url(url)
    
    # Set up retry mechanism
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            # Create a DocumentConverter instance
            converter = DocumentConverter()
            
            # Convert the document with timeout
            result = converter.convert(url)
            
            # Check if conversion was successful and document was created
            if result.document:
                # Check if the document has content
                markdown_content = result.document.export_to_markdown()
                
                # Validate markdown content is not empty
                if markdown_content and len(markdown_content.strip()) > 0:
                    return markdown_content, url
                else:
                    raise ConversionError(
                        message="Conversion produced empty markdown content",
                        input_path=url,
                        conversion_type="url",
                        details={"status": str(result.status)}
                    )
            else:
                # Handle case where document is None but result is returned
                error_details = {
                    "status": str(result.status),
                    "errors": [str(err) for err in (result.errors or [])]
                }
                
                raise ConversionError(
                    message=f"Failed to convert URL to document",
                    input_path=url,
                    conversion_type="url",
                    details=error_details
                )
                
        except requests.RequestException as e:
            # Network-related errors, might be temporary
            last_error = ConversionError(
                message=f"HTTP request failed: {str(e)}",
                input_path=url,
                conversion_type="url",
                details={"http_error": str(e)}
            )
        except ConversionError as e:
            # Re-raise conversion errors that we've already formatted properly
            last_error = e
        except Exception as e:
            # Catch-all for unexpected errors
            last_error = ConversionError(
                message=f"Unexpected conversion error: {str(e)}",
                input_path=url,
                conversion_type="url",
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
                    message="Failed to convert URL after multiple attempts",
                    input_path=url,
                    conversion_type="url",
                    details={"retries": retries - 1}
                )