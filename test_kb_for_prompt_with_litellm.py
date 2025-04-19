"""
Test script for integrating and using LiteLlmClient with kb-for-prompt components.

This script demonstrates:
1. Initializing the LiteLlmClient.
2. Integrating the client with the MenuSystem (though MenuSystem itself isn't run here).
3. Performing a direct test call to the LLM using the client's invoke method.

Note: Ensure necessary environment variables (like API keys for the target LLM service)
are set before running this script if required by your LiteLLM configuration.
"""

import logging
import os
from rich.console import Console

# Assuming the script is run from the root directory where kb_for_prompt package resides
# Adjust imports if your structure differs or run with appropriate PYTHONPATH
try:
    from kb_for_prompt.organisms.llm_client import LiteLlmClient
    from kb_for_prompt.organisms.menu_system import MenuSystem
except ImportError as e:
    print(f"ImportError: {e}. Make sure kb_for_prompt is installed or accessible in PYTHONPATH.")
    print("You might need to run 'pip install -e .' from the project root.")
    exit(1)

# --- Configuration ---
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the model to use for the test call (replace if needed)
# Ensure this model is supported by your LiteLLM setup and credentials
TEST_MODEL = "gemini/gemini-2.5-pro-preview-03-25" # The model we want to use

# Define a simple test prompt
TEST_PROMPT = "Explain the concept of 'large language model' in one sentence."

# --- Main Test Logic ---
def run_test():
    """
    Runs the test sequence: initialize client, integrate with menu (optional), invoke LLM.
    """
    console = Console()
    logging.info("Starting LiteLLM client test...")

    # 1. Create an instance of LiteLlmClient
    # API keys might be needed depending on the model and LiteLLM setup.
    # LiteLLM often reads keys from environment variables (e.g., GOOGLE_API_KEY).
    # You can pass api_key='YOUR_API_KEY' if needed and not handled by env vars.
    try:
        logging.info("Initializing LiteLlmClient...")
        # Example: Pass API key directly if needed
        # api_key = os.getenv("YOUR_LLM_API_KEY_ENV_VAR") # Replace with your actual env var if needed
        # llm_client = LiteLlmClient(api_key=api_key)
        llm_client = LiteLlmClient()
        logging.info("LiteLlmClient initialized successfully.")
    except ImportError as e:
        logging.error(f"Failed to initialize LiteLlmClient: {e}")
        logging.error("Ensure the 'litellm' library is installed ('pip install litellm').")
        return
    except Exception as e:
        logging.error(f"An unexpected error occurred during LiteLlmClient initialization: {e}", exc_info=True)
        return

    # 2. Set up MenuSystem with the client (demonstrates integration)
    # We are not running the menu system's interactive loop here, just showing setup.
    try:
        logging.info("Initializing MenuSystem with the LLM client...")
        menu_system = MenuSystem(console=console, llm_client=llm_client)
        logging.info("MenuSystem initialized successfully.")
        # In a full application, you would call menu_system.run() here.
    except Exception as e:
        logging.error(f"An unexpected error occurred during MenuSystem initialization: {e}", exc_info=True)
        # Continue to LLM test even if menu system init fails, as the primary goal is client test
        pass

    # 3. Call a simple test method (client.invoke)
    logging.info(f"Attempting to invoke LLM (Model: {TEST_MODEL})...")
    console.print(f"\n[bold blue]Sending prompt:[/bold blue]\n{TEST_PROMPT}")

    try:
        response = llm_client.invoke(prompt=TEST_PROMPT, model=TEST_MODEL)

        if response:
            logging.info("LLM invocation successful.")
            console.print(f"\n[bold green]Received response:[/bold green]\n{response}")
        else:
            logging.warning("LLM invocation returned None or empty response.")
            console.print("\n[bold yellow]Received no content in the response.[/bold yellow]")

    except Exception as e:
        logging.error(f"An error occurred during LLM invocation: {e}", exc_info=True)
        console.print(f"\n[bold red]Error during LLM invocation:[/bold red] {e}")

    logging.info("LiteLLM client test finished.")

if __name__ == "__main__":
    run_test()
