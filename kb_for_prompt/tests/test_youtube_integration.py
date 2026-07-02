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
#     "youtube-transcript-api",
#     "litellm",
# ]
# ///

"""
Integration tests for YouTube transcript support.

This module contains integration tests that verify YouTube transcript
extraction and conversion works correctly with existing single item
and batch conversion workflows.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401
from rich.console import Console

from kb_for_prompt.atoms.error_utils import ConversionError  # noqa: F401
from kb_for_prompt.organisms.single_item_converter import SingleItemConverter
from kb_for_prompt.organisms.batch_converter import BatchConverter
from youtube_transcript_api import TranscriptsDisabled


class TestYouTubeIntegration:
    """Integration tests for YouTube functionality."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.console = MagicMock(spec=Console)
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock LLM client
        self.mock_llm_client = MagicMock()
        self.mock_llm_response = MagicMock()
        self.mock_llm_response.content = "# Converted YouTube Video\n\nThis is the converted content."
        self.mock_llm_client.invoke.return_value = self.mock_llm_response
    
    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('kb_for_prompt.organisms.single_item_converter.LiteLlmClient')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_single_youtube_conversion(self, mock_youtube_api, mock_llm_client_cls):
        """Test single YouTube URL conversion end-to-end."""
        # Setup mocks
        mock_llm_client_cls.return_value = self.mock_llm_client
        
        # Mock transcript API
        mock_transcript = MagicMock()
        mock_transcript.language_code = 'en'
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = [
            {'text': 'Welcome to our tutorial', 'start': 0.0, 'duration': 2.0},
            {'text': 'Today we will learn about testing', 'start': 2.0, 'duration': 3.0}
        ]
        
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([mock_transcript])
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list
        
        # Create converter and run
        converter = SingleItemConverter(console=self.console)
        youtube_url = "https://www.youtube.com/watch?v=test123"
        success, result = converter.run(youtube_url, self.temp_dir)
        
        # Verify results
        assert success is True
        assert result['input_type'] == 'url'
        assert result['output_path'] is not None
        
        # Check output file exists and contains expected content
        output_path = Path(result['output_path'])
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
        assert "# Converted YouTube Video" in content
        assert "This is the converted content" in content
        
        # Verify LLM was called with transcript
        mock_llm_client_cls.assert_called()
        self.mock_llm_client.invoke.assert_called_once()
        call_args = self.mock_llm_client.invoke.call_args[1]
        assert 'messages' in call_args
        user_message = call_args['messages'][1]['content']
        assert 'Welcome to our tutorial' in user_message
        assert 'Today we will learn about testing' in user_message
    
    @patch('kb_for_prompt.organisms.batch_converter.LiteLlmClient')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    def test_batch_youtube_mixed_content(self, mock_doc_converter_cls, mock_youtube_api, mock_llm_client_cls):
        """Test batch conversion with mixed inputs including YouTube URLs."""
        # Setup mocks
        mock_llm_client_cls.return_value = self.mock_llm_client
        
        # Mock regular URL converter
        mock_doc_converter = MagicMock()
        mock_doc = MagicMock()
        mock_doc.export_to_markdown.return_value = "# Regular Web Page\n\nContent from regular URL."
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_result.status = "success"
        mock_doc_converter.convert.return_value = mock_result
        mock_doc_converter_cls.return_value = mock_doc_converter
        
        # Mock YouTube transcript API
        mock_transcript = MagicMock()
        mock_transcript.language_code = 'en'
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = [
            {'text': 'YouTube content', 'start': 0.0, 'duration': 1.0}
        ]
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([mock_transcript])
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list
        
        # Create test CSV with mixed content
        csv_path = Path(self.temp_dir) / "test_mixed.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['input'])
            writer.writerow(['https://www.youtube.com/watch?v=video1'])
            writer.writerow(['https://example.com/page'])
            writer.writerow(['https://youtu.be/video2'])
        
        # Create batch converter and run
        converter = BatchConverter(console=self.console)
        success, result = converter.run(csv_path, self.temp_dir)
        
        # Verify results
        assert success is True
        assert result['total'] == 3
        assert len(result['successful']) == 3
        assert len(result['failed']) == 0
        
        # Check that files were created
        output_files = list(Path(self.temp_dir).glob('*.md'))
        assert len(output_files) >= 3  # At least 3 markdown files created
        
        # Verify YouTube videos were processed differently
        youtube_count = sum(1 for item in result['successful'] if 'youtube' in item.get('type', '').lower() or 'youtube' in item.get('original', '').lower())
        assert youtube_count >= 2  # Both YouTube URLs should be processed
    
    @patch('kb_for_prompt.organisms.single_item_converter.LiteLlmClient')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_youtube_error_handling_transcripts_disabled(self, mock_youtube_api, mock_llm_client_cls):
        """Test handling of YouTube videos with disabled transcripts."""
        # Setup mocks
        mock_llm_client_cls.return_value = self.mock_llm_client
        mock_youtube_api.list_transcripts.side_effect = TranscriptsDisabled("private_video")
        
        # Create converter and run
        converter = SingleItemConverter(console=self.console)
        youtube_url = "https://www.youtube.com/watch?v=private_video"
        success, result = converter.run(youtube_url, self.temp_dir)
        
        # Verify error handling
        assert success is False
        assert result['error'] is not None
        assert 'Transcripts are disabled' in result['error']['message']
    
    @patch('kb_for_prompt.organisms.single_item_converter.LiteLlmClient')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_youtube_error_handling_no_transcript(self, mock_youtube_api, mock_llm_client_cls):
        """Test handling of YouTube videos with no transcripts available."""
        # Setup mocks
        mock_llm_client_cls.return_value = self.mock_llm_client
        
        # Mock empty transcript list
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([])
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list
        
        # Create converter and run
        converter = SingleItemConverter(console=self.console)
        youtube_url = "https://www.youtube.com/watch?v=no_transcript"
        success, result = converter.run(youtube_url, self.temp_dir)
        
        # Verify error handling
        assert success is False
        assert result['error'] is not None
        assert 'No transcripts found' in result['error']['message']
    
    @patch('kb_for_prompt.organisms.batch_converter.LiteLlmClient')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_youtube_filename_conflicts(self, mock_youtube_api, mock_llm_client_cls):
        """Test filename conflict resolution for YouTube videos with similar titles."""
        # Setup mocks
        mock_llm_client_cls.return_value = self.mock_llm_client
        
        # Mock transcript API to return same title for different videos
        mock_transcript = MagicMock()
        mock_transcript.language_code = 'en'
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = [
            {'text': 'Content', 'start': 0.0, 'duration': 1.0}
        ]
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([mock_transcript])
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list
        
        # Create test CSV with multiple YouTube URLs
        csv_path = Path(self.temp_dir) / "test_youtube_batch.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['urls'])
            writer.writerow(['https://www.youtube.com/watch?v=video1'])
            writer.writerow(['https://www.youtube.com/watch?v=video2'])
            writer.writerow(['https://www.youtube.com/watch?v=video3'])
        
        # Create batch converter and run
        converter = BatchConverter(console=self.console)
        success, result = converter.run(csv_path, self.temp_dir)
        
        # Verify results
        assert success is True
        assert len(result['successful']) == 3
        
        # Check that all files have unique names
        output_files = list(Path(self.temp_dir).glob('*.md'))
        filenames = [f.name for f in output_files]
        assert len(filenames) == len(set(filenames))  # All filenames should be unique
    
    @patch('kb_for_prompt.molecules.url_converter.DocumentConverter')
    @patch('kb_for_prompt.molecules.pdf_converter.DocumentConverter')
    def test_existing_functionality_preserved(self, mock_pdf_converter_cls, mock_url_converter_cls):
        """Test that YouTube integration doesn't break existing converters."""
        # Mock regular URL converter
        mock_url_converter = MagicMock()
        mock_url_doc = MagicMock()
        mock_url_doc.export_to_markdown.return_value = "# Web Page\n\nRegular web content."
        mock_url_result = MagicMock()
        mock_url_result.document = mock_url_doc
        mock_url_result.status = "success"
        mock_url_converter.convert.return_value = mock_url_result
        mock_url_converter_cls.return_value = mock_url_converter
        
        # Mock PDF converter
        mock_pdf_converter = MagicMock()
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.export_to_markdown.return_value = "# PDF Document\n\nPDF content."
        mock_pdf_result = MagicMock()
        mock_pdf_result.document = mock_pdf_doc
        mock_pdf_result.status = "success"
        mock_pdf_converter.convert.return_value = mock_pdf_result
        mock_pdf_converter_cls.return_value = mock_pdf_converter
        
        # Test regular URL conversion
        converter = SingleItemConverter(console=self.console)
        
        # Test URL conversion
        with patch('kb_for_prompt.organisms.single_item_converter.LiteLlmClient'):
            success, result = converter.run("https://example.com", self.temp_dir)
            assert success is True
            assert result['input_type'] == 'url'
            output_path = Path(result['output_path'])
            assert output_path.exists()
            with open(output_path, 'r') as f:
                assert "Regular web content" in f.read()
        
        # Create a test PDF file
        test_pdf = Path(self.temp_dir) / "test.pdf"
        test_pdf.write_text("fake pdf content")  # Just create a file
        
        # Test PDF conversion
        with patch('kb_for_prompt.organisms.single_item_converter.LiteLlmClient'):
            with patch('kb_for_prompt.organisms.single_item_converter.validate_file_type', return_value='pdf'):
                success, result = converter.run(str(test_pdf), self.temp_dir)
                assert success is True
                assert result['input_type'] == 'pdf'