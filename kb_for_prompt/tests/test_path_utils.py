"""
Tests for path_utils.py
"""

import os
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from kb_for_prompt.atoms.path_utils import (
    resolve_path,
    create_file_url,
    ensure_directory_exists,
    generate_output_filename,
    is_same_file
)
from kb_for_prompt.atoms.error_utils import FileIOError


class TestResolvePathFunction:
    """Tests for resolve_path function."""
    
    def test_with_absolute_path(self):
        # Test with an absolute path
        path = os.path.abspath("/absolute/path")
        result = resolve_path(path)
        assert result == Path(path)
    
    def test_with_string_relative_path(self):
        # Test with a relative path string
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/current/dir")
            result = resolve_path("relative/path")
            assert result == Path("/current/dir/relative/path")
    
    def test_with_path_object(self):
        # Test with a Path object
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/current/dir")
            result = resolve_path(Path("relative/path"))
            assert result == Path("/current/dir/relative/path")
    
    def test_with_base_path(self):
        # Test with a base path
        result = resolve_path("relative/path", "/base/path")
        assert result == Path("/base/path/relative/path")


class TestCreateFileUrlFunction:
    """Tests for create_file_url function."""
    
    def test_unix_path(self):
        # Test with a Unix-style path
        with patch("os.name", "posix"), patch("kb_for_prompt.atoms.path_utils.resolve_path") as mock_resolve:
            mock_resolve.return_value = Path("/path/to/file.txt")
            url = create_file_url("/path/to/file.txt")
            assert url == "file:///path/to/file.txt"
    
    def test_windows_path(self):
        # Test with a Windows-style path
        with patch("os.name", "nt"), patch("kb_for_prompt.atoms.path_utils.resolve_path") as mock_resolve:
            # Since we're on a non-Windows system, we need to create a regular Path
            # and then mock its behavior to act like a Windows path
            mock_path = MagicMock()
            mock_resolve.return_value = mock_path
            
            # Mock the absolute() method to return a string
            mock_path.absolute.return_value = "C:\\path\\to\\file.txt"
            
            url = create_file_url("C:\\path\\to\\file.txt")
            assert url == "file:///C:/path/to/file.txt"


class TestEnsureDirectoryExistsFunction:
    """Tests for ensure_directory_exists function."""
    
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_existing_directory(self):
        # Test with an existing directory
        result = ensure_directory_exists(self.temp_dir)
        assert result == Path(self.temp_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_new_directory(self):
        # Test with a new directory
        new_dir = os.path.join(self.temp_dir, "new_dir")
        result = ensure_directory_exists(new_dir)
        assert result == Path(new_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_nested_directory(self):
        # Test with a nested directory
        nested_dir = os.path.join(self.temp_dir, "parent/child/grandchild")
        result = ensure_directory_exists(nested_dir)
        assert result == Path(nested_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_permission_error(self):
        # Test with a directory that can't be created
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(FileIOError) as excinfo:
                ensure_directory_exists("/path/to/dir")
            
            assert "Failed to create directory" in str(excinfo.value)
            assert excinfo.value.operation == "create_directory"


class TestGenerateOutputFilenameFunction:
    """Tests for generate_output_filename function."""
    
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_url_input(self):
        # Test with a URL input
        url = "https://example.com/page.html"
        result = generate_output_filename(url, self.temp_dir)
        assert result.name == "example_com_page.md"
        assert result.parent == Path(self.temp_dir)
    
    def test_file_input(self):
        # Test with a file input
        file_path = "/path/to/document.pdf"
        result = generate_output_filename(file_path, self.temp_dir)
        assert result.name == "document.md"
        assert result.parent == Path(self.temp_dir)
    
    def test_custom_suffix(self):
        # Test with a custom suffix
        url = "https://example.com/page"
        result = generate_output_filename(url, self.temp_dir, suffix=".txt")
        assert result.name == "example_com_page.txt"
    
    def test_file_name_conflict(self):
        # Test handling of file name conflicts
        url = "https://example.com/page"
        
        # Create a file with the expected name
        first_path = os.path.join(self.temp_dir, "example_com_page.md")
        with open(first_path, "w") as f:
            f.write("Existing content")
        
        # Generate a new filename
        result = generate_output_filename(url, self.temp_dir)
        assert result.name == "example_com_page_1.md"
        
        # Create another conflict
        second_path = os.path.join(self.temp_dir, "example_com_page_1.md")
        with open(second_path, "w") as f:
            f.write("More existing content")
        
        # Generate yet another filename
        result = generate_output_filename(url, self.temp_dir)
        assert result.name == "example_com_page_2.md"
    
    def test_very_long_url(self):
        # Test with a very long URL
        long_url = "https://example.com/" + "a" * 200
        result = generate_output_filename(long_url, self.temp_dir)
        # Filename should be truncated
        assert len(result.stem) <= 100


class TestIsSameFileFunction:
    """Tests for is_same_file function."""
    
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_dir, "test_file.txt")
        
        # Create a test file
        with open(self.file_path, "w") as f:
            f.write("Test content")
    
    def teardown_method(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_same_path(self):
        # Test with the same exact path
        assert is_same_file(self.file_path, self.file_path)
    
    def test_relative_and_absolute_path(self):
        # Test with equivalent paths (relative vs absolute)
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/resolved/path")
            assert is_same_file("/path/one", "/path/two")
    
    def test_different_paths(self):
        # Test with different paths
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.side_effect = [Path("/path/one"), Path("/path/two")]
            assert not is_same_file("/path/one", "/path/two")
    
    def test_error_handling(self):
        # Test error handling
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.side_effect = Exception("Test error")
            assert not is_same_file("/path/one", "/path/two")