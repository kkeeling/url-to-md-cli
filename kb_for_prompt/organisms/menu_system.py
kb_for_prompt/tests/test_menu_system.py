import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Assume menu_system.py is in the same directory or accessible via PYTHONPATH
from menu_system import MenuSystem, MenuState 
# Assuming prompts.py is accessible
from templates import prompts

class TestMenuSystemTocConfirmSave(unittest.TestCase):

    def setUp(self):
        """Set up a MenuSystem instance before each test."""
        self.mock_console = MagicMock()
        self.menu = MenuSystem(console=self.mock_console)
        # Set initial state for testing the handler
        self.menu.current_state = MenuState.TOC_CONFIRM_SAVE
        # Provide necessary user_data
        self.output_dir = Path("./test_output_dir")
        self.toc_content = "Line 1\nLine 2\n" + "\n".join([f"Line {i}" for i in range(3, 60)])
        self.menu.user_data = {
            "output_dir": self.output_dir,
            "toc_content": self.toc_content
        }
        # Mock the save method directly on the instance
        self.menu._save_content_to_file = MagicMock(return_value=True)

    def test_handle_toc_confirm_save_content_none(self):
        """Test handler when toc_content is missing."""
        self.menu.user_data["toc_content"] = None
        
        self.menu._handle_toc_confirm_save()

        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] TOC content not found in user data. Cannot proceed with saving.")
        self.assertEqual(self.menu.next_state, MenuState.KB_PROMPT)

    def test_handle_toc_confirm_save_output_dir_none(self):
        """Test handler when output_dir is missing."""
        self.menu.user_data["output_dir"] = None
        
        self.menu._handle_toc_confirm_save()

        self.mock_console.print.assert_any_call("[bold red]Error:[/bold red] Output directory not found in user data. Cannot determine save location.")
        self.assertEqual(self.menu.next_state, MenuState.KB_PROMPT)

    @patch('menu_system.prompts.prompt_save_confirmation')
    def test_handle_toc_confirm_save_user_confirms_save_success(self, mock_prompt_save):
        """Test handler when user confirms save and save succeeds."""
        mock_prompt_save.return_value = True
        expected_preview = "\n".join(self.toc_content.splitlines()[:50]) + "\n[italic](... preview truncated ...)[/italic]"
        expected_target_path = self.output_dir / "toc.md"

        self.menu._handle_toc_confirm_save()

        # Check preview generation and prompt call
        mock_prompt_save.assert_called_once_with(expected_preview, console=self.mock_console)
        
        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(self.toc_content, expected_target_path)
        self.mock_console.print.assert_any_call(f"Attempting to save TOC to: {expected_target_path}")
        self.mock_console.print.assert_any_call("[green]TOC saved successfully.[/green]") # Assumes save mock returns True

        # Check state transition
        self.assertEqual(self.menu.next_state, MenuState.KB_PROMPT)

    @patch('menu_system.prompts.prompt_save_confirmation')
    def test_handle_toc_confirm_save_user_confirms_save_failure(self, mock_prompt_save):
        """Test handler when user confirms save but save fails."""
        mock_prompt_save.return_value = True
        self.menu._save_content_to_file.return_value = False # Simulate save failure
        expected_target_path = self.output_dir / "toc.md"

        self.menu._handle_toc_confirm_save()

        # Check save call
        self.menu._save_content_to_file.assert_called_once_with(self.toc_content, expected_target_path)
        self.mock_console.print.assert_any_call("[yellow]TOC saving failed. Check error messages above.[/yellow]")

        # Check state transition (should still go to KB_PROMPT)
        self.assertEqual(self.menu.next_state, MenuState.KB_PROMPT)

    @patch('menu_system.prompts.prompt_retry_generation')
    @patch('menu_system.prompts.prompt_save_confirmation')
    def test_handle_toc_confirm_save_user_denies_save_retries(self, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = True # User wants to retry

        self.menu._handle_toc_confirm_save()

        # Check prompts
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("TOC generation", console=self.mock_console)
        
        # Check no save call
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Retrying TOC generation...")


        # Check state transition
        self.assertEqual(self.menu.next_state, MenuState.TOC_PROCESSING)

    @patch('menu_system.prompts.prompt_retry_generation')
    @patch('menu_system.prompts.prompt_save_confirmation')
    def test_handle_toc_confirm_save_user_denies_save_no_retry(self, mock_prompt_save, mock_prompt_retry):
        """Test handler when user denies save and chooses not to retry."""
        mock_prompt_save.return_value = False # User denies save
        mock_prompt_retry.return_value = False # User does not want to retry

        self.menu._handle_toc_confirm_save()

        # Check prompts
        mock_prompt_save.assert_called_once()
        mock_prompt_retry.assert_called_once_with("TOC generation", console=self.mock_console)

        # Check no save call
        self.menu._save_content_to_file.assert_not_called()
        self.mock_console.print.assert_any_call("Save cancelled by user.")
        self.mock_console.print.assert_any_call("Skipping TOC generation retry.")

        # Check state transition
        self.assertEqual(self.menu.next_state, MenuState.KB_PROMPT)

    def test_preview_truncation(self):
        """Test that preview is correctly generated and truncated."""
        # Content with exactly 50 lines
        short_content = "\n".join([f"Line {i}" for i in range(1, 51)])
        self.menu.user_data["toc_content"] = short_content
        expected_preview_short = short_content

        # Content with 51 lines
        long_content = "\n".join([f"Line {i}" for i in range(1, 52)])
        self.menu.user_data["toc_content"] = long_content
        expected_preview_long = "\n".join([f"Line {i}" for i in range(1, 51)]) + "\n[italic](... preview truncated ...)[/italic]"

        with patch('menu_system.prompts.prompt_save_confirmation') as mock_prompt_save:
            # Test with short content
            self.menu.user_data["toc_content"] = short_content
            self.menu._handle_toc_confirm_save()
            mock_prompt_save.assert_called_with(expected_preview_short, console=self.mock_console)

            # Reset mock and test with long content
            mock_prompt_save.reset_mock()
            self.menu.user_data["toc_content"] = long_content
            self.menu._handle_toc_confirm_save()
            mock_prompt_save.assert_called_with(expected_preview_long, console=self.mock_console)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
