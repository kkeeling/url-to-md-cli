import unittest
from unittest.mock import patch, MagicMock, call, ANY
from pathlib import Path
import logging # Import logging

# Assume menu_system.py is in the same directory or accessible via PYTHONPATH
# Adjust the import path based on your project structure
try:
    from kb_for_prompt.organisms.menu_system import MenuSystem, MenuState
    # Assuming templates are accessible relative to menu_system or via PYTHONPATH
    from kb_for_prompt.templates import prompts
    from kb_for_prompt.templates import banner # Import banner for display_section_header
    from kb_for_prompt.templates.progress import display_spinner # Import spinner
except ImportError:
    # Fallback for running the test file directly
    from menu_system import MenuSystem, MenuState
    import sys
    # Add parent directory to sys.path if templates are there
    sys.path.append(str(Path(__file__).parent.parent / 'templates'))
    import prompts
    import banner
    from progress import display_spinner


class TestMenuSystemTocConfirmSave(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        # Mock the LLM client passed to LlmGenerator
        self.mock_llm_client = MagicMock()
        self.menu = MenuSystem(console=self.mock_console, llm_client=self.mock_llm_client)
        # Set initial state for testing the handler
        self.menu.current_state = MenuState.TOC_CONFIRM_SAVE
        # Provide necessary user_data
        self.output_dir_str = "./test_output_dir" # Use string as stored in user_data
        self.output_dir = Path(self.output_dir_str)
        self.toc_content = "Line 1\nLine 2\n" + "\n".join([f"Line {i}" for i in range(3, 60)])
        self.menu.user_data = {
            "output_dir": self.output_dir_str, # Store string path
            "generated_toc_content": self.toc_content # Renamed key
        }
        # Mock the save method directly on the instance
        self.menu._save_content_to_file = MagicMock(return_value=True)
        # Mock transition_to to check state changes
        self.menu._transition_to = MagicMock()
        # Mock retry prompt
        self.menu.prompt_retry_generation = MagicMock() # Mock directly if needed


    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_content_none(self, mock_header):
        """Test handler when toc_content is missing."""
        self.menu.user_data["generated_toc_content"] = None # Use correct key

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] TOC content not found in user data. Cannot proceed with saving.")
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROMPT)

    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_output_dir_none(self, mock_header):
        """Test handler when output_dir is missing."""
        self.menu.user_data["output_dir"] = None

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROMPT)

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_user_confirms_save_success(self, mock_header, mock_prompt_save):
        """Test handler when user confirms save and save succeeds."""
        mock_prompt_save.return_value = True
        expected_preview = "\n".join(self.toc_content.splitlines()[:50]) + "\n[italic](... preview truncated ...)[/italic]"
        expected_target_path = self.output_dir / "toc.md"

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check preview generation and prompt call
        mock_prompt_save.assert_called_once_with(expected_preview, console=self.mock_console)

        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(self.toc_content, expected_target_path)
        self.mock_console.print.assert_any_call(f"Attempting to save TOC to: {expected_target_path}")
        self.mock_console.print.assert_any_call("[green]TOC saved successfully.[/green]") # Assumes save mock returns True

        # Check state transition
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROMPT)

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_user_confirms_save_failure(self, mock_header, mock_prompt_save):
        """Test handler when user confirms save but save fails."""
        mock_prompt_save.return_value = True
        self.menu._save_content_to_file.return_value = False # Simulate save failure
        expected_target_path = self.output_dir / "toc.md"

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(self.toc_content, expected_target_path)
        self.mock_console.print.assert_any_call("[yellow]TOC saving failed. Check error messages above.[/yellow]")

        # Check state transition (should still go to KB_PROMPT)
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROMPT)

    @patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation')
    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_user_denies_save_retries(self, mock_header, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = True # User wants to retry

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check prompts
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("TOC generation", console=self.mock_console)

        # Check no save call
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Retrying TOC generation...")


        # Check state transition
        self.menu._transition_to.assert_called_once_with(MenuState.TOC_PROCESSING)

    @patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation')
    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_handle_toc_confirm_save_user_denies_save_no_retry(self, mock_header, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses not to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = False # User does not want to retry

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check prompts
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("TOC generation", console=self.mock_console)

        # Check no save call
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Skipping TOC generation retry.")

        # Check state transition
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROMPT)

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header') # Patch display_section_header
    def test_preview_truncation(self, mock_header, mock_prompt_save):
        """Test that preview is correctly generated and truncated."""
        # Content with exactly 50 lines
        short_content = "\n".join([f"Line {i}" for i in range(1, 51)])
        self.menu.user_data["generated_toc_content"] = short_content # Use correct key
        expected_preview_short = short_content

        # Content with 51 lines
        long_content = "\n".join([f"Line {i}" for i in range(1, 52)])
        self.menu.user_data["generated_toc_content"] = long_content # Use correct key
        expected_preview_long = "\n".join([f"Line {i}" for i in range(1, 51)]) + "\n[italic](... preview truncated ...)[/italic]"

        # Test with short content
        mock_prompt_save.return_value = False # Don't save, just check preview
        self.menu._handle_toc_confirm_save()
        mock_prompt_save.assert_called_with(expected_preview_short, console=self.mock_console)
        mock_header.assert_called_with("Save Table of Contents", console=self.mock_console)

        # Reset mocks and test with long content
        mock_prompt_save.reset_mock()
        mock_header.reset_mock()
        self.menu.user_data["generated_toc_content"] = long_content # Use correct key
        # Need to reset transition mock as well, as it's called in the previous run
        self.menu._transition_to.reset_mock()
        # Mock retry prompt to return False to avoid transition loop
        with patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation', return_value=False):
            self.menu._handle_toc_confirm_save()
        mock_prompt_save.assert_called_with(expected_preview_long, console=self.mock_console)
        mock_header.assert_called_with("Save Table of Contents", console=self.mock_console)


# --- NEW TEST CLASS FOR KB PROMPT ---
class TestMenuSystemKbPrompt(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        # Mock the LLM client passed to LlmGenerator
        self.mock_llm_client = MagicMock()
        self.menu = MenuSystem(console=self.mock_console, llm_client=self.mock_llm_client)
        # Set initial state for testing the handler
        self.menu.current_state = MenuState.KB_PROMPT
        # Mock transition_to
        self.menu._transition_to = MagicMock()
        # Mock _ask_convert_another
        self.menu._ask_convert_another = MagicMock()

    @patch('kb_for_prompt.organisms.menu_system.prompt_for_kb_generation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_prompt_yes(self, mock_header, mock_prompt_kb):
        """Test handler when user chooses YES for KB generation."""
        mock_prompt_kb.return_value = True

        self.menu._handle_kb_prompt()

        # Assertions
        mock_header.assert_called_once_with("Knowledge Base Generation", console=self.mock_console)
        mock_prompt_kb.assert_called_once_with(console=self.mock_console)
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROCESSING)
        self.menu._ask_convert_another.assert_not_called() # Should not be called if user says yes

    @patch('kb_for_prompt.organisms.menu_system.prompt_for_kb_generation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_prompt_no(self, mock_header, mock_prompt_kb):
        """Test handler when user chooses NO for KB generation."""
        mock_prompt_kb.return_value = False

        self.menu._handle_kb_prompt()

        # Assertions
        mock_header.assert_called_once_with("Knowledge Base Generation", console=self.mock_console)
        mock_prompt_kb.assert_called_once_with(console=self.mock_console)
        self.menu._ask_convert_another.assert_called_once_with() # Should be called if user says no
        self.menu._transition_to.assert_not_called() # Should not transition if user says no


# --- NEW TEST CLASS FOR KB PROCESSING ---
class TestMenuSystemKbProcessing(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        # Mock the LLM client passed to LlmGenerator
        self.mock_llm_client = MagicMock()
        self.menu = MenuSystem(console=self.mock_console, llm_client=self.mock_llm_client)
        # Mock the specific generator method
        self.menu.llm_generator.generate_kb = MagicMock()
        # Mock transition_to
        self.menu._transition_to = MagicMock()
        # Mock _ask_convert_another
        self.menu._ask_convert_another = MagicMock()
        # Set initial state and user data
        self.menu.current_state = MenuState.KB_PROCESSING
        self.output_dir_str = "./fake_output"
        self.output_dir = Path(self.output_dir_str)
        self.menu.user_data = {"output_dir": self.output_dir_str}
        # Disable logging during tests unless needed
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after tests."""
        logging.disable(logging.NOTSET)

    @patch('kb_for_prompt.organisms.menu_system.display_spinner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_success(self, mock_header, mock_spinner):
        """Test successful KB generation."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value.__enter__.return_value = mock_spinner_instance
        expected_kb_content = "<kb>Generated KB</kb>"
        self.menu.llm_generator.generate_kb.return_value = expected_kb_content

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        mock_spinner.assert_called_once_with("Calling LLM for KB generation...", console=self.mock_console)
        self.menu.llm_generator.generate_kb.assert_called_once_with(self.output_dir)
        mock_spinner_instance.succeed.assert_called_once_with("KB generation successful.")
        mock_spinner_instance.fail.assert_not_called()
        self.assertEqual(self.menu.user_data.get("generated_kb_content"), expected_kb_content)
        self.menu._transition_to.assert_called_once_with(MenuState.KB_CONFIRM_SAVE)
        self.menu._ask_convert_another.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.display_spinner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_failure_returns_none(self, mock_header, mock_spinner):
        """Test failed KB generation (LLM returns None)."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value.__enter__.return_value = mock_spinner_instance
        self.menu.llm_generator.generate_kb.return_value = None

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        mock_spinner.assert_called_once_with("Calling LLM for KB generation...", console=self.mock_console)
        self.menu.llm_generator.generate_kb.assert_called_once_with(self.output_dir)
        mock_spinner_instance.fail.assert_called_once_with("KB generation failed or returned no content.")
        mock_spinner_instance.succeed.assert_not_called()
        self.assertIsNone(self.menu.user_data.get("generated_kb_content"))
        self.mock_console.print.assert_any_call("[yellow]Skipping KB saving due to generation failure or error.[/yellow]")
        self.menu._transition_to.assert_not_called()
        self.menu._ask_convert_another.assert_called_once_with()

    @patch('kb_for_prompt.organisms.menu_system.display_spinner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_exception(self, mock_header, mock_spinner):
        """Test exception during KB generation."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value.__enter__.return_value = mock_spinner_instance
        test_exception = ValueError("LLM Error")
        self.menu.llm_generator.generate_kb.side_effect = test_exception

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        mock_spinner.assert_called_once_with("Calling LLM for KB generation...", console=self.mock_console)
        self.menu.llm_generator.generate_kb.assert_called_once_with(self.output_dir)
        # Spinner context manager handles exception, so succeed/fail might not be called on the instance itself
        # Check console output instead
        self.mock_console.print.assert_any_call(f"\n[bold red]An error occurred during KB generation: {test_exception}[/bold red]")
        self.assertIsNone(self.menu.user_data.get("generated_kb_content"))
        self.mock_console.print.assert_any_call("[yellow]Skipping KB saving due to generation failure or error.[/yellow]")
        self.menu._transition_to.assert_not_called()
        self.menu._ask_convert_another.assert_called_once_with()

    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_missing_output_dir(self, mock_header):
        """Test handling when output_dir is missing in user_data."""
        self.menu.user_data = {} # Clear user data

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        self.menu.llm_generator.generate_kb.assert_not_called()
        self.mock_console.print.assert_any_call("[bold red]Error: Output directory not found in user data. Skipping KB generation.[/bold red]")
        self.menu._transition_to.assert_not_called()
        self.menu._ask_convert_another.assert_called_once_with()

    # Note: Testing invalid Path string is tricky as Path() is robust.
    # This test assumes Path() might raise an error in some edge cases,
    # although unlikely for typical strings.
    @patch('kb_for_prompt.organisms.menu_system.Path', side_effect=TypeError("Invalid Path Type"))
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_invalid_output_dir_path(self, mock_header, mock_path):
        """Test handling when Path conversion fails for output_dir."""
        invalid_path_str = "/invalid:path"
        self.menu.user_data["output_dir"] = invalid_path_str

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        mock_path.assert_called_once_with(invalid_path_str)
        self.menu.llm_generator.generate_kb.assert_not_called()
        self.mock_console.print.assert_any_call(f"[bold red]Error: Invalid output directory path '{invalid_path_str}'. Skipping KB generation.[/bold red]")
        self.menu._transition_to.assert_not_called()
        self.menu._ask_convert_another.assert_called_once_with()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
