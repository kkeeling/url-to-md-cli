# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "rich",
#     "halo", 
#     "requests",
#     "pandas",
#     "docling",
#     "pytest",
#     "pytest-mock",
# ]
# ///

"""
Integration tests for the menu system with single item converter.

This module contains tests that verify the integration between
the MenuSystem and SingleItemConverter classes.
"""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from kb_for_prompt.organisms.menu_system import MenuSystem, MenuState


class TestMenuSystemIntegration:
    """Integration tests for MenuSystem with SingleItemConverter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = MagicMock(spec=Console)
        self.menu_system = MenuSystem(console=self.console)
    
    @patch('kb_for_prompt.organisms.single_item_converter.SingleItemConverter')
    def test_handle_processing_integration(self, mock_single_item_converter_class):
        """Test integration between menu system and single item converter during processing."""
        # Setup mock converter
        mock_converter = MagicMock()
        mock_single_item_converter_class.return_value = mock_converter
        
        # Mock successful conversion
        mock_converter.run.return_value = (
            True,
            {
                "input_path": "https://example.com",
                "input_type": "url",
                "output_path": "/output/dir/example_com.md",
                "error": None
            }
        )
        
        # Set user data in menu system
        self.menu_system.user_data = {
            "input_path": "https://example.com",
            "input_type": "url",
            "output_dir": "/output/dir"
        }
        
        # Set current state to PROCESSING
        self.menu_system.current_state = MenuState.PROCESSING
        
        # Call the processing handler
        self.menu_system._handle_processing()
        
        # Verify converter was used correctly
        mock_single_item_converter_class.assert_called_once_with(console=self.console)
        mock_converter.run.assert_called_once_with("https://example.com", "/output/dir")
        
        # Verify results are stored in user_data using the correct keys
        assert self.menu_system.user_data["single_conversion_success"] is True
        assert self.menu_system.user_data["single_conversion_results"]["input_path"] == "https://example.com"
        assert self.menu_system.user_data["single_conversion_results"]["input_type"] == "url"
        assert self.menu_system.user_data["single_conversion_results"]["output_path"] == "/output/dir/example_com.md"
        
        # Verify transition to RESULTS state
        assert self.menu_system.current_state == MenuState.RESULTS
    
    @patch('kb_for_prompt.organisms.single_item_converter.SingleItemConverter')
    def test_handle_processing_integration_failure(self, mock_single_item_converter_class):
        """Test integration when conversion fails."""
        # Setup mock converter
        mock_converter = MagicMock()
        mock_single_item_converter_class.return_value = mock_converter
        
        # Mock failed conversion
        mock_converter.run.return_value = (
            False,
            {
                "input_path": "/path/to/document.pdf",
                "input_type": "pdf",
                "output_path": None,
                "error": {
                    "type": "conversion",
                    "message": "Failed to convert PDF document"
                }
            }
        )
        
        # Set user data in menu system
        self.menu_system.user_data = {
            "input_path": "/path/to/document.pdf",
            "input_type": "pdf",
            "output_dir": "/output/dir"
        }
        
        # Set current state to PROCESSING
        self.menu_system.current_state = MenuState.PROCESSING
        
        # Call the processing handler
        self.menu_system._handle_processing()
        
        # Verify converter was used correctly
        mock_single_item_converter_class.assert_called_once_with(console=self.console)
        mock_converter.run.assert_called_once_with("/path/to/document.pdf", "/output/dir")
        
        # Verify results are stored in user_data using the correct keys
        assert self.menu_system.user_data["single_conversion_success"] is False
        assert self.menu_system.user_data["single_conversion_results"]["input_path"] == "/path/to/document.pdf"
        assert self.menu_system.user_data["single_conversion_results"]["input_type"] == "pdf"
        assert self.menu_system.user_data["single_conversion_results"]["error"]["message"] == "Failed to convert PDF document"
        
        # Verify transition to RESULTS state
        assert self.menu_system.current_state == MenuState.RESULTS
