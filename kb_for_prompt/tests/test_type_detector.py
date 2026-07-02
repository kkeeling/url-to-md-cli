"""
Tests for type_detector.py
"""

from pathlib import Path

from kb_for_prompt.atoms.type_detector import (
    detect_input_type,
    detect_file_type,
    get_supported_extensions,
    is_url,
    is_file_path,
    is_supported_file_type,
    is_youtube_url
)


class TestDetectInputTypeFunction:
    """Tests for detect_input_type function."""
    
    def test_http_url(self):
        """Test with HTTP URL."""
        assert detect_input_type("http://example.com") == "url"
    
    def test_https_url(self):
        """Test with HTTPS URL."""
        assert detect_input_type("https://example.com/path?query=value") == "url"
    
    def test_file_url(self):
        """Test with file URL."""
        assert detect_input_type("file:///path/to/file.txt") == "url"
    
    def test_url_without_scheme(self):
        """Test with URL without scheme."""
        assert detect_input_type("example.com") == "url"
        assert detect_input_type("www.example.com") == "url"
        assert detect_input_type("example.com/path") == "url"
    
    def test_ip_address(self):
        """Test with IP address."""
        assert detect_input_type("192.168.1.1") == "url"
        assert detect_input_type("192.168.1.1:8080") == "url"
        assert detect_input_type("192.168.1.1/path") == "url"
    
    def test_absolute_file_path(self):
        """Test with absolute file path."""
        assert detect_input_type("/path/to/file.txt") == "file"
    
    def test_relative_file_path(self):
        """Test with relative file path."""
        assert detect_input_type("./path/to/file.txt") == "file"
        assert detect_input_type("path/to/file.txt") == "file"
    
    def test_windows_file_path(self):
        """Test with Windows file path."""
        assert detect_input_type("C:\\path\\to\\file.txt") == "file"
        assert detect_input_type("C:/path/to/file.txt") == "file"


class TestDetectFileTypeFunction:
    """Tests for detect_file_type function."""
    
    def test_doc_file(self):
        """Test with .doc file."""
        assert detect_file_type("document.doc") == "doc"
        assert detect_file_type(Path("document.doc")) == "doc"
    
    def test_docx_file(self):
        """Test with .docx file."""
        assert detect_file_type("document.docx") == "docx"
        assert detect_file_type(Path("document.docx")) == "docx"
    
    def test_pdf_file(self):
        """Test with .pdf file."""
        assert detect_file_type("document.pdf") == "pdf"
        assert detect_file_type(Path("document.pdf")) == "pdf"
    
    def test_mixed_case_extension(self):
        """Test with mixed case extension."""
        assert detect_file_type("document.DOC") == "doc"
        assert detect_file_type("document.DocX") == "docx"
        assert detect_file_type("document.PDF") == "pdf"
    
    def test_unsupported_file_type(self):
        """Test with unsupported file type."""
        assert detect_file_type("document.txt") is None
        assert detect_file_type("image.jpg") is None
        assert detect_file_type("script.py") is None
    
    def test_no_extension(self):
        """Test with no extension."""
        assert detect_file_type("document") is None
        assert detect_file_type(Path("document")) is None


class TestGetSupportedExtensionsFunction:
    """Tests for get_supported_extensions function."""
    
    def test_returns_supported_extensions(self):
        """Test that it returns the expected extensions."""
        extensions = get_supported_extensions()
        assert "doc" in extensions
        assert "docx" in extensions
        assert "pdf" in extensions
        assert len(extensions) == 3  # Only these three extensions should be supported
        assert all(isinstance(ext, str) for ext in extensions)  # All should be strings


class TestIsUrlFunction:
    """Tests for is_url function."""
    
    def test_with_urls(self):
        """Test with valid URLs."""
        assert is_url("http://example.com")
        assert is_url("https://example.com/path")
        assert is_url("file:///path/to/file.txt")
        assert is_url("example.com")
    
    def test_with_file_paths(self):
        """Test with file paths."""
        assert not is_url("/path/to/file.txt")
        assert not is_url("./relative/path.txt")
        assert not is_url("C:\\Windows\\path.txt")


