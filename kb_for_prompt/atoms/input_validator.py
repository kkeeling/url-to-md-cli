"""
Input validation utilities for the kb-for-prompt package.

This module provides functions to validate URLs, file paths,
and file types based on extensions.
"""

import os
from pathlib import Path
from typing import Union, Optional, Tuple, List
from urllib.parse import urlparse
import requests
import re

from kb_for_prompt.atoms.error_utils import ValidationError
from kb_for_prompt.atoms.type_detector import detect_file_type, is_url, is_file_path
from kb_for_prompt.atoms.path_utils import resolve_path


def validate_url(url: str, check_connection: bool = False, timeout: int = 5) -> bool:
    """
    Validate a URL string.
    
    Args:
        url: The URL to validate
        check_connection: If True, attempts to connect to the URL to verify it's accessible
        timeout: Timeout in seconds for connection check (only used if check_connection is True)
    
    Returns:
        True if the URL is valid, False otherwise
    
    Raises:
        ValidationError: If the URL is invalid
    
    Example:
        >>> validate_url("https://example.com")
        True
        
        >>> validate_url("not-a-url")
        False
    """
    # Basic URL validation
    if not is_url(url):
        raise ValidationError(
            message="Invalid URL format",
            input_value=url,
            validation_type="url"
        )
    
    # Parse the URL to check its components
    parsed = urlparse(url)
    
    # file:// URLs are a special case
    if parsed.scheme == "file":
        # For file URLs, we don't need to check connection
        # Just make sure it has a path component
        if not parsed.path:
            raise ValidationError(
                message="Invalid file URL: missing path component",
                input_value=url,
                validation_type="file_url"
            )
        return True
    
    # For http/https URLs, ensure scheme and netloc are present
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(
            message=f"Unsupported URL scheme: {parsed.scheme}",
            input_value=url,
            validation_type="url_scheme"
        )
    
    if not parsed.netloc:
        raise ValidationError(
            message="Invalid URL: missing domain",
            input_value=url,
            validation_type="url"
        )
    
    # Optional: check if the URL is accessible
    if check_connection:
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code >= 400:
                raise ValidationError(
                    message=f"URL returned error status: {response.status_code}",
                    input_value=url,
                    validation_type="url_connection",
                    details={"status_code": response.status_code}
                )
        except requests.RequestException as e:
            raise ValidationError(
                message=f"Failed to connect to URL: {str(e)}",
                input_value=url,
                validation_type="url_connection"
            )
    
    return True


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate a file path.
    
    Args:
        file_path: The file path to validate
        must_exist: If True, checks that the file exists and is readable
    
    Returns:
        A resolved Path object for the file
    
    Raises:
        ValidationError: If the file path is invalid
    
    Example:
        >>> validate_file_path("/path/to/existing/file.txt")
        PosixPath('/path/to/existing/file.txt')
        
        >>> validate_file_path("/path/to/non-existent.txt", must_exist=False)
        PosixPath('/path/to/non-existent.txt')
    """
    # Validate the path is a string or Path object
    if not isinstance(file_path, (str, Path)):
        raise ValidationError(
            message="File path must be a string or Path object",
            input_value=str(file_path),
            validation_type="file_path_type"
        )
    
    # Resolve the path
    resolved_path = resolve_path(file_path)
    
    # If must_exist is True, check that the file exists and is readable
    if must_exist:
        if not resolved_path.exists():
            raise ValidationError(
                message="File does not exist",
                input_value=str(resolved_path),
                validation_type="file_existence"
            )
        
        if not resolved_path.is_file():
            raise ValidationError(
                message="Path exists but is not a file",
                input_value=str(resolved_path),
                validation_type="file_type"
            )
        
        if not os.access(resolved_path, os.R_OK):
            raise ValidationError(
                message="File exists but is not readable",
                input_value=str(resolved_path),
                validation_type="file_permissions"
            )
    
    return resolved_path


def validate_file_type(file_path: Union[str, Path], allowed_types: Optional[List[str]] = None) -> str:
    """
    Validate that a file is of an allowed type based on its extension.
    
    Args:
        file_path: The file path to validate
        allowed_types: List of allowed file types (extensions without the dot).
                       If None, defaults to ["doc", "docx", "pdf"]
    
    Returns:
        The detected file type
    
    Raises:
        ValidationError: If the file type is not allowed
    
    Example:
        >>> validate_file_type("document.docx")
        'docx'
        
        >>> validate_file_type("image.jpg", allowed_types=["jpg", "png"])
        'jpg'
    """
    if allowed_types is None:
        allowed_types = ["doc", "docx", "pdf"]
    
    # Resolve and validate file path
    path = Path(file_path)
    
    # Get file extension without the dot
    extension = path.suffix.lower().lstrip('.')
    
    if not extension:
        raise ValidationError(
            message="File has no extension",
            input_value=str(file_path),
            validation_type="file_extension"
        )
    
    if extension not in allowed_types:
        raise ValidationError(
            message=f"Unsupported file type: .{extension}. Allowed types: {', '.join(allowed_types)}",
            input_value=str(file_path),
            validation_type="file_type",
            details={"allowed_types": allowed_types}
        )
    
    return extension


def validate_directory_path(directory_path: Union[str, Path], must_exist: bool = False) -> Path:
    """
    Validate a directory path.
    
    Args:
        directory_path: The directory path to validate
        must_exist: If True, checks that the directory exists
    
    Returns:
        A resolved Path object for the directory
    
    Raises:
        ValidationError: If the directory path is invalid
    
    Example:
        >>> validate_directory_path("/path/to/existing/dir")
        PosixPath('/path/to/existing/dir')
        
        >>> validate_directory_path("/path/to/new/dir", must_exist=False)
        PosixPath('/path/to/new/dir')
    """
    # Validate the path is a string or Path object
    if not isinstance(directory_path, (str, Path)):
        raise ValidationError(
            message="Directory path must be a string or Path object",
            input_value=str(directory_path),
            validation_type="directory_path_type"
        )
    
    # Resolve the path
    resolved_path = resolve_path(directory_path)
    
    # If must_exist is True, check that the directory exists
    if must_exist:
        if not resolved_path.exists():
            raise ValidationError(
                message="Directory does not exist",
                input_value=str(resolved_path),
                validation_type="directory_existence"
            )
        
        if not resolved_path.is_dir():
            raise ValidationError(
                message="Path exists but is not a directory",
                input_value=str(resolved_path),
                validation_type="directory_type"
            )
        
        if not os.access(resolved_path, os.R_OK):
            raise ValidationError(
                message="Directory exists but is not readable",
                input_value=str(resolved_path),
                validation_type="directory_permissions"
            )
    
    return resolved_path


def validate_input_item(input_item: str) -> Tuple[str, str]:
    """
    Validate an input item as either a URL or a file path.
    
    Args:
        input_item: The input item to validate
    
    Returns:
        A tuple of (type, validated_item) where type is either "url" or "file"
    
    Raises:
        ValidationError: If the input item is invalid
    
    Example:
        >>> validate_input_item("https://example.com")
        ('url', 'https://example.com')
        
        >>> validate_input_item("/path/to/document.pdf")
        ('file', '/path/to/document.pdf')
    """
    # Detect input type
    input_type = "url" if is_url(input_item) else "file"
    
    # Validate based on type
    if input_type == "url":
        validate_url(input_item)
        return ("url", input_item)
    else:
        file_path = validate_file_path(input_item)
        file_type = detect_file_type(file_path)
        
        if file_type is None:
            raise ValidationError(
                message="Unsupported file type. Supported types: doc, docx, pdf",
                input_value=str(file_path),
                validation_type="file_type"
            )
        
        return ("file", str(file_path))