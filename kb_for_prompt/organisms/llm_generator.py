"""
Module for generating LLM-friendly XML from markdown files and using LLMs for generation tasks.
"""

import os
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Union, Optional, Any

from rich.console import Console

from kb_for_prompt.atoms.error_utils import FileIOError

# Define the base path for templates relative to this file's location
# Assumes templates directory is at ../templates from the organisms directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class LlmGenerator:
    """
    Generates an XML structure containing the content of markdown files
    from a specified directory and its subdirectories, suitable for LLM processing.
    Can also generate a Table of Contents (TOC) or a Knowledge Base (KB) by using an LLM.
    """

    def __init__(self, console: Optional[Console] = None, llm_client: Optional[Any] = None):
        """
        Initialize the LlmGenerator.

        Args:
            console: Optional Rich Console for output. Defaults to a new Console instance.
            llm_client: Optional LLM client for generating content from XML data.
                        Expected to have an `invoke` method.
        """
        self.console = console if console else Console()
        self.llm_client = llm_client

    def _load_prompt_template(self, template_path: Path) -> Optional[str]:
        """
        Loads a prompt template from the specified file path.

        Args:
            template_path: The Path object pointing to the template file.

        Returns:
            The content of the template file as a string, or None if an error occurs.
        """
        try:
            if not template_path.is_file():
                logging.error(f"Prompt template file not found: {template_path}")
                return None
            return template_path.read_text(encoding="utf-8")
        except (IOError, OSError) as e:
            logging.error(f"Error reading prompt template file {template_path}: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading template {template_path}: {e}")
            return None

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
                        logging.warning(f"Skipping file '{relative_path}' due to error: {e}")
                        continue # Skip to the next file
                    except Exception as e:
                        # Catch any other unexpected errors during file processing
                        self.console.print(f"[warning]Skipping file '{relative_path}' due to unexpected error: {e}[/warning]")
                        logging.warning(f"Skipping file '{relative_path}' due to unexpected error: {e}")
                        continue
        except PermissionError as e:
             # Handle errors accessing subdirectories during rglob
             logging.error(f"Permission denied while scanning directory contents: {dir_path}", exc_info=True)
             raise FileIOError(
                message=f"Permission denied while scanning directory contents: {e}",
                file_path=str(dir_path),
                operation="read_directory"
            ) from e
        except OSError as e:
             # Handle other OS errors during directory scanning
             logging.error(f"OS error while scanning directory contents: {dir_path}", exc_info=True)
             raise FileIOError(
                message=f"Failed to read directory contents: {e}",
                file_path=str(dir_path),
                operation="read_directory"
            ) from e
        except Exception as e:
            # Catch any other unexpected errors during directory traversal
            logging.error(f"Unexpected error while scanning directory: {dir_path}", exc_info=True)
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
        2. If no documents are found or XML is invalid, returns None.
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
                if not xml_data: # Handle empty string case
                    logging.info("Scan returned empty XML data, skipping TOC generation.")
                    return None
                root = ET.fromstring(xml_data)
                if len(root.findall("document")) == 0:
                    logging.info("No markdown documents found in the XML, skipping TOC generation.")
                    return None
            except ET.ParseError as e:
                logging.error(f"Malformed XML data from scan, cannot generate TOC: {e}")
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
                # Assuming llm_client has an 'invoke' method based on test structure
                generated_toc = self.llm_client.invoke(final_prompt, model=model_alias)
                return generated_toc
            except Exception as e:
                logging.error(f"LLM call failed for TOC generation: {e}", exc_info=True)
                return None

        except (FileNotFoundError, NotADirectoryError, FileIOError) as e:
            logging.error(f"Failed to scan directory for TOC generation: {e}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during TOC generation: {e}", exc_info=True)
            return None

    def generate_kb(self, directory_path: Union[str, Path]) -> Optional[str]:
        """
        Generate a Knowledge Base (KB) in markdown format by calling an LLM.

        This method:
        1. Loads the KB extraction prompt template.
        2. Scans the provided directory to build an XML representation of the markdown files.
        3. If no documents are found or XML is invalid, returns None.
        4. Injects the XML data into the prompt template.
        5. Calls the LLM with the specified model alias.
        6. Returns the generated markdown KB or None if an error occurs.

        Args:
            directory_path: The path to the directory containing markdown files.

        Returns:
            A markdown-formatted knowledge base or None if generation fails.
        """
        if not self.llm_client:
            logging.warning("No LLM client provided, cannot generate KB.")
            return None

        try:
            # 1. Load the KB extraction prompt template
            template_path = TEMPLATE_DIR / "kb_extraction_prompt.md"
            prompt_template = self._load_prompt_template(template_path)
            if not prompt_template:
                # Error already logged in _load_prompt_template
                return None

            # 2. Scan the directory and build XML
            xml_data = self.scan_and_build_xml(directory_path)

            # 3. Check if XML contains documents
            try:
                if not xml_data: # Handle empty string case
                    logging.info("Scan returned empty XML data, skipping KB generation.")
                    return None
                root = ET.fromstring(xml_data)
                if len(root.findall("document")) == 0:
                    logging.info("No markdown documents found in the XML, skipping KB generation.")
                    return None
            except ET.ParseError as e:
                logging.error(f"Malformed XML data from scan, cannot generate KB: {e}")
                return None

            # 4. Inject XML data into the prompt
            if "{{documents}}" not in prompt_template:
                 logging.error(f"Placeholder '{{documents}}' not found in template: {template_path}")
                 return None
            final_prompt = prompt_template.replace("{{documents}}", xml_data)

            # 5. Call the LLM
            model_alias = "gemini/gemini-2.5-pro-preview-03-25"
            try:
                generated_kb = self.llm_client.invoke(final_prompt, model=model_alias)
                return generated_kb
            except Exception as e:
                logging.error(f"LLM call failed for KB generation: {e}", exc_info=True)
                return None

        except (FileNotFoundError, NotADirectoryError, FileIOError) as e:
            logging.error(f"Failed to scan directory for KB generation: {e}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during KB generation: {e}", exc_info=True)
            return None
