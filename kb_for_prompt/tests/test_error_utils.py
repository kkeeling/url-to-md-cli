"""
Tests for error_utils.py
"""

import pytest
from kb_for_prompt.atoms.error_utils import (
    KbForPromptError, 
    ValidationError, 
    ConversionError, 
    FileIOError,
    format_error_message,
    create_error_details
)


def test_kb_for_prompt_error():
    """Test KbForPromptError base class."""
    # Test with only message
    error = KbForPromptError("Test error message")
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.details == {}
    
    # Test with message and details
    details = {"key": "value"}
    error = KbForPromptError("Test error message", details)
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.details == details


def test_validation_error():
    """Test ValidationError class."""
    # Test with minimum required parameters
    error = ValidationError("Invalid URL")
    assert str(error) == "Invalid URL"
    assert error.message == "Invalid URL"
    assert error.input_value is None
    assert error.validation_type is None
    assert error.details == {}
    
    # Test with all parameters
    error = ValidationError(
        "Invalid URL", 
        input_value="example.com", 
        validation_type="url",
        details={"attempted": True}
    )
    assert str(error) == "Invalid URL"
    assert error.message == "Invalid URL"
    assert error.input_value == "example.com"
    assert error.validation_type == "url"
    assert error.details == {"attempted": True}


def test_conversion_error():
    """Test ConversionError class."""
    # Test with minimum required parameters
    error = ConversionError("Conversion failed")
    assert str(error) == "Conversion failed"
    assert error.message == "Conversion failed"
    assert error.input_path is None
    assert error.conversion_type is None
    assert error.details == {}
    
    # Test with all parameters
    error = ConversionError(
        "Conversion failed", 
        input_path="/path/to/file.doc", 
        conversion_type="doc",
        details={"error_code": 500}
    )
    assert str(error) == "Conversion failed"
    assert error.message == "Conversion failed"
    assert error.input_path == "/path/to/file.doc"
    assert error.conversion_type == "doc"
    assert error.details == {"error_code": 500}


def test_file_io_error():
    """Test FileIOError class."""
    # Test with minimum required parameters
    error = FileIOError("File operation failed")
    assert str(error) == "File operation failed"
    assert error.message == "File operation failed"
    assert error.file_path is None
    assert error.operation is None
    assert error.details == {}
    
    # Test with all parameters
    error = FileIOError(
        "File operation failed", 
        file_path="/path/to/file.txt", 
        operation="read",
        details={"permissions": "r--"}
    )
    assert str(error) == "File operation failed"
    assert error.message == "File operation failed"
    assert error.file_path == "/path/to/file.txt"
    assert error.operation == "read"
    assert error.details == {"permissions": "r--"}


def test_format_error_message():
    """Test format_error_message function."""
    # Test with error type and message
    msg = format_error_message("Validation", "Invalid URL")
    assert msg == "Validation Error: Invalid URL"
    
    # Test with context
    context = {"url": "example.com", "attempt": 3}
    msg = format_error_message("Validation", "Invalid URL", context)
    assert msg == "Validation Error: Invalid URL [url=example.com; attempt=3]"
    
    # Test with empty context
    msg = format_error_message("Validation", "Invalid URL", {})
    assert msg == "Validation Error: Invalid URL"


def test_create_error_details():
    """Test create_error_details function."""
    # Test with just an exception
    error = ValueError("Invalid value")
    details = create_error_details(error)
    assert details == {
        "error_type": "ValueError",
        "error_message": "Invalid value"
    }
    
    # Test with additional info
    error = ValueError("Invalid value")
    additional_info = {"context": "testing", "line": 42}
    details = create_error_details(error, additional_info)
    assert details == {
        "error_type": "ValueError",
        "error_message": "Invalid value",
        "context": "testing",
        "line": 42
    }