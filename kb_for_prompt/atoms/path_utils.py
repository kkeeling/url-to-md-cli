"""
Path utilities for the kb-for-prompt package.

This module provides utilities for working with file paths,
including resolving relative paths, creating file URLs, and
managing output directories.
"""

import os
from pathlib import Path
from typing import Union, Optional
from urllib.parse import urlparse, urljoin

from kb_for_prompt.atoms.error_utils import FileIOError


def resolve_path(path: Union[str, Path], base_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Resolve a path against a base path or the current working directory.
    
    Args:
        path: The path to resolve (absolute or relative)
        base_path: Optional base path to resolve against. If None, uses current working directory.
    
    Returns:
        A resolved Path object
    
    Example:
        >>> resolve_path("docs/file.txt")
        PosixPath('/current/working/dir/docs/file.txt')
        
        >>> resolve_path("docs/file.txt", "/base/path")
        PosixPath('/base/path/docs/file.txt')
    """
    if isinstance(path, str):
        path = Path(path)
    
    # If the path is already absolute, just return it
    if path.is_absolute():
        return path
    
    # Resolve against base_path or current working directory
    base = Path(base_path) if base_path else Path.cwd()
    return base / path


def create_file_url(file_path: Union[str, Path]) -> str:
    """
    Create a file URL from a file path.
    
    Args:
        file_path: The file path to convert (absolute or relative)
    
    Returns:
        A file URL string (e.g., "file:///path/to/file.txt")
    
    Example:
        >>> create_file_url("/path/to/file.txt")
        'file:///path/to/file.txt'
    """
    # Ensure we have an absolute path
    path = resolve_path(file_path)
    
    # Convert to a valid file URL
    try:
        path_str = str(path.absolute())
    except AttributeError:
        # Handle the case where path might be a MagicMock in tests
        path_str = str(path)
    
    # Handle Windows paths by adding an extra slash for the drive letter
    if os.name == 'nt' and len(path_str) >= 3 and path_str[1:3] == ':\\':
        return "file:///" + path_str.replace('\\', '/')
    
    # For non-Windows paths, ensure three slashes are used
    # If path_str already starts with a slash, we don't need to add it
    if path_str.startswith('/'):
        return f"file:///{path_str[1:]}"
    else:
        return f"file:///{path_str}"


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: The directory path to ensure exists
    
    Returns:
        The resolved Path object for the directory
    
    Raises:
        FileIOError: If the directory cannot be created
    
    Example:
        >>> ensure_directory_exists("output/docs")
        PosixPath('/current/working/dir/output/docs')
    """
    dir_path = resolve_path(directory)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    except Exception as e:
        raise FileIOError(
            message=f"Failed to create directory: {str(e)}",
            file_path=str(dir_path),
            operation="create_directory"
        )


def generate_output_filename(input_path: str, output_dir: Union[str, Path], suffix: str = ".md") -> Path:
    """
    Generate an output filename based on the input path.
    
    Args:
        input_path: The input path or URL
        output_dir: The directory where the output file will be saved
        suffix: The file suffix to add (default: ".md")
    
    Returns:
        A Path object for the output file
    
    Example:
        >>> generate_output_filename("https://example.com/page", "output")
        PosixPath('/current/working/dir/output/example_com_page.md')
        
        >>> generate_output_filename("/path/to/document.pdf", "output")
        PosixPath('/current/working/dir/output/document.md')
    """
    # Ensure output directory exists
    out_dir = ensure_directory_exists(output_dir)
    
    # Parse input to extract a reasonable filename
    parsed = urlparse(input_path)
    
    if parsed.scheme and parsed.netloc:  # This is a URL
        # Extract domain and path parts of the URL
        domain = parsed.netloc.replace('.', '_')
        path = parsed.path.replace('/', '_')
        
        # Clean up filename components
        filename = f"{domain}{path}".rstrip('_')
        
        # Remove common extensions
        if filename.endswith(('.html', '.htm', '.php')):
            filename = filename.rsplit('.', 1)[0]
    else:  # This is a file path
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
    
    # Add suffix if needed
    if not suffix.startswith('.'):
        suffix = f".{suffix}"
    
    # Create the final path
    output_path = out_dir / f"{filename}{suffix}"
    
    # Handle file name conflicts by adding a numeric suffix
    counter = 1
    while output_path.exists():
        output_path = out_dir / f"{filename}_{counter}{suffix}"
        counter += 1
    
    return output_path


def is_same_file(path1: Union[str, Path], path2: Union[str, Path]) -> bool:
    """
    Check if two paths refer to the same file.
    
    Args:
        path1: First file path
        path2: Second file path
    
    Returns:
        True if paths refer to the same file, False otherwise
    
    Example:
        >>> is_same_file("/path/to/file.txt", "/path/to/../to/file.txt")
        True
    """
    try:
        return Path(path1).resolve() == Path(path2).resolve()
    except Exception:
        return False