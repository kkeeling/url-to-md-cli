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
# ]
# ///

"""Unit tests for the Word document converter module."""

import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add project root to Python path to ensure imports work properly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kb_for_prompt.molecules.doc_converter import convert_doc_to_markdown
from kb_for_prompt.atoms.error_utils import ConversionError, ValidationError


class TestDocConverter:
    """Tests for the Word document converter module."""

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    def test_convert_doc_to_markdown_success(
            self, 
            mock_document_converter, 
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test successful conversion of a Word document to markdown."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.docx')
        mock_validate_file_type.return_value = 'docx'
        mock_create_file_url.return_value = 'file:///path/to/document.docx'
        
        # Mock docling DocumentConverter
        mock_result = Mock()
        mock_result.document = Mock()
        mock_result.document.export_to_markdown.return_value = '# Converted Markdown'
        mock_result.status = 'SUCCESS'
        
        mock_converter = Mock()
        mock_converter.convert.return_value = mock_result
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function
        markdown_content, original_path = convert_doc_to_markdown('/path/to/document.docx')
        
        # Assertions
        assert markdown_content == '# Converted Markdown'
        assert original_path == '/path/to/document.docx'
        mock_validate_file_path.assert_called_once_with('/path/to/document.docx')
        mock_validate_file_type.assert_called_once_with(
            Path('/path/to/document.docx'), allowed_types=["doc", "docx"]
        )
        mock_create_file_url.assert_called_once_with(Path('/path/to/document.docx'))
        mock_converter.convert.assert_called_once_with('file:///path/to/document.docx')

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    def test_convert_doc_to_markdown_validation_error(self, mock_validate_file_path):
        """Test validation error handling."""
        # Mock file path validation to raise ValidationError
        mock_validate_file_path.side_effect = ValidationError(
            'File does not exist', '/path/to/nonexistent.docx', 'file_existence'
        )
        
        # Call the function and expect ValidationError
        with pytest.raises(ValidationError) as excinfo:
            convert_doc_to_markdown('/path/to/nonexistent.docx')
        
        # Assertions
        assert 'File does not exist' in str(excinfo.value)
        mock_validate_file_path.assert_called_once_with('/path/to/nonexistent.docx')

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    def test_convert_doc_to_markdown_empty_result(
            self, 
            mock_document_converter, 
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test handling of empty conversion results."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.doc')
        mock_validate_file_type.return_value = 'doc'
        mock_create_file_url.return_value = 'file:///path/to/document.doc'
        
        # Mock docling DocumentConverter with empty result
        mock_result = Mock()
        mock_result.document = Mock()
        mock_result.document.export_to_markdown.return_value = ''
        mock_result.status = 'SUCCESS'
        
        mock_converter = Mock()
        mock_converter.convert.return_value = mock_result
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function and expect ConversionError
        with pytest.raises(ConversionError) as excinfo:
            convert_doc_to_markdown('/path/to/document.doc')
        
        # Assertions
        assert 'Conversion produced empty markdown content' in str(excinfo.value)

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    def test_convert_doc_to_markdown_no_document(
            self, 
            mock_document_converter, 
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test handling of conversion with no document result."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.docx')
        mock_validate_file_type.return_value = 'docx'
        mock_create_file_url.return_value = 'file:///path/to/document.docx'
        
        # Mock docling DocumentConverter with no document
        mock_result = Mock()
        mock_result.document = None
        mock_result.status = 'FAILURE'
        mock_result.errors = ['Conversion failed']
        
        mock_converter = Mock()
        mock_converter.convert.return_value = mock_result
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function and expect ConversionError
        with pytest.raises(ConversionError) as excinfo:
            convert_doc_to_markdown('/path/to/document.docx')
        
        # Assertions
        assert 'Failed to convert docx document' in str(excinfo.value)

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    @patch('time.sleep')
    def test_convert_doc_to_markdown_with_retry(
            self, 
            mock_sleep,
            mock_document_converter,
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test retry mechanism for conversion failures."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.docx')
        mock_validate_file_type.return_value = 'docx'
        mock_create_file_url.return_value = 'file:///path/to/document.docx'
        
        # Mock success result for second attempt
        mock_success_result = Mock()
        mock_success_result.document = Mock()
        mock_success_result.document.export_to_markdown.return_value = '# Converted Markdown'
        mock_success_result.status = 'SUCCESS'
        
        mock_converter = Mock()
        # First call fails, second succeeds
        mock_converter.convert.side_effect = [
            Exception("Temporary failure"),
            mock_success_result
        ]
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function
        markdown_content, original_path = convert_doc_to_markdown('/path/to/document.docx', max_retries=3, retry_delay=0.1)
        
        # Assertions
        assert markdown_content == '# Converted Markdown'
        assert original_path == '/path/to/document.docx'
        assert mock_converter.convert.call_count == 2  # Should be called twice (one failure, one success)
        mock_sleep.assert_called_once()
        
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    @patch('time.sleep')
    def test_convert_doc_to_markdown_max_retries_exceeded(
            self,
            mock_sleep,
            mock_document_converter,
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test handling when max retries are exceeded."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.docx')
        mock_validate_file_type.return_value = 'docx'
        mock_create_file_url.return_value = 'file:///path/to/document.docx'
        
        # Mock converter with repeated failures
        mock_converter = Mock()
        mock_converter.convert.side_effect = [
            Exception("Failure 1"),
            Exception("Failure 2"),
            Exception("Failure 3"),
            Exception("Failure 4")  # This one shouldn't be reached as max_retries is 3
        ]
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function and expect ConversionError
        with pytest.raises(ConversionError) as excinfo:
            convert_doc_to_markdown('/path/to/document.docx', max_retries=3, retry_delay=0.1)
        
        # Assertions
        assert 'Unexpected conversion error' in str(excinfo.value)
        assert mock_converter.convert.call_count == 4  # Initial try + 3 retries
        # Check that retries count is in the error details
        assert excinfo.value.details.get('retries') == 3

    @patch('kb_for_prompt.molecules.doc_converter.validate_file_path')
    @patch('kb_for_prompt.molecules.doc_converter.validate_file_type')
    @patch('kb_for_prompt.molecules.doc_converter.create_file_url')
    @patch('kb_for_prompt.molecules.doc_converter.DocumentConverter')
    def test_convert_doc_to_markdown_file_access_error(
            self,
            mock_document_converter,
            mock_create_file_url, 
            mock_validate_file_type, 
            mock_validate_file_path
        ):
        """Test handling of file access errors."""
        # Set up the mocks
        mock_validate_file_path.return_value = Path('/path/to/document.docx')
        mock_validate_file_type.return_value = 'docx'
        mock_create_file_url.return_value = 'file:///path/to/document.docx'
        
        # Mock converter with file access error
        mock_converter = Mock()
        mock_converter.convert.side_effect = IOError("Permission denied")
        
        mock_document_converter.return_value = mock_converter
        
        # Call the function and expect ConversionError
        with pytest.raises(ConversionError) as excinfo:
            convert_doc_to_markdown('/path/to/document.docx', max_retries=0)
        
        # Assertions
        assert 'File access error' in str(excinfo.value)
        assert 'Permission denied' in str(excinfo.value.details.get('os_error', ''))