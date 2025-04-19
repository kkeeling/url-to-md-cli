#!/usr/bin/env python3

"""
Main entry point script for running the kb-for-prompt application
with the LiteLLM client integration.
"""

import sys
import logging
import os

# Attempt to import necessary components
try:
    from kb_for_prompt.organisms.menu_system import MenuSystem
    from kb_for_prompt.organisms.llm_client import LiteLlmClient
except ImportError as e:
    print(f"Error: Failed to import necessary modules ({e}).", file=sys.stderr)
    print("Please ensure the kb-for-prompt package is installed correctly.", file=sys.stderr)
    sys.exit(1)

def main():
    """
    Initializes the LLM client and menu system, then runs the application.
    """
    # Configure basic logging
    # You might want to customize the logging level and format further
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Silence noisy libraries if needed (optional)
    # logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info("Starting kb-for-prompt application...")

    # 1. Create LiteLlmClient instance
    llm_client = None
    try:
        # API key handling for Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY environment variable not set. LLM features will be unavailable.")
            print("Warning: GEMINI_API_KEY environment variable not set. LLM features will be unavailable.", file=sys.stderr)
            print("Set it with: export GEMINI_API_KEY=your-api-key", file=sys.stderr)
            # Continue without LLM client
            llm_client = None
        else:
            llm_client = LiteLlmClient(api_key=api_key)
        logging.info("LiteLlmClient initialized successfully.")
    except ImportError as e:
        # This error is caught if litellm is not installed
        logging.error(f"Failed to import litellm: {e}. LLM features will be unavailable.")
        print(f"Warning: {e}. Install 'litellm' for LLM features.", file=sys.stderr)
        # Decide if you want to exit or continue without LLM features.
        # For now, we'll let MenuSystem handle the llm_client being None if LlmGenerator is robust enough.
        # If LLM features are essential, uncomment the sys.exit(1) below.
        # sys.exit(1)
        pass # Continue without LLM client if import fails
    except Exception as e:
        logging.error(f"Failed to initialize LiteLlmClient: {e}", exc_info=True)
        print(f"Error initializing LLM client: {e}. Proceeding without LLM features.", file=sys.stderr)
        # Continue without LLM client

    # 2. Initialize MenuSystem with the client (client can be None)
    try:
        menu_system = MenuSystem(llm_client=llm_client)
        logging.info("MenuSystem initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize MenuSystem: {e}", exc_info=True)
        print(f"Critical Error: Failed to initialize the application menu: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Run the app
    exit_code = 0
    try:
        exit_code = menu_system.run()
        logging.info(f"Application finished with exit code: {exit_code}")
    except Exception as e:
        logging.error(f"An uncaught exception occurred during application execution: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        exit_code = 1 # Indicate an error exit

    # 4. Exit with the appropriate code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
