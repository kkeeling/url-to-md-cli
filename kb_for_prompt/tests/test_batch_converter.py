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
Tests for the batch conversion module.

This module contains tests for the batch conversion functionality,
ensuring proper CSV parsing, input validation, concurrent processing,
and error handling.
"""

import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd
import pytest
from rich.console import Console

from kb_for_prompt.organisms.batch_converter import BatchConverter
from kb_for_prompt.atoms.error_utils import ValidationError, FileIOError, ConversionError


class TestBatchConverter:
    """Tests for the BatchConverter class."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.console = MagicMock(spec=Console)
        self.batch_converter = BatchConverter(console=self.console)
    
    @patch('kb_for_prompt.organisms.batch_converter.validate_file_path')
    @patch('builtins.open', new_callable=mock_open, read_data="url,files\nhttps://example.com,file1.pdf\nhttps://test.com,\n,file2.docx")
    @patch('kb_for_prompt.organisms.batch_converter.csv.reader')
    def test_read_inputs_from_csv_standard(self, mock_csv_reader, mock_open_file, mock_validate_path):
        """Test reading inputs from a CSV file using the standard csv module."""
        # Mock CSV data as returned by csv.reader
        mock_csv_data = [
            ['url', 'files'],
            ['https://example.com', 'file1.pdf'],
            ['https://test.com', ''],
            ['', 'file2.docx']
        ]
        mock_csv_reader.return_value = iter(mock_csv_data)
        
        # Mock path validation
        mock_validate_path.return_value = Path('/path/to/test.csv')
        
        # Call the method under test
        with patch('kb_for_prompt.organisms.batch_converter.display_spinner') as mock_spinner:
            mock_spinner.return_value.__enter__.return_value = MagicMock()
            result = self.batch_converter.read_inputs_from_csv('test.csv')
        
        # Check the results - expecting unique, non-empty values from all cells
        assert len(result) == 6 # url, files, https://example.com, file1.pdf, https://test.com, file2.docx
        assert 'https://example.com' in result
        assert 'https://test.com' in result
        assert 'file1.pdf' in result
        assert 'file2.docx' in result
        assert 'url' in result # Header values are also included
        assert 'files' in result # Header values are also included

        # Verify mocks
        mock_validate_path.assert_called_once_with('test.csv')
        mock_open_file.assert_called_once_with(Path('/path/to/test.csv'), 'r', newline='', encoding='utf-8')
        mock_csv_reader.assert_called_once()

    @patch('kb_for_prompt.organisms.batch_converter.validate_file_path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('kb_for_prompt.organisms.batch_converter.csv.reader')
    def test_read_inputs_from_csv_standard_reader_error(self, mock_csv_reader, mock_open_file, mock_validate_path):
        """Test handling of csv.Error during standard CSV reading."""
        # Mock path validation
        mock_validate_path.return_value = Path('/path/to/error.csv')

        # Mock csv.reader to raise an error
        mock_csv_reader.side_effect = csv.Error("Malformed CSV")

        # Call the method under test and expect FileIOError
        with patch('kb_for_prompt.organisms.batch_converter.display_spinner') as mock_spinner:
            mock_spinner.return_value.__enter__.return_value = MagicMock()
            with pytest.raises(FileIOError) as excinfo:
                self.batch_converter.read_inputs_from_csv('error.csv')

        # Check the exception details
        assert "Failed to parse CSV file with standard reader" in str(excinfo.value)
        assert "Malformed CSV" in str(excinfo.value)
        assert excinfo.value.file_path == '/path/to/error.csv'
        assert excinfo.value.operation == 'read'

        # Verify mocks
        mock_validate_path.assert_called_once_with('error.csv')
        mock_open_file.assert_called_once_with(Path('/path/to/error.csv'), 'r', newline='', encoding='utf-8')
        mock_csv_reader.assert_called_once()

    # Note: The test_read_inputs_from_csv_fallback is less relevant now as the primary
    # mechanism IS the standard CSV reader. We keep it but adjust its purpose slightly
    # to test the general file reading error handling if open itself fails.
    @patch('kb_for_prompt.organisms.batch_converter.validate_file_path')
    @patch('builtins.open')
    def test_read_inputs_from_csv_file_open_error(self, mock_open_file, mock_validate_path):
        """Test handling errors during file opening."""
        # Mock path validation
        mock_validate_path.return_value = Path('/path/to/unreadable.csv')

        # Mock open to raise an IOError
        mock_open_file.side_effect = IOError("Permission denied")

        # Call the method under test and expect FileIOError
        with patch('kb_for_prompt.organisms.batch_converter.display_spinner') as mock_spinner:
            mock_spinner.return_value.__enter__.return_value = MagicMock()
            with pytest.raises(FileIOError) as excinfo:
                self.batch_converter.read_inputs_from_csv('unreadable.csv')

        # Check the exception details
        assert "Failed to read CSV file" in str(excinfo.value)
        assert "Permission denied" in str(excinfo.value)
        assert excinfo.value.file_path == '/path/to/unreadable.csv'
        assert excinfo.value.operation == 'read'

        # Verify mocks
        mock_validate_path.assert_called_once_with('unreadable.csv')
        mock_open_file.assert_called_once_with(Path('/path/to/unreadable.csv'), 'r', newline='', encoding='utf-8')

    def test_validate_and_classify_inputs(self):
        """Test validation and classification of inputs."""
        inputs = [
            'https://example.com',       # Valid URL
            'invalid-url',               # Invalid URL
            '/path/to/nonexistent.pdf',  # Invalid file (nonexistent)
            '/path/to/document.docx'     # Valid document
        ]
        
        # Mock validate_input_item to return expected values
        with patch('kb_for_prompt.organisms.batch_converter.validate_input_item') as mock_validate:
            mock_validate.side_effect = [
                ('url', 'https://example.com'),  # Valid URL
                ValidationError(message="Invalid URL", input_value="invalid-url", validation_type="url"),  # Invalid URL
                ValidationError(message="File not found", input_value="/path/to/nonexistent.pdf", validation_type="file_existence"),  # Invalid file
                ('file', '/path/to/document.docx')  # Valid document
            ]
            
            # Mock detect_file_type for valid files
            with patch('kb_for_prompt.organisms.batch_converter.detect_file_type') as mock_detect:
                mock_detect.return_value = 'docx'  # Return docx for the valid document
                
                # Call the method under test
                with patch('kb_for_prompt.organisms.batch_converter.display_spinner') as mock_spinner:
                    mock_spinner.return_value.__enter__.return_value = MagicMock()
                    valid, invalid = self.batch_converter.validate_and_classify_inputs(inputs)
        
        # Check the valid inputs
        assert len(valid) == 2
        assert valid[0]['type'] == 'url'
        assert valid[0]['original'] == 'https://example.com'
        assert valid[1]['type'] == 'docx'
        assert valid[1]['original'] == '/path/to/document.docx'
        
        # Check the invalid inputs
        assert len(invalid) == 2
        assert invalid[0]['original'] == 'invalid-url'
        assert invalid[1]['original'] == '/path/to/nonexistent.pdf'
    
    @patch('kb_for_prompt.organisms.batch_converter.ensure_directory_exists')
    @patch('kb_for_prompt.organisms.batch_converter.display_conversion_summary')
    def test_run_empty_inputs(self, mock_summary, mock_ensure_dir):
        """Test running batch conversion with no valid inputs."""
        # Mock directory resolution
        mock_ensure_dir.return_value = Path('/output/dir')
        
        # Mock reading empty input list
        with patch.object(self.batch_converter, 'read_inputs_from_csv', return_value=[]):
            # Call the method under test
            success, result = self.batch_converter.run('input.csv', '/output/dir')
        
        # Check the results
        assert not success
        assert result['total'] == 0
        assert not result['successful']
        assert not result['failed']
    
    @patch('kb_for_prompt.organisms.batch_converter.ensure_directory_exists')
    @patch('kb_for_prompt.organisms.batch_converter.display_conversion_summary')
    def test_run_with_inputs(self, mock_summary, mock_ensure_dir):
        """Test running batch conversion with valid inputs."""
        # Mock directory resolution
        mock_ensure_dir.return_value = Path('/output/dir')
        
        # Mock reading inputs
        inputs = ['https://example.com', '/path/to/document.pdf']
        
        # Mock batch processing results
        successful = [{'file': '/output/dir/example_com.md', 'original': 'https://example.com', 'type': 'url'}]
        failed = [{'original': '/path/to/document.pdf', 'error': 'File not found', 'type': 'pdf'}]
        
        with patch.object(self.batch_converter, 'read_inputs_from_csv', return_value=inputs):
            with patch.object(self.batch_converter, '_process_batch', return_value=(successful, failed)):
                with patch.object(self.batch_converter, '_display_input_summary'):
                    # Call the method under test
                    success, result = self.batch_converter.run('input.csv', '/output/dir')
        
        # Check the results
        assert success
        assert result['total'] == 2
        assert len(result['successful']) == 1
        assert len(result['failed']) == 1
        assert result['successful'][0]['original'] == 'https://example.com'
        assert result['failed'][0]['original'] == '/path/to/document.pdf'
    
    @patch('kb_for_prompt.organisms.batch_converter.ThreadPoolExecutor')
    def test_process_batch(self, mock_executor_class):
        """Test processing a batch of inputs concurrently."""
        # Mock inputs
        inputs = ['https://example.com', '/path/to/document.pdf']
        
        # Mock validate_and_classify_inputs results
        valid_inputs = [
            {'original': 'https://example.com', 'validated': 'https://example.com', 'type': 'url'},
            {'original': '/path/to/document.pdf', 'validated': '/path/to/document.pdf', 'type': 'pdf'}
        ]
        invalid_inputs = []
        
        # Mock successful conversion results
        successful_result = {
            'success': True,
            'original': 'https://example.com',
            'type': 'url',
            'output_path': '/output/dir/example_com.md',
            'error': None
        }
        
        # Mock failed conversion results
        failed_result = {
            'success': False,
            'original': '/path/to/document.pdf',
            'type': 'pdf',
            'output_path': None,
            'error': {'type': 'conversion', 'message': 'Failed to convert PDF'}
        }
        
        # Mock ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures
        mock_future1 = MagicMock()
        mock_future1.result.return_value = successful_result
        
        mock_future2 = MagicMock()
        mock_future2.result.return_value = failed_result
        
        # Create a mapping from future to input_data for as_completed
        future_to_input_map = {
            mock_future1: valid_inputs[0],
            mock_future2: valid_inputs[1]
        }
        mock_executor.submit.side_effect = [mock_future1, mock_future2]

        # Mock concurrent.futures.as_completed to return futures and use the map
        with patch('kb_for_prompt.organisms.batch_converter.concurrent.futures.as_completed', return_value=[mock_future1, mock_future2]):
            with patch.object(self.batch_converter, 'validate_and_classify_inputs', return_value=(valid_inputs, invalid_inputs)):
                with patch('kb_for_prompt.organisms.batch_converter.display_progress_bar') as mock_progress_bar:
                    # Mock the progress bar context manager
                    mock_progress = MagicMock()
                    mock_progress.task_id = 'task1'
                    mock_progress_bar.return_value.__enter__.return_value = mock_progress

                    # Reconstruct the future_to_input dictionary inside the mocked context
                    # This is necessary because the original dict is created before as_completed is mocked
                    with patch.dict(self.batch_converter.__dict__, {'future_to_input': future_to_input_map}):
                        # Call the method under test
                        successful, failed = self.batch_converter._process_batch(inputs, Path('/output/dir'))

        # Check the results
        assert len(successful) == 1
        assert len(failed) == 1
        assert successful[0]['original'] == 'https://example.com'
        assert successful[0]['file'] == '/output/dir/example_com.md'
        assert failed[0]['original'] == '/path/to/document.pdf'
        assert failed[0]['error'] == 'Failed to convert PDF'
        assert failed[0]['type'] == 'pdf' # Ensure type is included in failed items

        # Verify that submit was called correctly
        assert mock_executor.submit.call_count == 2
        mock_executor.submit.assert_any_call(self.batch_converter._process_single_input, valid_inputs[0], Path('/output/dir'))
        mock_executor.submit.assert_any_call(self.batch_converter._process_single_input, valid_inputs[1], Path('/output/dir'))

    def test_process_single_input_url(self):
        """Test processing a single URL input."""
        # Input data
        input_data = {
            'original': 'https://example.com',
            'validated': 'https://example.com',
            'type': 'url'
        }
        
        # Mock URL conversion
        with patch('kb_for_prompt.organisms.batch_converter.convert_url_to_markdown') as mock_convert:
            mock_convert.return_value = ('# Example.com\n\nThis is a test markdown content.', 'https://example.com')
            
            # Mock file operations
            with patch('kb_for_prompt.organisms.batch_converter.generate_output_filename') as mock_generate:
                mock_generate.return_value = Path('/output/dir/example_com.md')
                
                with patch('builtins.open', mock_open()) as mock_file:
                    # Call the method under test
                    result = self.batch_converter._process_single_input(input_data, Path('/output/dir'))
        
        # Check the results
        assert result['success']
        assert result['original'] == 'https://example.com'
        assert result['type'] == 'url'
        assert result['output_path'] == '/output/dir/example_com.md'
        assert result['error'] is None
    
    def test_process_single_input_doc(self):
        """Test processing a single Word document input."""
        # Input data
        input_data = {
            'original': '/path/to/document.docx',
            'validated': '/path/to/document.docx',
            'type': 'docx'
        }
        
        # Mock DOC conversion
        with patch('kb_for_prompt.organisms.batch_converter.convert_doc_to_markdown') as mock_convert:
            mock_convert.return_value = ('# Document\n\nThis is a test markdown content.', '/path/to/document.docx')
            
            # Mock file operations
            with patch('kb_for_prompt.organisms.batch_converter.generate_output_filename') as mock_generate:
                mock_generate.return_value = Path('/output/dir/document.md')
                
                with patch('builtins.open', mock_open()) as mock_file:
                    # Call the method under test
                    result = self.batch_converter._process_single_input(input_data, Path('/output/dir'))
        
        # Check the results
        assert result['success']
        assert result['original'] == '/path/to/document.docx'
        assert result['type'] == 'docx'
        assert result['output_path'] == '/output/dir/document.md'
        assert result['error'] is None
    
    def test_process_single_input_pdf(self):
        """Test processing a single PDF input."""
        # Input data
        input_data = {
            'original': '/path/to/document.pdf',
            'validated': '/path/to/document.pdf',
            'type': 'pdf'
        }
        
        # Mock PDF conversion
        with patch('kb_for_prompt.organisms.batch_converter.convert_pdf_to_markdown') as mock_convert:
            mock_convert.return_value = ('# PDF Document\n\nThis is a test markdown content.', '/path/to/document.pdf')
            
            # Mock file operations
            with patch('kb_for_prompt.organisms.batch_converter.generate_output_filename') as mock_generate:
                mock_generate.return_value = Path('/output/dir/document.md')
                
                with patch('builtins.open', mock_open()) as mock_file:
                    # Call the method under test
                    result = self.batch_converter._process_single_input(input_data, Path('/output/dir'))
        
        # Check the results
        assert result['success']
        assert result['original'] == '/path/to/document.pdf'
        assert result['type'] == 'pdf'
        assert result['output_path'] == '/output/dir/document.md'
        assert result['error'] is None
    
    def test_process_single_input_error(self):
        """Test processing a single input that results in an error."""
        # Input data
        input_data = {
            'original': 'https://example.com',
            'validated': 'https://example.com',
            'type': 'url'
        }
        
        # Create a custom error for testing
        conversion_error = ConversionError(
            message="Failed to convert URL: test error",
            input_path='https://example.com',
            conversion_type='url'
        )
        
        # Mock generate_output_filename to avoid file system issues
        with patch('kb_for_prompt.organisms.batch_converter.generate_output_filename') as mock_generate:
            mock_generate.return_value = Path('/output/dir/example_com.md')
            
            # Mock URL conversion that raises an error
            with patch('kb_for_prompt.organisms.batch_converter.convert_url_to_markdown') as mock_convert:
                mock_convert.side_effect = conversion_error
                
                # Call the method under test
                result = self.batch_converter._process_single_input(input_data, Path('/output/dir'))
        
        # Check the results
        assert not result['success']
        assert result['original'] == 'https://example.com'
        assert result['type'] == 'url'
        assert result['output_path'] is None
        # Check if the error type is correctly identified
        assert result['error']['type'] == 'conversion' # Should now correctly identify ConversionError
        assert 'Failed to convert URL' in result['error']['message']
        assert 'test error' in result['error']['message']

    def test_display_input_summary(self):
        """Test displaying a summary of inputs."""
        inputs = [
            'https://example.com',
            'https://test.com',
            '/path/to/document.pdf',
            '/path/to/other.docx'
        ]
        
        # Mock is_url function
        with patch('kb_for_prompt.organisms.batch_converter.is_url') as mock_is_url:
            mock_is_url.side_effect = lambda x: x.startswith('http')
            
            # Mock display_processing_update
            with patch('kb_for_prompt.organisms.batch_converter.display_processing_update') as mock_display:
                # Call the method under test
                self.batch_converter._display_input_summary(inputs)
        
        # Check the results
        mock_display.assert_called_once()
        call_args, call_kwargs = mock_display.call_args
        assert "Loaded 4 inputs" in call_args[0]
        assert "2 URLs" in call_args[0]
        assert "2 files" in call_args[0]
        assert call_kwargs['status'] == 'info'
        assert call_kwargs['console'] == self.console
