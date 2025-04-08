"""
Tests for input_validator.py
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from kb_for_prompt.atoms.input_validator import (
    validate_url,
    validate_file_path,
    validate_file_type,
    validate_directory_path,
    validate_input_item
)
from kb_for_prompt.atoms.error_utils import ValidationError


class TestValidateUrlFunction:
    """Tests for validate_url function."""
    
    def test_valid_http_url(self):
        """Test with valid HTTP URL."""
        assert validate_url("http://example.com") is True
    
    def test_valid_https_url(self):
        """Test with valid HTTPS URL."""
        assert validate_url("https://example.com/path") is True
    
    def test_valid_file_url(self):
        """Test with valid file URL."""
        assert validate_url("file:///path/to/file.txt") is True
    
    def test_invalid_url_format(self):
        """Test with invalid URL format."""
        with patch("kb_for_prompt.atoms.type_detector.is_url", return_value=False):
            with pytest.raises(ValidationError) as excinfo:
                validate_url("not-a-url")
            assert "Invalid URL format" in str(excinfo.value)
    
    def test_unsupported_url_scheme(self):
        """Test with unsupported URL scheme."""
        with patch("kb_for_prompt.atoms.type_detector.is_url", return_value=True):
            with pytest.raises(ValidationError) as excinfo:
                validate_url("ftp://example.com")
            assert "Unsupported URL scheme" in str(excinfo.value)
    
    def test_missing_domain(self):
        """Test with missing domain."""
        # We need to modify both the is_url return value and the urlparse return value
        # First, ensure is_url returns True to bypass the first check
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=True):
            # Then, patch urlparse to return a URL with scheme but no netloc
            with patch("urllib.parse.urlparse") as mock_urlparse:
                mock_result = MagicMock()
                mock_result.scheme = "http"
                mock_result.netloc = ""
                mock_urlparse.return_value = mock_result
                
                with pytest.raises(ValidationError) as excinfo:
                    validate_url("http://")
                assert "Invalid URL: missing domain" in str(excinfo.value)
    
    def test_invalid_file_url(self):
        """Test with invalid file URL."""
        # First, ensure is_url returns True to bypass the first check
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=True):
            # Then, patch urlparse to return a file URL with no path
            with patch("urllib.parse.urlparse") as mock_urlparse:
                mock_result = MagicMock()
                mock_result.scheme = "file"
                mock_result.path = ""
                mock_urlparse.return_value = mock_result
                
                with pytest.raises(ValidationError) as excinfo:
                    validate_url("file://")
                assert "Invalid file URL: missing path component" in str(excinfo.value)
    
    def test_url_connection_check_success(self):
        """Test URL connection check success."""
        with patch("requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            assert validate_url("https://example.com", check_connection=True) is True
    
    def test_url_connection_check_http_error(self):
        """Test URL connection check with HTTP error."""
        with patch("requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            with pytest.raises(ValidationError) as excinfo:
                validate_url("https://example.com", check_connection=True)
            assert "URL returned error status: 404" in str(excinfo.value)
    
    def test_url_connection_check_request_exception(self):
        """Test URL connection check with request exception."""
        # First, ensure is_url returns True to bypass the first check
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=True):
            with patch("requests.head") as mock_head, \
                 patch("requests.RequestException", Exception):  # Make any Exception a RequestException
                
                mock_head.side_effect = Exception("Connection refused")
                
                with pytest.raises(ValidationError) as excinfo:
                    validate_url("https://example.com", check_connection=True)
                assert "Failed to connect to URL" in str(excinfo.value)


class TestValidateFilePathFunction:
    """Tests for validate_file_path function."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory and file
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_dir, "test_file.txt")
        
        # Create a test file
        with open(self.file_path, "w") as f:
            f.write("Test content")
        
        # Create a directory
        self.dir_path = os.path.join(self.temp_dir, "test_dir")
        os.mkdir(self.dir_path)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_file_path(self):
        """Test with valid file path."""
        result = validate_file_path(self.file_path)
        assert result == Path(self.file_path)
    
    def test_invalid_path_type(self):
        """Test with invalid path type."""
        with pytest.raises(ValidationError) as excinfo:
            validate_file_path(123)
        assert "File path must be a string or Path object" in str(excinfo.value)
    
    def test_non_existent_file(self):
        """Test with non-existent file."""
        non_existent = os.path.join(self.temp_dir, "non_existent.txt")
        
        with pytest.raises(ValidationError) as excinfo:
            validate_file_path(non_existent)
        assert "File does not exist" in str(excinfo.value)
        
        # Test with must_exist=False
        result = validate_file_path(non_existent, must_exist=False)
        assert result == Path(non_existent)
    
    def test_directory_not_file(self):
        """Test with a directory instead of a file."""
        with pytest.raises(ValidationError) as excinfo:
            validate_file_path(self.dir_path)
        assert "Path exists but is not a file" in str(excinfo.value)
    
    def test_not_readable_file(self):
        """Test with a not readable file."""
        with patch("os.access", return_value=False):
            with pytest.raises(ValidationError) as excinfo:
                validate_file_path(self.file_path)
            assert "File exists but is not readable" in str(excinfo.value)


