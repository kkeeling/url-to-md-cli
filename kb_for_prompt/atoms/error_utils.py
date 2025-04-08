"""
Error handling utilities for the kb-for-prompt package.

This module provides custom exception classes and utility functions
for consistent error reporting across the application.
"""

from typing import Optional, Any, Dict


class KbForPromptError(Exception):
    """Base exception class for all kb-for-prompt errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a KbForPromptError.
        
        Args:
            message: The error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(KbForPromptError):
    """Exception raised when input validation fails."""
    
    def __init__(
        self, 
        message: str, 
        input_value: Optional[str] = None, 
        validation_type: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ValidationError.
        
        Args:
            message: The error message
            input_value: The value that failed validation
            validation_type: The type of validation that failed (e.g., "url", "file", "extension")
            details: Optional dictionary with additional error details
        """
        self.input_value = input_value
        self.validation_type = validation_type
        super().__init__(message, details)


class ConversionError(KbForPromptError):
    """Exception raised when a document conversion fails."""
    
    def __init__(
        self, 
        message: str, 
        input_path: Optional[str] = None, 
        conversion_type: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ConversionError.
        
        Args:
            message: The error message
            input_path: The path to the document that failed conversion
            conversion_type: The type of conversion that failed (e.g., "url", "doc", "pdf")
            details: Optional dictionary with additional error details
        """
        self.input_path = input_path
        self.conversion_type = conversion_type
        super().__init__(message, details)


class FileIOError(KbForPromptError):
    """Exception raised when file I/O operations fail."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None, 
        operation: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a FileIOError.
        
        Args:
            message: The error message
            file_path: The path to the file that caused the error
            operation: The operation that failed (e.g., "read", "write", "create")
            details: Optional dictionary with additional error details
        """
        self.file_path = file_path
        self.operation = operation
        super().__init__(message, details)


def format_error_message(
    error_type: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format an error message with consistent structure.
    
    Args:
        error_type: The type of error (e.g., "Validation", "Conversion")
        message: The core error message
        context: Optional context information to include in the message
    
    Returns:
        A formatted error message string
    """
    base_message = f"{error_type} Error: {message}"
    
    if not context:
        return base_message
    
    # Add context details to the message
    context_str = "; ".join(f"{key}={value}" for key, value in context.items())
    return f"{base_message} [{context_str}]"


def create_error_details(
    error: Exception,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error details dictionary.
    
    Args:
        error: The exception that occurred
        additional_info: Additional information to include in the details
    
    Returns:
        A dictionary with error details
    """
    details = {
        "error_type": error.__class__.__name__,
        "error_message": str(error)
    }
    
    if additional_info:
        details.update(additional_info)
    
    return details