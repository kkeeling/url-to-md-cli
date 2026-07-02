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
#     "youtube-transcript-api",
#     "litellm",
# ]
# ///

# Run pytest if executed directly
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))

"""
Tests for kb_for_prompt.molecules.youtube_converter module.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kb_for_prompt.molecules.youtube_converter import YouTubeConverter, convert_youtube_to_markdown
from kb_for_prompt.atoms.type_detector import is_youtube_url
from kb_for_prompt.atoms.error_utils import ConversionError
from youtube_transcript_api import (
    TranscriptsDisabled
)


class TestYouTubeConverter:
    """Test cases for the YouTube converter module."""
    
    def test_youtube_url_detection(self):
        """Test YouTube URL detection with various URL formats."""
        test_cases = [
            # (url, expected_is_youtube, expected_video_id)
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://www.youtube.com/v/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf", True, "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s", True, "dQw4w9WgXcQ"),
            # Non-YouTube URLs
            ("https://vimeo.com/123456789", False, None),
            ("https://example.com/video", False, None),
            ("https://www.google.com", False, None),
            ("not a url", False, None),
            ("", False, None),
        ]
        
        for url, expected_is_youtube, expected_video_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_video_id, f"Wrong video ID for URL: {url}"
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_transcript_extraction_manual_preferred(self, mock_api):
        """Test transcript extraction with preference for manual transcripts."""
        # Create mock transcript objects
        manual_transcript = MagicMock()
        manual_transcript.language_code = 'en'
        manual_transcript.is_generated = False
        manual_transcript.fetch.return_value = [
            {'text': 'Hello', 'start': 0.0, 'duration': 1.0},
            {'text': 'World', 'start': 1.0, 'duration': 1.0}
        ]
        
        auto_transcript = MagicMock()
        auto_transcript.language_code = 'en'
        auto_transcript.is_generated = True
        auto_transcript.fetch.return_value = [
            {'text': 'Auto Hello', 'start': 0.0, 'duration': 1.0}
        ]
        
        # Create mock transcript list
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([manual_transcript, auto_transcript])
        
        # Configure the API mock
        mock_api.list_transcripts.return_value = mock_transcript_list
        
        # Create converter and test
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        transcript_text = converter.get_transcript("test_video_id")
        
        # Assertions
        assert transcript_text == "Hello World"
        manual_transcript.fetch.assert_called_once()
        auto_transcript.fetch.assert_not_called()
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_transcript_extraction_fallback_to_auto(self, mock_api):
        """Test fallback to auto-generated transcripts when no manual available."""
        # Create only auto-generated transcript
        auto_transcript = MagicMock()
        auto_transcript.language_code = 'en'
        auto_transcript.is_generated = True
        auto_transcript.fetch.return_value = [
            {'text': 'Auto generated', 'start': 0.0, 'duration': 1.0},
            {'text': 'transcript', 'start': 1.0, 'duration': 1.0}
        ]
        
        # Create mock transcript list
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([auto_transcript])
        
        # Configure the API mock
        mock_api.list_transcripts.return_value = mock_transcript_list
        
        # Create converter and test
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        transcript_text = converter.get_transcript("test_video_id")
        
        # Assertions
        assert transcript_text == "Auto generated transcript"
        auto_transcript.fetch.assert_called_once()
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_transcript_disabled_error(self, mock_api):
        """Test handling of TranscriptsDisabled error."""
        # Configure API to raise TranscriptsDisabled
        mock_api.list_transcripts.side_effect = TranscriptsDisabled("test_video_id")
        
        # Create converter and test
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        
        with pytest.raises(ConversionError) as exc_info:
            converter.get_transcript("test_video_id")
        
        # Assertions
        assert "Transcripts are disabled for this video" in str(exc_info.value)
        assert exc_info.value.details["video_id"] == "test_video_id"
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_no_transcript_found_error(self, mock_api):
        """Test handling of NoTranscriptFound error."""
        # Configure API to return empty transcript list
        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__.return_value = iter([])
        mock_api.list_transcripts.return_value = mock_transcript_list
        
        # Create converter and test
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        
        with pytest.raises(ConversionError) as exc_info:
            converter.get_transcript("test_video_id")
        
        # Assertions
        assert "No transcripts found for video" in str(exc_info.value)
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_api_error_handling(self, mock_api):
        """Test handling of general API errors."""
        # Configure API to raise generic exception
        mock_api.list_transcripts.side_effect = Exception("Network error")
        
        # Create converter and test
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        
        with pytest.raises(ConversionError) as exc_info:
            converter.get_transcript("test_video_id")
        
        # Assertions
        assert "Failed to fetch YouTube transcript" in str(exc_info.value)
        assert "Network error" in str(exc_info.value.details["original_error"])
    
    def test_filename_sanitization(self):
        """Test filename sanitization with various title formats."""
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        
        test_cases = [
            # (title, expected_filename)
            ("Normal Title", "youtube_Normal_Title.md"),
            ("Title with / slashes \\ and | pipes", "youtube_Title_with___slashes___and___pipes.md"),
            ("Title: With Colon", "youtube_Title__With_Colon.md"),
            ("Title? With! Special# Characters$", "youtube_Title__With__Special__Characters_.md"),
            ("   Spaces   Around   ", "youtube_Spaces_Around.md"),
            ("A" * 150, f"youtube_{'A' * 91}.md"),  # Test length limiting (100 - len("youtube_") - len(".md"))
            ("", "youtube_untitled.md"),
            ("   ", "youtube_untitled.md"),
        ]
        
        for title, expected in test_cases:
            result = converter.sanitize_filename(title)
            assert result == expected, f"Failed for title: '{title}'"
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeTranscriptApi')
    def test_extract_video_metadata(self, mock_api):
        """Test video metadata extraction."""
        # Mock the transcript API to return a video title
        mock_api.get_transcript.return_value = []
        
        # For this test, we'll just verify the metadata structure
        llm_client = MagicMock()
        converter = YouTubeConverter(llm_client)
        
        # Since we can't easily mock the internal youtube-transcript-api's metadata,
        # we'll test the default behavior
        metadata = converter.extract_video_metadata("test_video_id")
        
        # Assertions
        assert isinstance(metadata, dict)
        assert 'title' in metadata
        assert 'video_id' in metadata
        assert metadata['video_id'] == "test_video_id"
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeConverter.extract_video_metadata')
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeConverter.get_transcript')
    def test_convert_to_markdown(self, mock_get_transcript, mock_extract_metadata):
        """Test complete conversion pipeline."""
        # Setup mocks
        mock_extract_metadata.return_value = {
            'title': 'Test Video',
            'video_id': 'test123',
            'channel': 'Test Channel',
            'duration': '10:30'
        }
        mock_get_transcript.return_value = "This is the transcript text."
        
        # Mock LLM client
        llm_client = MagicMock()
        llm_response = MagicMock()
        llm_response.content = "# Test Video\n\nThis is the converted article."
        llm_client.invoke.return_value = llm_response
        
        # Create converter and test
        converter = YouTubeConverter(llm_client)
        result = converter.convert_to_markdown("test123", "https://youtube.com/watch?v=test123")
        
        # Assertions
        assert result == "# Test Video\n\nThis is the converted article."
        mock_extract_metadata.assert_called_once_with("test123")
        mock_get_transcript.assert_called_once_with("test123")
        
        # Verify LLM was called with correct data
        llm_client.invoke.assert_called_once()
        call_args = llm_client.invoke.call_args[1]
        assert 'messages' in call_args
        messages = call_args['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert 'YouTube transcript' in messages[0]['content']
        assert messages[1]['role'] == 'user'
        assert 'Test Video' in messages[1]['content']
        assert 'This is the transcript text.' in messages[1]['content']
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeConverter')
    def test_convert_youtube_to_markdown_helper_success(self, mock_converter_cls):
        """Test helper function with successful conversion."""
        # Setup mock converter
        mock_converter = MagicMock()
        mock_converter.convert_to_markdown.return_value = "# Converted Content"
        mock_converter_cls.return_value = mock_converter
        
        # Mock LLM client
        llm_client = MagicMock()
        
        # Test the helper function
        result = convert_youtube_to_markdown("test_video_id", "https://youtube.com/watch?v=test_video_id", llm_client)
        
        # Assertions
        assert result == ("# Converted Content", "https://youtube.com/watch?v=test_video_id")
        mock_converter.convert_to_markdown.assert_called_once_with("test_video_id", "https://youtube.com/watch?v=test_video_id")
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeConverter')
    @patch('kb_for_prompt.molecules.youtube_converter.time.sleep')
    def test_convert_youtube_to_markdown_helper_with_retry(self, mock_sleep, mock_converter_cls):
        """Test helper function retry mechanism."""
        # Setup mock converter to fail twice then succeed
        mock_converter = MagicMock()
        mock_converter.convert_to_markdown.side_effect = [
            ConversionError("Network error", "test_video_id", "youtube"),
            ConversionError("Temporary error", "test_video_id", "youtube"),
            "# Success after retry"
        ]
        mock_converter_cls.return_value = mock_converter
        
        # Mock LLM client
        llm_client = MagicMock()
        
        # Test the helper function
        result = convert_youtube_to_markdown("test_video_id", "https://youtube.com/watch?v=test_video_id", llm_client, max_retries=3)
        
        # Assertions
        assert result == ("# Success after retry", "https://youtube.com/watch?v=test_video_id")
        assert mock_converter.convert_to_markdown.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('kb_for_prompt.molecules.youtube_converter.YouTubeConverter')
    @patch('kb_for_prompt.molecules.youtube_converter.time.sleep')
    def test_convert_youtube_to_markdown_helper_max_retries_exhausted(self, mock_sleep, mock_converter_cls):
        """Test helper function when all retries are exhausted."""
        # Setup mock converter to always fail
        mock_converter = MagicMock()
        mock_converter.convert_to_markdown.side_effect = ConversionError("Persistent error", "test_video_id", "youtube")
        mock_converter_cls.return_value = mock_converter
        
        # Mock LLM client
        llm_client = MagicMock()
        
        # Test the helper function
        with pytest.raises(ConversionError) as exc_info:
            convert_youtube_to_markdown("test_video_id", "https://youtube.com/watch?v=test_video_id", llm_client, max_retries=2)
        
        # Assertions
        assert mock_converter.convert_to_markdown.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2
        assert "Persistent error" in str(exc_info.value)