class TestValidateFileTypeFunction:
    """Tests for validate_file_type function."""
    
    def test_valid_file_type(self):
        """Test with valid file type."""
        assert validate_file_type("document.docx") == "docx"
        assert validate_file_type("document.pdf") == "pdf"
        assert validate_file_type(Path("document.doc")) == "doc"
    
    def test_custom_allowed_types(self):
        """Test with custom allowed types."""
        assert validate_file_type("image.jpg", allowed_types=["jpg", "png"]) == "jpg"
        assert validate_file_type("image.png", allowed_types=["jpg", "png"]) == "png"
    
    def test_file_without_extension(self):
        """Test with file without extension."""
        with pytest.raises(ValidationError) as excinfo:
            validate_file_type("document")
        assert "File has no extension" in str(excinfo.value)
    
    def test_unsupported_file_type(self):
        """Test with unsupported file type."""
        with pytest.raises(ValidationError) as excinfo:
            validate_file_type("image.jpg")
        assert "Unsupported file type: .jpg" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            validate_file_type("script.py", allowed_types=["js", "ts"])
        assert "Unsupported file type: .py" in str(excinfo.value)
        assert "Allowed types: js, ts" in str(excinfo.value)


class TestValidateDirectoryPathFunction:
    """Tests for validate_directory_path function."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a file
        self.file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(self.file_path, "w") as f:
            f.write("Test content")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_directory_path(self):
        """Test with valid directory path."""
        result = validate_directory_path(self.temp_dir, must_exist=True)
        assert result == Path(self.temp_dir)
    
    def test_invalid_path_type(self):
        """Test with invalid path type."""
        with pytest.raises(ValidationError) as excinfo:
            validate_directory_path(123)
        assert "Directory path must be a string or Path object" in str(excinfo.value)
    
    def test_non_existent_directory(self):
        """Test with non-existent directory."""
        non_existent = os.path.join(self.temp_dir, "non_existent_dir")
        
        with pytest.raises(ValidationError) as excinfo:
            validate_directory_path(non_existent, must_exist=True)
        assert "Directory does not exist" in str(excinfo.value)
        
        # Test with must_exist=False
        result = validate_directory_path(non_existent, must_exist=False)
        assert result == Path(non_existent)
    
    def test_file_not_directory(self):
        """Test with a file instead of a directory."""
        with pytest.raises(ValidationError) as excinfo:
            validate_directory_path(self.file_path, must_exist=True)
        assert "Path exists but is not a directory" in str(excinfo.value)
    
    def test_not_readable_directory(self):
        """Test with a not readable directory."""
        with patch("os.access", return_value=False):
            with pytest.raises(ValidationError) as excinfo:
                validate_directory_path(self.temp_dir, must_exist=True)
            assert "Directory exists but is not readable" in str(excinfo.value)


class TestValidateInputItemFunction:
    """Tests for validate_input_item function."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_dir, "test_file.pdf")
        
        # Create a test file
        with open(self.file_path, "w") as f:
            f.write("Test content")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_url(self):
        """Test with valid URL."""
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=True), \
             patch("kb_for_prompt.atoms.input_validator.validate_url", return_value=True):
            result = validate_input_item("https://example.com")
            assert result == ("url", "https://example.com")
    
    def test_valid_file_path(self):
        """Test with valid file path."""
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=False), \
             patch("kb_for_prompt.atoms.input_validator.validate_file_path") as mock_validate_file_path, \
             patch("kb_for_prompt.atoms.input_validator.detect_file_type", return_value="pdf"):
            mock_validate_file_path.return_value = Path(self.file_path)
            
            result = validate_input_item(self.file_path)
            assert result == ("file", self.file_path)
    
    def test_unsupported_file_type(self):
        """Test with unsupported file type."""
        with patch("kb_for_prompt.atoms.input_validator.is_url", return_value=False), \
             patch("kb_for_prompt.atoms.input_validator.validate_file_path") as mock_validate_file_path, \
             patch("kb_for_prompt.atoms.input_validator.detect_file_type", return_value=None):
            mock_validate_file_path.return_value = Path(self.file_path)
            
            with pytest.raises(ValidationError) as excinfo:
                validate_input_item(self.file_path)
            assert "Unsupported file type" in str(excinfo.value)