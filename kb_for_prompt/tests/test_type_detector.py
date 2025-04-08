"""
Tests for type_detector.py
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from kb_for_prompt.atoms.type_detector import (
    detect_input_type,
    detect_file_type,
    get_supported_extensions,
    is_url,
    is_file_path,
    is_supported_file_type
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