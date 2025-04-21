"""
Module for condensing knowledge base content using an LLM.

This module provides functionality to read a knowledge base file,
use a Language Model (LLM) via LiteLlmClient to condense its content
based on a specific prompt, and save the condensed version to a new file.
"""

import logging
from pathlib import Path
from typing import Optional, Any

# Attempt to import LiteLlmClient and handle potential ImportError if litellm is not installed
try:
    # Assuming LITELLM_AVAILABLE is defined in llm_client to indicate if litellm loaded
    from kb_for_prompt.organisms.llm_client import LiteLlmClient, LITELLM_AVAILABLE
except ImportError:
    # Handle cases where llm_client.py itself might have issues or LITELLM_AVAILABLE is needed
    LITELLM_AVAILABLE = False
    # Define a dummy class if the import fails completely, allowing the rest of the file to load
    # but the function will fail if called without litellm.
    class LiteLlmClient:
        """Dummy LiteLlmClient class for when litellm is not available."""
        def __init__(self, *args: Any, **kwargs: Any):
            raise ImportError("LiteLlmClient could not be imported. Ensure 'litellm' is installed and kb_for_prompt.organisms.llm_client is accessible.")
        def invoke(self, *args: Any, **kwargs: Any) -> Optional[str]:
            raise NotImplementedError("LLM client is not available because 'litellm' is not installed.")

from kb_for_prompt.atoms.error_utils import FileIOError, KbForPromptError

# Configure logging
# Consider moving configuration to a central place if the application grows
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

# --- LLM Prompt for Condensing ---
CONDENSE_PROMPT = """
Review the knowledge base provided below and condense it down to just the key information the agent needs to know to help the user.

Instead of listing each article in its entirety, organize the content by meaningful topic, and then provide a extremely detailed summary of the topic content as taken from each article that discusses that topic. Where some of the existing content discusses the same topic, merge that content into the detailed summary. Where some of the existing content provides conflicting or different points of view on the same topic, include all points of view and indicate which author provided the point of view.

There is no token limit for the knowledge base.

--- KNOWLEDGE BASE CONTENT ---
{knowledge_base_content}
"""

# --- Model Specification ---
# Using the specific model requested in the specification
CONDENSE_MODEL = "gemini/gemini-2.5-pro-preview-03-25"


