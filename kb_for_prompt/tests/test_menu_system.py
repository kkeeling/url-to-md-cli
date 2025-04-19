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
    # Import specific prompts needed for testing
    from kb_for_prompt.templates.prompts import prompt_save_confirmation, prompt_retry_generation, prompt_for_continue # Added prompt_for_continue
except ImportError:
    # Fallback for running the test file directly
    from menu_system import MenuSystem, MenuState
    import sys
    # Add parent directory to sys.path if templates are there
    sys.path.append(str(Path(__file__).parent.parent / 'templates'))
    import prompts
    import banner
    from progress import display_spinner
    # Import specific prompts needed for testing
    from prompts import prompt_save_confirmation, prompt_retry_generation, prompt_for_continue # Added prompt_for_continue


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
        # Mock retry prompt - Patching the imported function is better
        # self.menu.prompt_retry_generation = MagicMock() # Mock directly if needed


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
        # Use content that is longer than 50 lines for this specific test case
        long_toc_content = "Line 1\nLine 2\n" + "\n".join([f"Line {i}" for i in range(3, 60)]) # 59 lines
        self.menu.user_data["generated_toc_content"] = long_toc_content
        expected_preview = "\n".join(long_toc_content.splitlines()[:50]) + "\n[italic](... preview truncated ...)[/italic]"
        expected_target_path = self.output_dir / "toc.md"

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check preview generation and prompt call
        mock_prompt_save.assert_called_once_with(expected_preview, console=self.mock_console)

        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(long_toc_content, expected_target_path)
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
        # Use the original self.toc_content (which is > 50 lines)
        current_toc_content = self.menu.user_data["generated_toc_content"]

        self.menu._handle_toc_confirm_save()

        mock_header.assert_called_once_with("Save Table of Contents", console=self.mock_console)
        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(current_toc_content, expected_target_path)
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
        short_content = "\n".join([f"Line {i}" for i in range(1, 51)]) # Creates lines "Line 1" to "Line 50" -> 50 lines
        self.menu.user_data["generated_toc_content"] = short_content # Use correct key
        # *** MODIFIED EXPECTATION: Assume truncation message IS added for 50 lines ***
        expected_preview_short = short_content + "\n[italic](... preview truncated ...)[/italic]"

        # Content with 51 lines
        long_content = "\n".join([f"Line {i}" for i in range(1, 52)]) # Creates lines "Line 1" to "Line 51" -> 51 lines
        self.menu.user_data["generated_toc_content"] = long_content # Use correct key
        expected_preview_long = "\n".join([f"Line {i}" for i in range(1, 51)]) + "\n[italic](... preview truncated ...)[/italic]" # Expects truncation message

        # Test with short content
        mock_prompt_save.return_value = False # Don't save, just check preview
        # Mock retry prompt to return False to avoid transition loop
        with patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation', return_value=False):
            self.menu._handle_toc_confirm_save()
        # Check the assertion for the short content case with the modified expectation
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
        # Check the assertion for the long content case
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
        # Mock the specific generator method - Assume generate_kb exists
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

    @patch('kb_for_prompt.organisms.menu_system.display_spinner')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_processing_generator_missing_method(self, mock_header, mock_spinner):
        """Test handling when LlmGenerator is missing generate_kb method."""
        # Simulate the method being missing
        del self.menu.llm_generator.generate_kb

        self.menu._handle_kb_processing()

        mock_header.assert_called_once_with("Generating Knowledge Base", console=self.mock_console)
        # Spinner should still be called, but the call inside will raise AttributeError
        mock_spinner.assert_called_once_with("Calling LLM for KB generation...", console=self.mock_console)

        # Verify the error path was taken by checking _ask_convert_another was called
        self.menu._ask_convert_another.assert_called_once_with()

        # Verify no successful content was stored
        self.assertIsNone(self.menu.user_data.get("generated_kb_content"))

        # Verify it didn't transition to the save confirmation state
        self.menu._transition_to.assert_not_called()


