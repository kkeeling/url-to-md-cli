"""
Module for a simple LLM client implementation.
"""

import logging
from typing import Optional

class SimpleLlmClient:
    """
    A basic LLM client simulator for testing and development purposes.

    This client mimics the interface expected by LlmGenerator (an `invoke` method)
    but returns hardcoded responses instead of making actual API calls.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SimpleLlmClient.

        Args:
            api_key: An optional API key (not used in this simple implementation).
        """
        # In a real client, the API key would be used for authentication.
        self.api_key = api_key
        logging.info("SimpleLlmClient initialized (simulation mode).")

    def invoke(self, prompt: str, model: str) -> str:
        """
        Simulates invoking an LLM with the given prompt and model.

        Args:
            prompt: The input prompt string for the LLM.
            model: The identifier of the model to use (e.g., "gemini/gemini-1.5-pro-latest").

        Returns:
            A hardcoded string representing a simulated LLM response in markdown format.
        """
        logging.info(f"Simulating LLM call with model: {model}")
        # Log a snippet of the prompt for debugging (optional)
        prompt_snippet = (prompt[:100] + '...') if len(prompt) > 100 else prompt
        logging.debug(f"Prompt snippet: {prompt_snippet}")

        # Return a generic placeholder response based on typical usage
        if "table of contents" in prompt.lower():
            # Simulate a TOC response
            return """
# Simulated Table of Contents

## Section 1
- [Document A](path/to/document_a.md)
- [Document B](path/to/document_b.md)

## Section 2
- [Sub-section 2.1](path/to/document_c.md#sub-section-21)
  - [Document C](path/to/document_c.md)
"""
        elif "knowledge base" in prompt.lower() or "extract key information" in prompt.lower():
             # Simulate a KB response (could be XML or Markdown depending on prompt)
             # Returning Markdown here for simplicity, matching the KB prompt template expectation
            return """
# Simulated Knowledge Base

## Topic: Example Topic 1
- **Key Point:** Detail about topic 1 from document X.
- **Source:** `document_x.md`

## Topic: Example Topic 2
- **Key Point:** Detail about topic 2 from document Y.
- **Relationship:** Linked to Topic 1.
- **Source:** `document_y.md`
"""
        else:
            # Default generic response
            return f"Simulated response for model {model} based on the provided prompt."

