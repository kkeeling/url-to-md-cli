# menu_system.py
import sys
import os
from pathlib import Path
from enum import Enum, auto
from typing import Dict, Any, Optional

# Assuming prompts.py is in the path or adjusted relative path
# For this example, let's assume it's accessible directly
try:
    # Adjust this import based on your actual project structure
    from templates import prompts
except ImportError:
    # Fallback if the structure is different or running standalone
    # This might require adding the path to sys.path in a real scenario
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from templates import prompts

from rich.console import Console

class MenuState(Enum):
    """ Defines the different states of the menu system. """
    START = auto()
    MAIN_MENU = auto()
    SINGLE_ITEM_INPUT = auto()
    BATCH_INPUT = auto()
    PROCESSING = auto()
    TOC_PROMPT = auto()
    TOC_PROCESSING = auto()
    TOC_CONFIRM_SAVE = auto() # State for Task 6c
    KB_PROMPT = auto()
    KB_PROCESSING = auto()
    KB_CONFIRM_SAVE = auto()
    EXIT = auto()
    ERROR = auto()

class MenuSystem:
    """
    Manages the interactive menu flow for the application.
    Uses a state machine pattern to handle transitions.
    """
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.current_state = MenuState.START
        self.next_state = MenuState.START
        self.user_data: Dict[str, Any] = {} # Stores data between states
        self.state_handlers = {
            # ... other state handlers ...
            MenuState.TOC_CONFIRM_SAVE: self._handle_toc_confirm_save,
            # ... other state handlers ...
        }
        # Add placeholder data for demonstration/testing
        self.user_data['output_dir'] = Path("./output")
        self.user_data['toc_content'] = "Line 1\nLine 2\n" + "\n".join([f"Line {i}" for i in range(3, 60)])


    def run(self):
        """ Runs the menu system state machine. """
        while self.current_state != MenuState.EXIT:
            handler = self.state_handlers.get(self.current_state)
            if handler:
                try:
                    # Execute the handler for the current state
                    handler()
                    # Transition to the next state determined by the handler
                    self.current_state = self.next_state
                except Exception as e:
                    self.console.print(f"[bold red]An unexpected error occurred in state {self.current_state}: {e}[/bold red]")
                    self.current_state = MenuState.ERROR # Or handle error appropriately
            else:
                self.console.print(f"[bold red]Error: No handler defined for state {self.current_state}. Exiting.[/bold red]")
                self.current_state = MenuState.EXIT

            if self.current_state == MenuState.ERROR:
                # Simple error handling: print message and exit
                self.console.print("[bold red]Entering error state. Exiting application.[/bold red]")
                break
        
        self.console.print("Exiting application.")


    def _save_content_to_file(self, content: str, file_path: Path) -> bool:
        """
        Saves the given content to the specified file path.

        Args:
            content: The string content to save.
            file_path: The Path object representing the target file.

        Returns:
            True if saving was successful, False otherwise.
        """
        try:
            # Ensure the output directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.console.print(f"[green]Successfully saved content to:[/green] {file_path}")
            return True
        except IOError as e:
            self.console.print(f"[bold red]Error saving file {file_path}: {e}[/bold red]")
            return False
        except Exception as e:
            self.console.print(f"[bold red]An unexpected error occurred while saving file {file_path}: {e}[/bold red]")
            return False


    def _handle_toc_confirm_save(self):
        """
        Handles confirmation for saving the generated Table of Contents.
        Retrieves TOC content, prompts user, saves if confirmed, and transitions state.
        """
        self.console.print("\n[bold blue]Step: Confirm TOC Save[/bold blue]")

        # 1. Retrieve generated TOC content and output directory
        toc_content: Optional[str] = self.user_data.get("toc_content")
        output_dir: Optional[Path] = self.user_data.get("output_dir")

        # 3. Handle the case where content is unexpectedly None
        if toc_content is None:
            self.console.print("[bold red]Error:[/bold red] TOC content not found in user data. Cannot proceed with saving.")
            # Transition to KB prompt as per requirement (or maybe an error state?)
            self.next_state = MenuState.KB_PROMPT
            return
        
        if output_dir is None:
            self.console.print("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
            # Decide on appropriate transition, KB_PROMPT seems reasonable
            self.next_state = MenuState.KB_PROMPT
            return

        # 4. Generate a preview (first 50 lines)
        preview_lines = toc_content.splitlines()[:50]
        content_preview = "\n".join(preview_lines)
        if len(toc_content.splitlines()) > 50:
            content_preview += "\n[italic](... preview truncated ...)[/italic]"

        # 5. Use prompt_save_confirmation
        save_confirmed = prompts.prompt_save_confirmation(content_preview, console=self.console)

        if save_confirmed:
            # 6. If saving:
            target_path = output_dir / "toc.md"
            self.console.print(f"Attempting to save TOC to: {target_path}")
            # Call the save utility
            save_successful = self._save_content_to_file(toc_content, target_path)
            if save_successful:
                self.console.print("[green]TOC saved successfully.[/green]")
            else:
                self.console.print("[yellow]TOC saving failed. Check error messages above.[/yellow]")
            # Transition to KB_PROMPT after save attempt (success or failure)
            self.next_state = MenuState.KB_PROMPT
        else:
            # 7. If not saving:
            self.console.print("Save cancelled by user.")
            # Use prompt_retry_generation
            retry_generation = prompts.prompt_retry_generation("TOC generation", console=self.console)
            if retry_generation:
                # Transition to TOC_PROCESSING if retrying
                self.console.print("Retrying TOC generation...")
                self.next_state = MenuState.TOC_PROCESSING
            else:
                # Transition to KB_PROMPT if not retrying
                self.console.print("Skipping TOC generation retry.")
                self.next_state = MenuState.KB_PROMPT

# Example of how to run (optional, for direct execution)
if __name__ == "__main__":
    # To test this specific handler, we can manually set the state
    menu = MenuSystem()
    menu.current_state = MenuState.TOC_CONFIRM_SAVE
    # Add some dummy data if needed for testing run
    if 'output_dir' not in menu.user_data:
         menu.user_data['output_dir'] = Path("./test_output")
    if 'toc_content' not in menu.user_data:
         menu.user_data['toc_content'] = "# Table of Contents\n\n*   [Section 1](#section-1)\n*   [Section 2](#section-2)"

    # Need to add KB_PROMPT handler or adjust run loop for testing this state transition
    # For now, let's add a dummy handler for KB_PROMPT to avoid crashing
    def _dummy_kb_prompt():
        print("Entered KB_PROMPT state. Exiting for test.")
        menu.next_state = MenuState.EXIT
    menu.state_handlers[MenuState.KB_PROMPT] = _dummy_kb_prompt
    
    def _dummy_toc_processing():
        print("Entered TOC_PROCESSING state. Exiting for test.")
        menu.next_state = MenuState.EXIT
    menu.state_handlers[MenuState.TOC_PROCESSING] = _dummy_toc_processing

    menu.run()
