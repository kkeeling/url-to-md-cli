# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "rich",
#     "halo",
#     "requests",
#     "pandas",
#     "docling",
#     "pytest",
# ]
# ///

# Run pytest if executed directly
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))

"""
Tests for kb_for_prompt.molecules.url_converter module.
"""

import os
import sys
import pytest
import requests
from unittest.mock import patch, MagicMock
from urllib.error import URLError

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kb_for_prompt.molecules.url_converter import convert_url_to_markdown
from kb_for_prompt.atoms.error_utils import ConversionError
from kb_for_prompt.atoms.error_utils import ValidationError


class TestUrlConverter:
    """Test cases for the URL converter module."""
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    def test_convert_url_to_markdown_success(self, mock_validate_url, mock_converter_cls):
        """Test successful URL to markdown conversion."""
        # Setup mocks
        mock_validate_url.return_value = True
        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "# Sample Markdown\n\nThis is a test."
        
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_result.status = "success"
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_cls.return_value = mock_converter
        
        # Call the function
        url = "https://example.com"
        content, returned_url = convert_url_to_markdown(url)
        
        # Assertions
        mock_validate_url.assert_called_once_with(url)
        mock_converter_cls.assert_called_once()
        mock_converter.convert.assert_called_once_with(url)
        assert content == "# Sample Markdown\n\nThis is a test."
        assert returned_url == url
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    def test_invalid_url(self, mock_validate_url, mock_converter_cls):
        """Test conversion with invalid URL."""
        # Set up mock to raise validation error
        mock_validate_url.side_effect = ValidationError(
            message="Invalid URL format",
            input_value="invalid-url",
            validation_type="url"
        )
        
        # Call the function and check for exception
        with pytest.raises(ValidationError) as exc_info:
            convert_url_to_markdown("invalid-url")
        
        # Assertions
        assert "Invalid URL format" in str(exc_info.value)
        mock_converter_cls.assert_not_called()
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    def test_empty_document_result(self, mock_validate_url, mock_converter_cls):
        """Test conversion when docling returns None for document."""
        # Setup mocks
        mock_validate_url.return_value = True
        
        mock_result = MagicMock()
        mock_result.document = None
        mock_result.status = "failure"
        mock_result.errors = ["Document parsing failed"]
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_cls.return_value = mock_converter
        
        # Call the function and check for exception
        with pytest.raises(ConversionError) as exc_info:
            convert_url_to_markdown("https://example.com")
        
        # Assertions
        assert "Failed to convert URL to document" in str(exc_info.value)
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    def test_empty_markdown_result(self, mock_validate_url, mock_converter_cls):
        """Test conversion when markdown result is empty."""
        # Setup mocks
        mock_validate_url.return_value = True
        
        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = ""
        
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_result.status = "success"
        
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_cls.return_value = mock_converter
        
        # Call the function and check for exception
        with pytest.raises(ConversionError) as exc_info:
            convert_url_to_markdown("https://example.com")
        
        # Assertions
        assert "Conversion produced empty markdown content" in str(exc_info.value)
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    @patch('kb_for_prompt.molecules.url_converter.time.sleep')
    def test_retry_mechanism_success(self, mock_sleep, mock_validate_url, mock_converter_cls):
        """Test retry mechanism with eventual success."""
        # Setup mocks
        mock_validate_url.return_value = True
        
        # Create a mock document for successful attempt
        mock_document = MagicMock()
        mock_document.export_to_markdown.return_value = "# Success after retry"
        
        # Create mock results
        mock_result_failure = MagicMock()
        mock_result_failure.document = None
        mock_result_failure.status = "failure"
        mock_result_failure.errors = ["Temporary network error"]
        
        mock_result_success = MagicMock()
        mock_result_success.document = mock_document
        mock_result_success.status = "success"
        
        # Configure converter mock to fail twice then succeed
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = [
            requests.RequestException("Connection timeout"),
            requests.RequestException("Temporary network error"),
            mock_result_success
        ]
        mock_converter_cls.return_value = mock_converter
        
        # Call the function
        content, url = convert_url_to_markdown("https://example.com", max_retries=3, retry_delay=0.1)
        
        # Assertions
        assert mock_converter.convert.call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep between retries
        assert content == "# Success after retry"
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    @patch('kb_for_prompt.molecules.url_converter.time.sleep')
    def test_retry_mechanism_max_retries_exhausted(self, mock_sleep, mock_validate_url, mock_converter_cls):
        """Test retry mechanism with all retries exhausted."""
        # Setup mocks
        mock_validate_url.return_value = True
        
        # Configure converter mock to always fail with network error
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = requests.RequestException("Connection timeout")
        mock_converter_cls.return_value = mock_converter
        
        # Call the function and check for exception
        with pytest.raises(ConversionError) as exc_info:
            convert_url_to_markdown("https://example.com", max_retries=2, retry_delay=0.1)
        
        # Assertions
        assert mock_converter.convert.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2  # Should sleep between retries
        assert "HTTP request failed" in str(exc_info.value)
        assert "retries" in exc_info.value.details
        assert exc_info.value.details["retries"] == 2
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.url_converter.validate_url')
    def test_unexpected_exception(self, mock_validate_url, mock_converter_cls):
        """Test handling of unexpected exceptions during conversion."""
        # Setup mocks
        mock_validate_url.return_value = True
        
        # Configure converter mock to raise unexpected exception
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = ValueError("Unexpected error")
        mock_converter_cls.return_value = mock_converter
        
        # Call the function and check for exception
        with pytest.raises(ConversionError) as exc_info:
            convert_url_to_markdown("https://example.com", max_retries=0)
        
        # Assertions
        assert "Unexpected conversion error" in str(exc_info.value)
        assert exc_info.value.details["error_type"] == "ValueError"