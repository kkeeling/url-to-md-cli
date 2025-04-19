"""
Module for generating LLM-friendly XML from markdown files.
"""

import os
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Union, Optional, Any

from rich.console import Console

from kb_for_prompt.atoms.error_utils import FileIOError


class LlmGenerator:
    """
    Generates an XML structure containing the content of markdown files
    from a specified directory and its subdirectories, suitable for LLM processing.
    Can also generate a Table of Contents (TOC) by using an LLM.
    """

    def __init__(self, console: Optional[Console] = None, llm_client: Optional[Any] = None):
        """
        Initialize the LlmGenerator.
        
        Args:
            console: Optional Rich Console for output. Defaults to a new Console instance.
            llm_client: Optional LLM client for generating content from XML data.
        """
        self.console = console if console else Console()
        self.llm_client = llm_client
    
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
        
    def generate_toc(self, directory_path: Union[str, Path]) -> Optional[str]:
        """
        Generate a Table of Contents (TOC) in markdown format by calling an LLM with XML document data.
        
        This method:
        1. Scans the provided directory to build an XML representation of the markdown files.
        2. If no documents are found, returns None.
        3. Constructs a prompt for the LLM, injecting the XML data.
        4. Calls the LLM with the specified model alias.
        5. Returns the generated markdown TOC or None if an error occurs.
        
        Args:
            directory_path: The path to the directory containing markdown files.
            
        Returns:
            A markdown-formatted table of contents or None if generation fails.
        """
        if not self.llm_client:
            logging.warning("No LLM client provided, cannot generate TOC.")
            return None
            
        try:
            # Get the XML representation of markdown files
            xml_data = self.scan_and_build_xml(directory_path)
            
            # Parse the XML and check if any document elements exist
            try:
                root = ET.fromstring(xml_data)
                if len(root.findall("document")) == 0:
                    logging.info("No markdown documents found in the directory, skipping TOC generation.")
                    return None
            except ET.ParseError as e:
                logging.error(f"Malformed XML data, cannot generate TOC: {e}")
                return None
                
            # Construct the prompt with the XML data
            prompt_template = """
You are a documentation indexing assistant. Create a comprehensive table of contents in markdown format based on the content of the provided documents.

Format the output as a nested markdown list with:
1. Top-level sections as # headers
2. Sub-sections properly indented
3. Links to the document paths

DOCUMENTS:
{{documents}}

Generate a clear, hierarchical, and well-structured table of contents that would help a user navigate the documentation.
"""
            # Replace the placeholder with the actual XML
            final_prompt = prompt_template.replace("{{documents}}", xml_data)
            
            # Specify the model alias to use
            model_alias = "gemini/gemini-2.5-pro-preview-03-25"
            
            # Call the LLM client to generate the TOC
            try:
                # The exact API of the llm_client is assumed to be:
                # llm_client.generate(prompt, model_alias) or similar
                # Adjust if the actual API is different
                generated_toc = self.llm_client.generate(prompt=final_prompt, model_alias=model_alias)
                return generated_toc
            except Exception as e:
                logging.error(f"LLM call failed for TOC generation: {e}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to generate TOC: {e}")
            return None