class TestIsFilePathFunction:
    """Tests for is_file_path function."""
    
    def test_with_file_paths(self):
        """Test with file paths."""
        assert is_file_path("/path/to/file.txt")
        assert is_file_path("./relative/path.txt")
        assert is_file_path("C:\\Windows\\path.txt")
    
    def test_with_urls(self):
        """Test with URLs."""
        assert not is_file_path("http://example.com")
        assert not is_file_path("https://example.com/path")
        assert not is_file_path("file:///path/to/file.txt")
        assert not is_file_path("example.com")


class TestIsSupportedFileTypeFunction:
    """Tests for is_supported_file_type function."""
    
    def test_supported_file_types(self):
        """Test with supported file types."""
        assert is_supported_file_type("document.doc")
        assert is_supported_file_type("document.docx")
        assert is_supported_file_type("document.pdf")
        assert is_supported_file_type(Path("document.pdf"))
    
    def test_unsupported_file_types(self):
        """Test with unsupported file types."""
        assert not is_supported_file_type("document.txt")
        assert not is_supported_file_type("image.jpg")
        assert not is_supported_file_type("script.py")
        assert not is_supported_file_type(Path("document.txt"))
    
    def test_mixed_case_extensions(self):
        """Test with mixed case extensions."""
        assert is_supported_file_type("document.DOC")
        assert is_supported_file_type("document.DocX")
        assert is_supported_file_type("document.PDF")


class TestIsYoutubeUrlFunction:
    """Tests for is_youtube_url function."""
    
    def test_youtube_watch_url(self):
        """Test various youtube.com/watch?v= URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://www.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("www.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_youtube_mobile_url(self):
        """Test m.youtube.com URL formats."""
        test_cases = [
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://m.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("m.youtube.com/watch?v=dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_youtu_be_url(self):
        """Test youtu.be shortened URL formats."""
        test_cases = [
            ("https://youtu.be/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://youtu.be/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("youtu.be/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_youtube_embed_url(self):
        """Test youtube.com/embed/ URL formats."""
        test_cases = [
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://www.youtube.com/embed/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://youtube.com/embed/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("youtube.com/embed/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_youtube_v_url(self):
        """Test youtube.com/v/ URL formats."""
        test_cases = [
            ("https://www.youtube.com/v/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("http://www.youtube.com/v/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("https://youtube.com/v/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
            ("youtube.com/v/dQw4w9WgXcQ", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_youtube_url_with_additional_parameters(self):
        """Test YouTube URLs with additional query parameters."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be", True, "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s", True, "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ?t=1m30s", True, "dQw4w9WgXcQ"),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"
    
    def test_non_youtube_urls(self):
        """Test non-YouTube URLs return False."""
        test_cases = [
            ("https://example.com", False, None),
            ("https://vimeo.com/123456789", False, None),
            ("https://www.dailymotion.com/video/x12345", False, None),
            ("not_a_url", False, None),
            ("/path/to/file.mp4", False, None),
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed for URL: {url}"
    
    def test_youtube_url_with_different_video_ids(self):
        """Test YouTube URLs with various valid video ID formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=Y5elLLjcmLU", True, "Y5elLLjcmLU"),  # Test video from spec
            ("https://youtu.be/-wtIMTCHWuI", True, "-wtIMTCHWuI"),  # ID with dash
            ("https://youtube.com/watch?v=0zM3nApSvMg", True, "0zM3nApSvMg"),  # ID starting with number
            ("https://youtube.com/embed/lalOy8Mbfdc", True, "lalOy8Mbfdc"),  # Mixed case ID
        ]
        
        for url, expected_is_youtube, expected_id in test_cases:
            is_yt, video_id = is_youtube_url(url)
            assert is_yt == expected_is_youtube, f"Failed for URL: {url}"
            assert video_id == expected_id, f"Failed to extract ID from URL: {url}"