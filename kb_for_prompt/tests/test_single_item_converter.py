# /// script
# requires-python = "==3.12"
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
Tests for the single item converter module.

This module contains tests for the SingleItemConverter class, which
handles the conversion of single URLs or files to Markdown format.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

import pytest
from rich.console import Console

from kb_for_prompt.atoms.error_utils import ValidationError, ConversionError, FileIOError
from kb_for_prompt.organisms.single_item_converter import SingleItemConverter


class TestSingleItemConverter:
    """Test suite for the SingleItemConverter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = MagicMock(spec=Console)
        self.converter = SingleItemConverter(console=self.console)
    
    @patch('kb_for_prompt.organisms.single_item_converter.validate_input_item')
    def test_detect_input_type_url(self, mock_validate_input_item):
        """Test detecting URL input type."""
        # Setup
        mock_validate_input_item.return_value = ("url", "https://example.com")
        
        # Execute
        input_type, validated_input = self.converter._detect_input_type("https://example.com")
        
        # Verify
        assert input_type == "url"
        assert validated_input == "https://example.com"
        mock_validate_input_item.assert_called_once_with("https://example.com")
    
    @patch('kb_for_prompt.organisms.single_item_converter.validate_input_item')
    @patch('kb_for_prompt.organisms.single_item_converter.validate_file_type')
    def test_detect_input_type_pdf(self, mock_validate_file_type, mock_validate_input_item):
        """Test detecting PDF file input type."""
        # Setup
        mock_validate_input_item.return_value = ("file", "/path/to/document.pdf")
        mock_validate_file_type.return_value = "pdf"
        
        # Execute
        input_type, validated_input = self.converter._detect_input_type("/path/to/document.pdf")
        
        # Verify
        assert input_type == "pdf"
        assert validated_input == "/path/to/document.pdf"
        mock_validate_input_item.assert_called_once_with("/path/to/document.pdf")
        mock_validate_file_type.assert_called_once_with(Path("/path/to/document.pdf"))
    
    @patch('kb_for_prompt.organisms.single_item_converter.ensure_directory_exists')
    def test_get_output_directory_provided(self, mock_ensure_directory_exists):
        """Test getting output directory when provided."""
        # Setup
        mock_ensure_directory_exists.return_value = Path("/output/dir")
        
        # Execute
        output_dir = self.converter._get_output_directory("/output/dir")
        
        # Verify
        assert output_dir == Path("/output/dir")
        mock_ensure_directory_exists.assert_called_once_with("/output/dir")
    
    @patch('kb_for_prompt.organisms.single_item_converter.prompt_for_output_directory')
    def test_get_output_directory_prompt(self, mock_prompt_for_output_directory):
        """Test prompting for output directory when not provided."""
        # Setup
        mock_prompt_for_output_directory.return_value = Path("/user/selected/dir")
        
        # Execute
        output_dir = self.converter._get_output_directory(None)
        
        # Verify
        assert output_dir == Path("/user/selected/dir")
        mock_prompt_for_output_directory.assert_called_once_with(console=self.console)
    
    def test_generate_default_filename_url(self):
        """Test generating default filename for URL input."""
        # Execute
        filename = self.converter._generate_default_filename("https://example.com/path/to/page", "url")
        
        # Verify
        assert filename == "example_com_path_to_page.md"
    
    def test_generate_default_filename_pdf(self):
        """Test generating default filename for PDF input."""
        # Execute
        filename = self.converter._generate_default_filename("/path/to/document.pdf", "pdf")
        
        # Verify
        assert filename == "document.md"
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_url_to_markdown')
    def test_convert_with_retry_url_success(self, mock_convert_url):
        """Test successful URL conversion with no retries needed."""
        # Setup
        mock_convert_url.return_value = ("# Markdown Content", "https://example.com")
        
        # Execute
        success, content, error = self.converter._convert_with_retry("https://example.com", "url")
        
        # Verify
        assert success is True
        assert content == "# Markdown Content"
        assert error is None
        mock_convert_url.assert_called_once_with("https://example.com")
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_pdf_to_markdown')
    def test_convert_with_retry_pdf_success(self, mock_convert_pdf):
        """Test successful PDF conversion with no retries needed."""
        # Setup
        mock_convert_pdf.return_value = ("# PDF Content", "/path/to/document.pdf")
        
        # Execute
        success, content, error = self.converter._convert_with_retry("/path/to/document.pdf", "pdf")
        
        # Verify
        assert success is True
        assert content == "# PDF Content"
        assert error is None
        mock_convert_pdf.assert_called_once_with("/path/to/document.pdf")
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_doc_to_markdown')
    def test_convert_with_retry_doc_success(self, mock_convert_doc):
        """Test successful DOC conversion with no retries needed."""
        # Setup
        mock_convert_doc.return_value = ("# DOC Content", "/path/to/document.doc")
        
        # Execute
        success, content, error = self.converter._convert_with_retry("/path/to/document.doc", "doc")
        
        # Verify
        assert success is True
        assert content == "# DOC Content"
        assert error is None
        mock_convert_doc.assert_called_once_with("/path/to/document.doc")
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_url_to_markdown')
    @patch('kb_for_prompt.organisms.single_item_converter.prompt_for_retry')
    def test_convert_with_retry_failure_no_retry(self, mock_prompt_for_retry, mock_convert_url):
        """Test conversion failure with user choosing not to retry."""
        # Setup
        mock_convert_url.side_effect = ConversionError(
            message="Conversion failed",
            input_path="https://example.com",
            conversion_type="url"
        )
        mock_prompt_for_retry.return_value = False  # User chooses not to retry
        
        # Execute
        success, content, error = self.converter._convert_with_retry("https://example.com", "url")
        
        # Verify
        assert success is False
        assert content is None
        assert error is not None
        assert error["message"] == "Conversion failed"
        assert error["retries"] == 1
        assert error["input_type"] == "url"
        mock_convert_url.assert_called_once()
        mock_prompt_for_retry.assert_called_once()
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_url_to_markdown')
    @patch('kb_for_prompt.organisms.single_item_converter.prompt_for_retry')
    def test_convert_with_retry_success_after_retry(self, mock_prompt_for_retry, mock_convert_url):
        """Test conversion succeeding after a retry."""
        # Setup - First call fails, second call succeeds
        mock_convert_url.side_effect = [
            ConversionError(
                message="Temporary failure",
                input_path="https://example.com",
                conversion_type="url"
            ),
            ("# Retry Content", "https://example.com")
        ]
        mock_prompt_for_retry.return_value = True  # User chooses to retry
        
        # Execute
        success, content, error = self.converter._convert_with_retry("https://example.com", "url")
        
        # Verify
        assert success is True
        assert content == "# Retry Content"
        assert error is None
        assert mock_convert_url.call_count == 2
        mock_prompt_for_retry.assert_called_once()
    
    @patch('kb_for_prompt.organisms.single_item_converter.convert_url_to_markdown')
    @patch('kb_for_prompt.organisms.single_item_converter.prompt_for_retry')
    def test_convert_with_retry_max_retries_exhausted(self, mock_prompt_for_retry, mock_convert_url):
        """Test conversion failing after max retries are exhausted."""
        # Setup - All calls fail
        error = ConversionError(
            message="Persistent failure",
            input_path="https://example.com",
            conversion_type="url"
        )
        mock_convert_url.side_effect = [error, error, error, error]  # 3 retries + original attempt
        mock_prompt_for_retry.return_value = True  # User always chooses to retry
        
        # Set max_retries to 3
        self.converter.max_retries = 3
        
        # Execute
        success, content, error_details = self.converter._convert_with_retry("https://example.com", "url")
        
        # Verify
        assert success is False
        assert content is None
        assert error_details is not None
        assert error_details["message"] == "Persistent failure"
        assert error_details["retries"] == 4  # Original attempt + 3 retries
        assert mock_convert_url.call_count == 4  # Original + 3 retries
        assert mock_prompt_for_retry.call_count == 3  # 3 retry prompts
    
    def test_write_output_file_success(self):
        """Test successfully writing output file."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.md"
            
            # Execute
            self.converter._write_output_file("# Test Content", output_path)
            
            # Verify
            assert output_path.exists()
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == "# Test Content"
    
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_write_output_file_failure(self, mock_mkdir, mock_open):
        """Test failure when writing output file."""
        # Setup
        mock_open.side_effect = IOError("Disk full")
        
        # Execute and verify
        with pytest.raises(FileIOError) as exc_info:
            self.converter._write_output_file("# Test Content", Path("/path/to/output.md"))
        
        assert "Failed to write output file" in str(exc_info.value)
        assert "Disk full" in str(exc_info.value)
    
    @patch.object(SingleItemConverter, '_detect_input_type')
    @patch.object(SingleItemConverter, '_get_output_directory')
    @patch.object(SingleItemConverter, '_generate_default_filename')
    @patch.object(SingleItemConverter, '_convert_with_retry')
    @patch.object(SingleItemConverter, '_write_output_file')
    def test_run_success(self, mock_write, mock_convert, mock_generate, mock_get_dir, mock_detect):
        """Test successful run of the complete workflow."""
        # Setup
        mock_detect.return_value = ("url", "https://example.com")
        mock_get_dir.return_value = Path("/output/dir")
        mock_generate.return_value = "example_com.md"
        mock_convert.return_value = (True, "# Content", None)
        
        # Execute
        success, result_data = self.converter.run("https://example.com", "/output/dir")
        
        # Verify
        assert success is True
        assert result_data["input_path"] == "https://example.com"
        assert result_data["input_type"] == "url"
        assert result_data["output_path"] == str(Path("/output/dir/example_com.md"))
        assert result_data["error"] is None
        
        mock_detect.assert_called_once_with("https://example.com")
        mock_get_dir.assert_called_once_with("/output/dir")
        mock_generate.assert_called_once_with("https://example.com", "url")
        mock_convert.assert_called_once_with("https://example.com", "url")
        mock_write.assert_called_once_with("# Content", Path("/output/dir/example_com.md"))
    
    @patch.object(SingleItemConverter, '_detect_input_type')
    @patch.object(SingleItemConverter, '_get_output_directory')
    @patch.object(SingleItemConverter, '_generate_default_filename')
    @patch.object(SingleItemConverter, '_convert_with_retry')
    def test_run_conversion_failure(self, mock_convert, mock_generate, mock_get_dir, mock_detect):
        """Test handling conversion failure."""
        # Setup
        mock_detect.return_value = ("pdf", "/path/to/doc.pdf")
        mock_get_dir.return_value = Path("/output/dir")
        mock_generate.return_value = "doc.md"
        mock_convert.return_value = (False, None, {"message": "Conversion failed"})
        
        # Execute
        success, result_data = self.converter.run("/path/to/doc.pdf")
        
        # Verify
        assert success is False
        assert result_data["input_path"] == "/path/to/doc.pdf"
        assert result_data["input_type"] == "pdf"
        assert result_data["output_path"] is None
        assert result_data["error"] == {"message": "Conversion failed"}
    
    @patch.object(SingleItemConverter, '_detect_input_type')
    def test_run_validation_error(self, mock_detect):
        """Test handling validation error."""
        # Setup
        mock_detect.side_effect = ValidationError(
            message="Invalid URL",
            input_value="not-a-url",
            validation_type="url"
        )
        
        # Execute
        success, result_data = self.converter.run("not-a-url")
        
        # Verify
        assert success is False
        assert result_data["input_path"] == "not-a-url"
        assert result_data["input_type"] is None
        assert result_data["output_path"] is None
        assert result_data["error"]["type"] == "validation"
        assert result_data["error"]["message"] == "Invalid URL"