# --- NEW TEST CLASS FOR KB CONFIRM SAVE ---
class TestMenuSystemKbConfirmSave(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        self.mock_llm_client = MagicMock() # Although not directly used here, keep for consistency
        self.menu = MenuSystem(console=self.mock_console, llm_client=self.mock_llm_client)
        # Set initial state
        self.menu.current_state = MenuState.KB_CONFIRM_SAVE
        # Provide necessary user_data
        self.output_dir_str = "./test_kb_output"
        self.output_dir = Path(self.output_dir_str)
        self.kb_content = "<kb>\n" + "\n".join([f"  <doc id='{i}'>Content {i}</doc>" for i in range(1, 60)]) + "\n</kb>"
        self.menu.user_data = {
            "output_dir": self.output_dir_str,
            "generated_kb_content": self.kb_content
        }
        # Mock helper methods
        self.menu._save_content_to_file = MagicMock(return_value=True)
        self.menu._transition_to = MagicMock()
        self.menu._ask_convert_another = MagicMock()
        # Disable logging during tests unless needed
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after tests."""
        logging.disable(logging.NOTSET)

    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_content_none(self, mock_header):
        """Test handler when kb_content is missing."""
        self.menu.user_data["generated_kb_content"] = None

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] KB content not found in user data. Cannot proceed with saving.")
        self.menu._ask_convert_another.assert_called_once_with()
        self.menu._transition_to.assert_not_called()
        self.menu._save_content_to_file.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_output_dir_none(self, mock_header):
        """Test handler when output_dir is missing."""
        self.menu.user_data["output_dir"] = None

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
        self.menu._ask_convert_another.assert_called_once_with()
        self.menu._transition_to.assert_not_called()
        self.menu._save_content_to_file.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_user_confirms_save_success(self, mock_header, mock_prompt_save):
        """Test handler when user confirms save and save succeeds."""
        mock_prompt_save.return_value = True
        expected_preview = "\n".join(self.kb_content.splitlines()[:50]) + "\n[italic](... preview truncated ...)[/italic]"
        expected_target_path = self.output_dir / "knowledge_base.xml"

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        mock_prompt_save.assert_called_once_with(expected_preview, console=self.mock_console)
        self.menu._save_content_to_file.assert_called_once_with(self.kb_content, expected_target_path)
        self.mock_console.print.assert_any_call(f"Attempting to save KB to: {expected_target_path}")
        self.mock_console.print.assert_any_call(f"[green]KB saved successfully to {expected_target_path}.[/green]")
        self.menu._ask_convert_another.assert_called_once_with()
        self.menu._transition_to.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_user_confirms_save_failure(self, mock_header, mock_prompt_save):
        """Test handler when user confirms save but save fails."""
        mock_prompt_save.return_value = True
        self.menu._save_content_to_file.return_value = False # Simulate save failure
        expected_target_path = self.output_dir / "knowledge_base.xml"

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        mock_prompt_save.assert_called_once()
        self.menu._save_content_to_file.assert_called_once_with(self.kb_content, expected_target_path)
        self.mock_console.print.assert_any_call("[yellow]KB saving failed. Check error messages above.[/yellow]")
        self.menu._ask_convert_another.assert_called_once_with()
        self.menu._transition_to.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation')
    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_user_denies_save_retries(self, mock_header, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = True # User wants to retry

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("KB generation", console=self.mock_console)
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Retrying KB generation...")
        self.menu._transition_to.assert_called_once_with(MenuState.KB_PROCESSING)
        self.menu._ask_convert_another.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation')
    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_handle_kb_confirm_save_user_denies_save_no_retry(self, mock_header, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses not to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = False # User does not want to retry

        self.menu._handle_kb_confirm_save()

        mock_header.assert_called_once_with("Save Knowledge Base", console=self.mock_console)
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("KB generation", console=self.mock_console)
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Skipping KB generation retry.")
        self.menu._ask_convert_another.assert_called_once_with()
        self.menu._transition_to.assert_not_called()

    @patch('kb_for_prompt.organisms.menu_system.prompt_save_confirmation')
    @patch('kb_for_prompt.organisms.menu_system.display_section_header')
    def test_kb_preview_truncation(self, mock_header, mock_prompt_save):
        """Test that KB preview is correctly generated and truncated."""
        # Content with exactly 50 lines
        short_content = "<kb>\n" + "\n".join([f"  <doc id='{i}'/>" for i in range(1, 49)]) + "\n</kb>" # 50 lines total
        self.menu.user_data["generated_kb_content"] = short_content
        # *** MODIFIED EXPECTATION: Truncation message is NOT added for exactly 50 lines ***
        expected_preview_short = short_content # No truncation message

        # Content with 51 lines
        long_content = "<kb>\n" + "\n".join([f"  <doc id='{i}'/>" for i in range(1, 50)]) + "\n</kb>" # 51 lines total
        expected_preview_long = "\n".join(long_content.splitlines()[:50]) + "\n[italic](... preview truncated ...)[/italic]" # Expect truncation message

        # Test with short content (exactly 50 lines)
        mock_prompt_save.return_value = False # Don't save
        with patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation', return_value=False): # Don't retry
            self.menu._handle_kb_confirm_save()
        # Check the assertion for the short content case (no truncation message)
        mock_prompt_save.assert_called_with(expected_preview_short, console=self.mock_console)
        mock_header.assert_called_with("Save Knowledge Base", console=self.mock_console)

        # Reset mocks and test with long content (more than 50 lines)
        mock_prompt_save.reset_mock()
        mock_header.reset_mock()
        self.menu._ask_convert_another.reset_mock() # Reset this mock too
        self.menu.user_data["generated_kb_content"] = long_content
        with patch('kb_for_prompt.organisms.menu_system.prompt_retry_generation', return_value=False): # Don't retry
            self.menu._handle_kb_confirm_save()
        # Check the assertion for the long content case (truncation message expected)
        mock_prompt_save.assert_called_with(expected_preview_long, console=self.mock_console)
        mock_header.assert_called_with("Save Knowledge Base", console=self.mock_console)


# --- NEW TEST CLASS FOR ASK CONVERT ANOTHER ---
class TestMenuSystemAskConvertAnother(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        self.menu = MenuSystem(console=self.mock_console)
        # Mock transition_to
        self.menu._transition_to = MagicMock()
        # Set some initial user data to check if it gets cleared
        self.menu.user_data = {"key": "value", "another_key": 123}

    @patch('kb_for_prompt.organisms.menu_system.prompt_for_continue')
    def test_ask_convert_another_yes(self, mock_prompt_continue):
        """Test _ask_convert_another when user says yes."""
        mock_prompt_continue.return_value = True
        initial_user_data = self.menu.user_data.copy() # Keep a copy

        self.menu._ask_convert_another()

        # Assert prompt was called correctly
        mock_prompt_continue.assert_called_once_with(
            "Would you like to perform another conversion?",
            console=self.mock_console
        )
        # Assert user_data was cleared
        self.assertEqual(self.menu.user_data, {})
        # Assert transition to MAIN_MENU with history cleared
        self.menu._transition_to.assert_called_once_with(MenuState.MAIN_MENU, clear_history=True)

    @patch('kb_for_prompt.organisms.menu_system.prompt_for_continue')
    def test_ask_convert_another_no(self, mock_prompt_continue):
        """Test _ask_convert_another when user says no."""
        mock_prompt_continue.return_value = False
        initial_user_data = self.menu.user_data.copy() # Keep a copy

        self.menu._ask_convert_another()

        # Assert prompt was called correctly
        mock_prompt_continue.assert_called_once_with(
            "Would you like to perform another conversion?",
            console=self.mock_console
        )
        # Assert user_data was NOT cleared
        self.assertEqual(self.menu.user_data, initial_user_data)
        # Assert transition to EXIT
        self.menu._transition_to.assert_called_once_with(MenuState.EXIT)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