def condense_knowledge_base(kb_file_path: Path) -> Optional[Path]:
    """
    Condenses a knowledge base Markdown file using an LLM.

    Reads the content of the input file, sends it to an LLM with a specific
    prompt for condensation, and writes the result to a new file named
    'knowledge_base_condensed.md' in the same directory as the input file.

    Args:
        kb_file_path: Path object pointing to the knowledge base markdown file.

    Returns:
        The Path object of the created condensed file if successful.
        Returns None if any step in the process fails (e.g., file reading error,
        LLM client instantiation error, LLM invocation error, file writing error,
        or if the 'litellm' library is unavailable).

    Raises:
        This function aims to handle errors internally and return None on failure,
        but underlying operations (like file I/O or LLM client calls) could
        potentially raise exceptions if not caught internally by those components
        or if unexpected errors occur. Standard exceptions like FileNotFoundError
        or IOError might occur during file operations if initial checks fail,
        and errors from the LLM client (like API errors) might occur during invocation.
    """
    logger.info(f"Starting condensation process for: {kb_file_path}")

    # --- 1. Validate and Read Input File ---
    kb_content: str
    try:
        if not kb_file_path.is_file():
            # Log specific error for not found vs not a file
            if not kb_file_path.exists():
                 logger.error(f"Input file not found: {kb_file_path}")
            else:
                 logger.error(f"Input path exists but is not a file: {kb_file_path}")
            # Raise FileNotFoundError or a custom error if needed, but spec asks to return None
            # raise FileNotFoundError(f"Input file not found or is not a file: {kb_file_path}")
            return None

        logger.info(f"Reading content from {kb_file_path}...")
        kb_content = kb_file_path.read_text(encoding='utf-8')
        logger.debug(f"Successfully read {len(kb_content)} characters from {kb_file_path}.")

    except (IOError, OSError) as e:
        logger.error(f"Error reading file {kb_file_path}: {e}", exc_info=True)
        # Optionally wrap in FileIOError for consistency if needed elsewhere
        # raise FileIOError(message=str(e), file_path=str(kb_file_path), operation="read") from e
        return None
    except Exception as e: # Catch potential encoding errors or other unexpected issues
        logger.error(f"Unexpected error reading file {kb_file_path}: {e}", exc_info=True)
        return None

    # --- 2. Check Prerequisite and Instantiate LLM Client ---
    if not LITELLM_AVAILABLE:
        logger.error("Cannot condense knowledge base: The 'litellm' library is not installed or failed to load.")
        # Optionally raise an error here if this is considered a critical failure condition
        # raise ImportError("Condensation requires the 'litellm' library, which is not available.")
        return None

    llm_client: LiteLlmClient
    try:
        # API key handling might be needed depending on LiteLLM setup (e.g., env vars)
        # Pass API key if required: llm_client = LiteLlmClient(api_key="YOUR_API_KEY")
        llm_client = LiteLlmClient()
        logger.info("LiteLlmClient instantiated successfully.")
    except ImportError as e: # Catch error if dummy class was used
         logger.error(f"Failed to instantiate LiteLlmClient: {e}", exc_info=False) # Keep log clean
         return None
    except Exception as e: # Catch any other unexpected init errors
        logger.error(f"Unexpected error instantiating LiteLlmClient: {e}", exc_info=True)
        return None

    # --- 3. Prepare Prompt and Call LLM ---
    full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=kb_content)

    logger.info(f"Sending request to LLM model: {CONDENSE_MODEL}")
    condensed_content: Optional[str] = None
    try:
        # The invoke method in LiteLlmClient should handle specific litellm API errors
        condensed_content = llm_client.invoke(prompt=full_prompt, model=CONDENSE_MODEL)
    except Exception as e: # Catch unexpected errors during the invoke call itself
        # This might happen if invoke raises an error not caught internally
        logger.error(f"An unexpected error occurred during the LLM invoke call: {e}", exc_info=True)
        return None

    # --- 4. Handle LLM Response ---
    if not condensed_content:
        # LiteLlmClient's invoke method already logs errors, but we add context here.
        logger.error(f"LLM call failed or returned empty content for model {CONDENSE_MODEL}.")
        # Optionally raise a specific error
        # raise KbForPromptError(message="LLM failed to generate condensed content.", details={"model": CONDENSE_MODEL})
        return None

    logger.info("Received condensed content from LLM.")
    # Avoid logging potentially large content, log length instead
    logger.debug(f"Condensed content length: {len(condensed_content)} characters.")

    # --- 5. Calculate Output Path and Write File ---
    output_filename = "knowledge_base_condensed.md"
    output_path = kb_file_path.parent / output_filename

    logger.info(f"Attempting to write condensed knowledge base to: {output_path}")
    try:
        output_path.write_text(condensed_content, encoding='utf-8')
        logger.info(f"Successfully wrote condensed file: {output_path}")
    except (IOError, OSError) as e:
        logger.error(f"Error writing condensed file {output_path}: {e}", exc_info=True)
        # Optionally wrap in FileIOError
        # raise FileIOError(message=str(e), file_path=str(output_path), operation="write") from e
        return None
    except Exception as e: # Catch potential encoding errors or other unexpected issues
        logger.error(f"Unexpected error writing file {output_path}: {e}", exc_info=True)
        return None

    # --- 6. Return Output Path ---
    return output_path

# Example Usage (Optional - can be uncommented for direct testing)
# if __name__ == '__main__':
#     # Create a dummy KB file for testing in the current directory
#     # Adjust the path if needed, e.g., Path("data/knowledge_base.md")
#     sample_kb_path = Path("./knowledge_base_sample_for_condenser.md")
#     try:
#         sample_kb_path.write_text("# Sample KB\n\nThis is the first section.\n\n## Topic A\nDetails about A.\n\n## Topic B\nDetails about B.", encoding='utf-8')
#         print(f"Created sample file for testing: {sample_kb_path}")
#
#         print(f"\nAttempting to condense: {sample_kb_path}")
#         condensed_file_path = condense_knowledge_base(sample_kb_path)
#
#         if condensed_file_path:
#             print(f"\nCondensation successful!")
#             print(f"Output file: {condensed_file_path}")
#             # Optionally print content for verification
#             # print("\nCondensed Content:")
#             # print(condensed_file_path.read_text(encoding='utf-8'))
#         else:
#             print("\nCondensation failed. Check logs for details.")
#
#     except Exception as e:
#         print(f"An error occurred during the example run: {e}")
#     finally:
#         # Clean up the dummy file
#         if sample_kb_path.exists():
#             try:
#                 sample_kb_path.unlink()
#                 print(f"\nCleaned up sample file: {sample_kb_path}")
#             except OSError as e:
#                 print(f"Error cleaning up sample file {sample_kb_path}: {e}")
