"""
Module for generating LLM-friendly XML from markdown files.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union, Optional

from rich.console import Console

from kb_for_prompt.atoms.error_utils import FileIOError


class LlmGenerator:
    """
    Generates an XML structure containing the content of markdown files
    from a specified directory and its subdirectories, suitable for LLM processing.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the LlmGenerator.
        
        Args:
            console: Optional Rich Console for output. Defaults to a new Console instance.
        """
        self.console = console if console else Console()
    
    def scan_and_build_xml(self, directory_path: Union[str, Path]) -> str:
        """
        Recursively scans a directory for markdown files (.md) and builds an XML string.

        The XML structure is:
        <documents>
            <document path="relative/path/to/file1.md">Content of file1</document>
            <document path="subdir/file2.md">Content of file2</document>
            ...
        </documents>

        Args:
            directory_path: The path to the directory to scan.

        Returns:
            An XML string containing the documents.

        Raises:
            FileNotFoundError: If the specified directory does not exist.
            NotADirectoryError: If the specified path is not a directory.
            FileIOError: If there's an issue reading the directory contents during scanning.
        """
        dir_path = Path(directory_path).resolve()

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory_path}")

        root = ET.Element("documents")
        found_files = False

        try:
            # Use rglob to find all .md files recursively
            for item in dir_path.rglob("*.md"):
                if item.is_file():
                    relative_path = item.relative_to(dir_path)
                    try:
                        content = item.read_text(encoding="utf-8")
                        doc_element = ET.SubElement(root, "document")
                        doc_element.set("path", str(relative_path).replace("\\", "/")) # Ensure consistent path separators
                        # Set text content, ensuring empty strings are preserved
                        doc_element.text = content if content else ""
                        found_files = True
                    except (IOError, OSError, UnicodeDecodeError) as e:
                        # Handle file reading errors gracefully by skipping the file
                        self.console.print(f"[warning]Skipping file '{relative_path}' due to error: {e}[/warning]")
                        continue # Skip to the next file
                    except Exception as e:
                        # Catch any other unexpected errors during file processing
                        self.console.print(f"[warning]Skipping file '{relative_path}' due to unexpected error: {e}[/warning]")
                        continue
        except PermissionError as e:
             # Handle errors accessing subdirectories during rglob
             raise FileIOError(
                message=f"Permission denied while scanning directory contents: {e}",
                file_path=str(dir_path),
                operation="read_directory"
            ) from e
        except OSError as e:
             # Handle other OS errors during directory scanning
             raise FileIOError(
                message=f"Failed to read directory contents: {e}",
                file_path=str(dir_path),
                operation="read_directory"
            ) from e
        except Exception as e:
            # Catch any other unexpected errors during directory traversal
            raise FileIOError(
                message=f"An unexpected error occurred while scanning directory: {e}",
                file_path=str(dir_path),
                operation="read_directory"
            ) from e


        # Generate the XML string
        # Using 'unicode' ensures it's a string, not bytes.
        # Set short_empty_elements=False to ensure empty tags are written as <tag></tag>
        # instead of <tag/>, which makes the .text attribute "" instead of None when parsed back.
        xml_string = ET.tostring(root, encoding="unicode", xml_declaration=False, short_empty_elements=False)
             
        return xml_string
