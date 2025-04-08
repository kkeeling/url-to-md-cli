"""
Atoms module for kb_for_prompt.

In atomic design, atoms are the basic building blocks of matter.
Applied to this project, atoms are the foundational utility functions
and primitive components that form the basis of our application.

This module contains utility functions for file path handling, input validation,
type detection, and error handling.
"""

# Import and expose key utility functions
from kb_for_prompt.atoms.error_utils import (
    KbForPromptError,
    ValidationError,
    ConversionError,
    FileIOError,
    format_error_message,
    create_error_details
)

from kb_for_prompt.atoms.path_utils import (
    resolve_path,
    create_file_url,
    ensure_directory_exists,
    generate_output_filename,
    is_same_file
)

from kb_for_prompt.atoms.type_detector import (
    detect_input_type,
    detect_file_type,
    get_supported_extensions,
    is_url,
    is_file_path,
    is_supported_file_type
)

from kb_for_prompt.atoms.input_validator import (
    validate_url,
    validate_file_path,
    validate_file_type,
    validate_directory_path,
    validate_input_item
)

# For convenience, expose all functions in the public API
__all__ = [
    # Error utilities
    'KbForPromptError',
    'ValidationError',
    'ConversionError',
    'FileIOError',
    'format_error_message',
    'create_error_details',
    
    # Path utilities
    'resolve_path',
    'create_file_url',
    'ensure_directory_exists',
    'generate_output_filename',
    'is_same_file',
    
    # Type detection
    'detect_input_type',
    'detect_file_type',
    'get_supported_extensions',
    'is_url',
    'is_file_path',
    'is_supported_file_type',
    
    # Input validation
    'validate_url',
    'validate_file_path',
    'validate_file_type',
    'validate_directory_path',
    'validate_input_item'
]