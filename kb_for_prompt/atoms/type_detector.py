"""
Type detection utilities for the kb-for-prompt package.

This module provides functions to detect input types (URLs vs. local files)
and file types based on extensions.
"""

import os
from pathlib import Path
from typing import Union, Optional, Tuple, Literal
from urllib.parse import urlparse
import re


def detect_input_type(input_string: str) -> Literal["url", "file"]:
    """
    Determine if an input string is a URL or a local file path.
    
    Args:
        input_string: The input string to analyze
    
    Returns:
        "url" if the input appears to be a URL, "file" otherwise
    
    Example:
        >>> detect_input_type("https://example.com")
        'url'
        
        >>> detect_input_type("/path/to/document.pdf")
        'file'
    """
    parsed = urlparse(input_string)
    
    # If it has a scheme (http, https, etc.) and a netloc (domain), it's a URL
    if parsed.scheme and parsed.netloc:
        return "url"
    
    # file:// URLs are a special case
    if parsed.scheme == "file":
        return "url"
    
    # Some URLs might be provided without a scheme (e.g. "example.com")
    # Common URL patterns to check
    url_patterns = [
        # Domain with TLD, no scheme
        r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(/.*)?$",
        # IP address
        r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?(/.*)?$"
    ]
    
    for pattern in url_patterns:
        if re.match(pattern, input_string):
            return "url"
    
    # Otherwise, assume it's a file path
    return "file"


def detect_file_type(file_path: Union[str, Path]) -> Optional[str]:
    """
    Detect the type of file based on its extension.
    
    Args:
        file_path: The path to the file
    
    Returns:
        The detected file type ("doc", "docx", "pdf") or None if unsupported
    
    Example:
        >>> detect_file_type("document.docx")
        'docx'
        
        >>> detect_file_type("document.pdf")
        'pdf'
        
        >>> detect_file_type("document.txt")
        None
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    extension = file_path.suffix.lower().lstrip('.')
    
    # Check for supported file types
    if extension in ("doc", "docx"):
        return extension
    elif extension == "pdf":
        return extension
    
    return None


def get_supported_extensions() -> Tuple[str, ...]:
    """
    Get a tuple of supported file extensions.
    
    Returns:
        A tuple of supported file extensions (without the dot)
    
    Example:
        >>> get_supported_extensions()
        ('doc', 'docx', 'pdf')
    """
    return ("doc", "docx", "pdf")


def is_url(input_string: str) -> bool:
    """
    Check if an input string is a URL.
    
    Args:
        input_string: The input string to check
    
    Returns:
        True if the input is a URL, False otherwise
    
    Example:
        >>> is_url("https://example.com")
        True
        
        >>> is_url("/path/to/file.txt")
        False
    """
    return detect_input_type(input_string) == "url"


def is_file_path(input_string: str) -> bool:
    """
    Check if an input string is a file path.
    
    Args:
        input_string: The input string to check
    
    Returns:
        True if the input is a file path, False otherwise
    
    Example:
        >>> is_file_path("/path/to/file.txt")
        True
        
        >>> is_file_path("https://example.com")
        False
    """
    return detect_input_type(input_string) == "file"


def is_supported_file_type(file_path: Union[str, Path]) -> bool:
    """
    Check if a file has a supported extension.
    
    Args:
        file_path: The path to the file
    
    Returns:
        True if the file extension is supported, False otherwise
    
    Example:
        >>> is_supported_file_type("document.docx")
        True
        
        >>> is_supported_file_type("image.jpg")
        False
    """
    return detect_file_type(file_path) is not None