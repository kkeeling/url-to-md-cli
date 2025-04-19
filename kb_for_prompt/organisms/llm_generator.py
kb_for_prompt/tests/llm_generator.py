import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LlmGenerator:
    """Generates content using an LLM based on scanned document data."""

    # Define the prompt template as a class variable
    TOC_PROMPT_TEMPLATE = """
You are a documentation indexing assistant. Create a comprehensive table of contents in markdown format based on the content of the provided documents.

Format the output as a nested markdown list with:
1. Top-level sections as # headers
2. Sub-sections properly indented
3. Links to the document paths (use the 'path' attribute from the XML)

DOCUMENTS:
{documents}

Generate a clear, hierarchical, and well-structured table of contents that would help a user navigate the documentation.
Ensure the final output is only the markdown TOC, without any introductory text or explanations.
"""

    def __init__(self, llm_client: Optional[object] = None):
        """
        Initializes the LlmGenerator.

        Args:
            llm_client: An optional client object for interacting with the LLM.
                        This object is expected to have an 'invoke' method.
        """
        self.llm_client = llm_client

    def scan_and_build_xml(self, output_dir: Union[str, Path]) -> str:
        """
        Scans a directory and builds an XML representation of the documents.

        Args:
            output_dir: The directory containing the documents to scan.

        Returns:
            A string containing the XML representation of the documents.
            Returns an empty string or minimal XML structure if no documents are found.

        Note:
            This is a placeholder implementation. Replace it with your actual
            directory scanning and XML building logic. The expected XML format
            should contain document elements with path attributes.
            Example:
            <documents>
              <document path="path/to/doc1.md">
                <content>...</content>
              </document>
              <document path="path/to/doc2.py">
                <content>...</content>
              </document>
            </documents>
        """
        # Placeholder implementation - replace with actual logic
        logger.info(f"Scanning directory (placeholder): {output_dir}")
        # Simulate finding some documents
        root = ET.Element("documents")
        doc1 = ET.SubElement(root, "document", path=str(Path(output_dir) / "doc1.md"))
        content1 = ET.SubElement(doc1, "content")
        content1.text = "Content of document 1."
        doc2 = ET.SubElement(root, "document", path=str(Path(output_dir) / "subdir/doc2.py"))
        content2 = ET.SubElement(doc2, "content")
        content2.text = "Content of document 2 in a subdirectory."

        # Return the XML as a string
        # Use encoding='unicode' for string output, default is 'us-ascii'
        # xml_declaration=True adds <?xml version='1.0' encoding='unicode'?>
        return ET.tostring(root, encoding='unicode', xml_declaration=False)


    def generate_toc(self, output_dir: Union[str, Path]) -> Optional[str]:
        """
        Generates a Table of Contents (TOC) in markdown format using an LLM.

        Args:
            output_dir: The directory containing the documents to be included in the TOC.

        Returns:
            A string containing the generated markdown TOC, or None if an error occurs
            or no documents are found.
        """
        if not self.llm_client:
            logger.error("LLM client is not configured. Cannot generate TOC.")
            return None

        logger.info(f"Starting TOC generation for directory: {output_dir}")
        try:
            xml_data = self.scan_and_build_xml(output_dir)
        except Exception as e:
            logger.error(f"Error during XML generation for {output_dir}: {e}", exc_info=True)
            return None

        if not xml_data:
            logger.warning(f"No XML data generated from {output_dir}. Cannot generate TOC.")
            return None

        # Basic check if the XML contains any document elements
        try:
            root = ET.fromstring(xml_data)
            if not root.findall('.//document'):
                 logger.warning(f"XML data from {output_dir} contains no document elements. Cannot generate TOC.")
                 return None
        except ET.ParseError as e:
            logger.error(f"Failed to parse generated XML: {e}\nXML Data:\n{xml_data}", exc_info=True)
            return None
        except Exception as e: # Catch other potential errors during parsing/checking
            logger.error(f"An unexpected error occurred while checking XML structure: {e}", exc_info=True)
            return None


        prompt = self.TOC_PROMPT_TEMPLATE.format(documents=xml_data)
        model_alias = "gemini/gemini-2.5-pro-preview-03-25" # As requested

        try:
            logger.info(f"Calling LLM ({model_alias}) to generate TOC...")
            # Assuming the llm_client has an 'invoke' method that takes the prompt
            # and model details. Adjust if your client API differs.
            response = self.llm_client.invoke(prompt, model=model_alias) # Adapt this call if needed

            # Assuming the response object has the generated text directly
            # or in an attribute like 'content' or 'text'. Adjust as needed.
            generated_toc = response if isinstance(response, str) else getattr(response, 'content', str(response))

            logger.info("Successfully generated TOC from LLM.")
            return generated_toc.strip()

        except Exception as e:
            logger.error(f"LLM client failed to generate TOC: {e}", exc_info=True)
            return None

# Example usage (optional, for testing purposes)
if __name__ == '__main__':
    # This requires a mock or real LLM client
    class MockLlmClient:
        def invoke(self, prompt: str, model: str) -> str:
            print(f"--- Mock LLM Call ({model}) ---")
            # print(f"Prompt:\n{prompt}") # Uncomment to see the full prompt
            print("--- End Mock LLM Call ---")
            # Simulate a markdown TOC response
            return """
# Document Collection

## Top Level Docs
- [Document 1](output/doc1.md)

## Subdirectory Docs
- [Document 2](output/subdir/doc2.py)
            """

    # Create an instance with the mock client
    generator = LlmGenerator(llm_client=MockLlmClient())

    # Define a dummy output directory
    dummy_output_dir = Path("./dummy_output")
    dummy_output_dir.mkdir(exist_ok=True) # Ensure it exists for the placeholder scan

    # Generate the TOC
    toc_markdown = generator.generate_toc(dummy_output_dir)

    if toc_markdown:
        print("\nGenerated TOC:")
        print(toc_markdown)
    else:
        print("\nFailed to generate TOC.")

    # Clean up dummy directory if needed
    # import shutil
    # shutil.rmtree(dummy_output_dir)
