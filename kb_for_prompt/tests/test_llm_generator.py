import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import logging

# Import rich here, as LlmGenerator uses it.
# If rich itself was problematic, we might use pytest.importorskip("rich")
pytest.importorskip("rich")
from rich.console import Console # noqa: E402 - Import after importorskip

# Import the specific component being tested.
# The changes in organisms/__init__.py should ensure this import works
# even if other organisms fail to import due to dependencies.
from kb_for_prompt.organisms.llm_generator import LlmGenerator # noqa: E402

# Import error utilities used in tests
from kb_for_prompt.atoms.error_utils import FileIOError # noqa: E402


# Fixture to create a mock Console
@pytest.fixture
def mock_console():
    """Fixture to create a mock Rich Console."""
    # Using MagicMock with spec ensures the mock behaves like a Console instance
    return MagicMock(spec=Console)

# Fixture to create a mock LLM client
@pytest.fixture
def mock_llm_client():
    """Fixture to create a mock LLM client."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "# Sample TOC\n\n- [Document 1](doc1.md)\n- [Document 2](doc2.md)"
    return mock_client

# Fixture to create an LlmGenerator instance with a mock console
@pytest.fixture
def generator(mock_console):
    """Fixture to create an LlmGenerator instance with a mock console."""
    return LlmGenerator(console=mock_console)

# Fixture to create an LlmGenerator instance with both mock console and mock LLM client
@pytest.fixture
def generator_with_llm(mock_console, mock_llm_client):
    """Fixture to create an LlmGenerator instance with a mock console and mock LLM client."""
    return LlmGenerator(console=mock_console, llm_client=mock_llm_client)

def test_scan_empty_directory(generator, tmp_path):
    """Test scanning an empty directory returns an empty documents XML."""
    xml_output = generator.scan_and_build_xml(tmp_path)
    # Accept either format of empty element: <documents /> or <documents></documents>
    assert xml_output in ["<documents />", "<documents></documents>"]

def test_scan_with_markdown_files_recursive(generator, tmp_path):
    """Test scanning a directory with markdown files recursively generates correct XML."""
    # Create test files
    md_file1 = tmp_path / "file1.md"
    md_file1.write_text("Content of file 1.", encoding="utf-8")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    md_file2 = subdir / "file2.md"
    md_file2.write_text("Content from subdir.", encoding="utf-8")

    deeper_subdir = subdir / "deeper"
    deeper_subdir.mkdir()
    md_file3 = deeper_subdir / "file3.md"
    md_file3.write_text("Content from deeper subdir.", encoding="utf-8")


    # Create a non-markdown file to ensure it's ignored
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("This should be ignored.", encoding="utf-8")

    # Create an empty markdown file
    empty_md_file = tmp_path / "empty.md"
    empty_md_file.write_text("", encoding="utf-8")


    xml_output = generator.scan_and_build_xml(tmp_path)

    # Parse the XML to verify structure and content
    root = ET.fromstring(xml_output)
    assert root.tag == "documents"

    docs = root.findall("document")
    # Sort documents by path for consistent assertion order
    docs.sort(key=lambda doc: doc.get("path"))

    assert len(docs) == 4 # empty.md, file1.md, subdir/deeper/file3.md, subdir/file2.md

    paths_and_content = {doc.get("path"): doc.text for doc in docs}

    # Use forward slashes for paths consistently
    expected_path_file2 = "subdir/file2.md"
    expected_path_file3 = "subdir/deeper/file3.md"

    # Check paths and content
    assert docs[0].get("path") == "empty.md"
    # In XML, empty text can be represented as None or empty string
    assert docs[0].text is None or docs[0].text == ""

    assert docs[1].get("path") == "file1.md"
    assert docs[1].text == "Content of file 1."

    assert docs[2].get("path") == expected_path_file3
    assert docs[2].text == "Content from deeper subdir."

    assert docs[3].get("path") == expected_path_file2
    assert docs[3].text == "Content from subdir."

    assert "notes.txt" not in paths_and_content


def test_scan_file_read_error(generator, mock_console, tmp_path):
    """Test that a file causing a read error is skipped and a warning is logged."""
    readable_file = tmp_path / "readable.md"
    readable_file.write_text("Readable content", encoding="utf-8")

    unreadable_file_path = tmp_path / "unreadable.md"
    # Don't write content, just mock the read error
    unreadable_file_path.touch()

    # Mock Path.read_text to raise an error only for the specific unreadable file
    original_read_text = Path.read_text
    def mock_read_text_side_effect(self, encoding=None, errors=None):
        # Make sure 'self' is resolved for consistent comparison
        if self.resolve() == unreadable_file_path.resolve():
            raise IOError("Permission denied on read")
        # Call the original method for other files
        # Need to handle potential args/kwargs mismatch if original_read_text is complex
        # For Path.read_text, this should be okay.
        return original_read_text(self, encoding=encoding, errors=errors)

    # Use patch on the Path class itself
    with patch.object(Path, 'read_text', side_effect=mock_read_text_side_effect, autospec=True):
        xml_output = generator.scan_and_build_xml(tmp_path)

    # Check that a warning was printed via the mock console
    # Use flexible matching for the path separator which might be OS-dependent in the mock call
    expected_warning_fragment = "Skipping file 'unreadable.md' due to error: Permission denied on read"
    # Check if any call to mock_console.print contains the expected warning fragment
    call_found = False
    for call in mock_console.print.call_args_list:
        args, kwargs = call
        if args and expected_warning_fragment in args[0]:
            call_found = True
            break
    assert call_found, f"Expected warning containing '{expected_warning_fragment}' was not printed."


    # Verify XML contains only the readable file
    root = ET.fromstring(xml_output)
    docs = root.findall("document")
    assert len(docs) == 1
    assert docs[0].get("path") == "readable.md"
    assert docs[0].text == "Readable content"


def test_scan_non_existent_directory(generator):
    """Test scanning a non-existent directory raises FileNotFoundError."""
    non_existent_path = Path("./non_existent_dir_12345")
    assert not non_existent_path.exists() # Ensure it doesn't exist

    with pytest.raises(FileNotFoundError, match=f"Directory not found: {non_existent_path}"):
        generator.scan_and_build_xml(non_existent_path)

def test_scan_path_is_a_file(generator, tmp_path):
    """Test scanning a path that points to a file raises NotADirectoryError."""
    file_path = tmp_path / "i_am_a_file.txt"
    file_path.write_text("hello")

    with pytest.raises(NotADirectoryError, match=f"Path is not a directory: {file_path.resolve()}"):
         generator.scan_and_build_xml(file_path)

def test_scan_directory_permission_error_rglob(generator, tmp_path):
    """Test handling of PermissionError when rglob encounters an inaccessible directory."""
    # Create a file to ensure rglob starts processing
    (tmp_path / "accessible.md").touch()

    # Mock Path.rglob to raise PermissionError
    # Patching the method on the class level
    with patch.object(Path, 'rglob', autospec=True) as mock_rglob:
        # Configure the mock to raise PermissionError when called
        mock_rglob.side_effect = PermissionError("Permission denied accessing subdirectory")

        # We expect a FileIOError wrapping the original PermissionError
        with pytest.raises(FileIOError) as excinfo:
             generator.scan_and_build_xml(tmp_path)

        # Check the error message and the original cause
        assert "Permission denied while scanning directory contents" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, PermissionError)
        assert "Permission denied accessing subdirectory" in str(excinfo.value.__cause__)


def test_xml_encoding_and_special_chars(generator, tmp_path):
    """Test that XML handles special characters correctly."""
    md_file = tmp_path / "special.md"
    content = "Content with <tag> & \"quotes' and > greater than"
    md_file.write_text(content, encoding="utf-8")

    xml_output = generator.scan_and_build_xml(tmp_path)

    # Check raw string output for escaped characters
    # ElementTree handles attribute quoting automatically (' vs ")
    # Path separators should be '/'
    expected_xml_fragment = "<document path=\"special.md\">Content with &lt;tag&gt; &amp; \"quotes' and &gt; greater than</document>"
    assert expected_xml_fragment in xml_output

    # Parse and check text content
    root = ET.fromstring(xml_output)
    doc = root.find("document[@path='special.md']")
    assert doc is not None
    assert doc.text == content # ElementTree automatically handles unescaping when parsed

def test_scan_skips_unreadable_subdir_via_rglob_behavior(generator, mock_console, tmp_path):
    """Test that rglob skipping unreadable subdirs doesn't cause errors or unexpected logs."""
    # This test relies on the typical behavior of Path.rglob, which often
    # yields accessible files and skips inaccessible directories without raising
    # an error that stops the whole iteration (though specifics can be OS/filesystem dependent).

    readable_file = tmp_path / "root.md"
    readable_file.write_text("Root content", encoding="utf-8")

    readable_subdir = tmp_path / "readable_dir"
    readable_subdir.mkdir()
    (readable_subdir / "sub.md").write_text("Sub content", encoding="utf-8")

    unreadable_subdir = tmp_path / "unreadable_dir"
    unreadable_subdir.mkdir()
    (unreadable_subdir / "hidden.md").write_text("Cannot see this", encoding="utf-8")

    # Mock Path.rglob to simulate finding only readable files/dirs
    # This simulates the *result* of rglob skipping the unreadable dir
    # without explicitly mocking the permission error handling *within* rglob.
    def mock_rglob_side_effect(self, pattern):
        # Only yield files from the root and the readable subdirectory
        if self.resolve() == tmp_path.resolve():
            yield readable_file.resolve()
            yield (readable_subdir / "sub.md").resolve()
        else:
            # Prevent recursion or handle other calls if necessary
            yield from [] # Return empty iterator for other paths

    with patch('pathlib.Path.rglob', side_effect=mock_rglob_side_effect, autospec=True):
         xml_output = generator.scan_and_build_xml(tmp_path)

    # Verify XML contains only the readable files
    root = ET.fromstring(xml_output)
    docs = root.findall("document")
    docs.sort(key=lambda doc: doc.get("path")) # Sort for consistent order

    assert len(docs) == 2
    assert docs[0].get("path") == "readable_dir/sub.md"
    assert docs[0].text == "Sub content"
    assert docs[1].get("path") == "root.md"
    assert docs[1].text == "Root content"


    # Assert that no warning was logged by LlmGenerator for the skipped *directory*
    # (Warnings are only logged for file read errors or rglob *raising* an error)
    found_unexpected_call = False
    for call_args in mock_console.print.call_args_list:
        args, kwargs = call_args
        # Check if the call message contains directory names or permission errors related to dirs
        # Be specific to avoid matching file-related warnings
        if args and ("unreadable_dir" in args[0] or "directory" in args[0].lower()):
             # Allow warnings about *files* within directories
             if "Skipping file" not in args[0]:
                 found_unexpected_call = True
                 print(f"Unexpected console call found: {args[0]}") # Debugging output
                 break
    assert not found_unexpected_call, "Console should not have logged warnings about skipping the directory itself."

# Tests for generate_toc method

def test_generate_toc_success(generator_with_llm, tmp_path):
    """Test successful generation of TOC from markdown files."""
    # Create test files
    md_file1 = tmp_path / "file1.md"
    md_file1.write_text("# Document 1\n\nContent of file 1.", encoding="utf-8")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    md_file2 = subdir / "file2.md"
    md_file2.write_text("# Document 2\n\nContent from subdir.", encoding="utf-8")
    
    # Call generate_toc
    result = generator_with_llm.generate_toc(tmp_path)
    
    # Assert result is the mock response
    assert result == "# Sample TOC\n\n- [Document 1](doc1.md)\n- [Document 2](doc2.md)"
    
    # Assert LLM client was called with correct parameters
    assert generator_with_llm.llm_client.generate.called
    args, kwargs = generator_with_llm.llm_client.generate.call_args
    
    # Check prompt content
    assert "You are a documentation indexing assistant" in kwargs["prompt"]
    assert "{{documents}}" not in kwargs["prompt"]  # Placeholder should be replaced
    assert "<document" in kwargs["prompt"]  # XML should be injected
    
    # Check model alias
    assert kwargs["model_alias"] == "gemini/gemini-2.5-pro-preview-03-25"

def test_generate_toc_no_documents(generator_with_llm, tmp_path):
    """Test TOC generation with no markdown files."""
    # Create a directory with no markdown files
    txt_file = tmp_path / "not_markdown.txt"
    txt_file.write_text("This is not a markdown file.", encoding="utf-8")
    
    # Call generate_toc
    with patch("logging.info") as mock_log:
        result = generator_with_llm.generate_toc(tmp_path)
    
    # Assert result is None
    assert result is None
    
    # Assert LLM client was not called
    assert not generator_with_llm.llm_client.generate.called
    
    # Assert appropriate log message
    mock_log.assert_called_once()
    assert "No markdown documents found" in mock_log.call_args[0][0]

def test_generate_toc_llm_error(generator_with_llm, tmp_path):
    """Test handling of LLM client errors during TOC generation."""
    # Create a test file to ensure there's content
    md_file = tmp_path / "file.md"
    md_file.write_text("# Document\n\nContent.", encoding="utf-8")
    
    # Configure LLM client to raise an exception
    generator_with_llm.llm_client.generate.side_effect = Exception("LLM API error")
    
    # Call generate_toc with logging capture
    with patch("logging.error") as mock_log:
        result = generator_with_llm.generate_toc(tmp_path)
    
    # Assert result is None
    assert result is None
    
    # Assert error was logged
    mock_log.assert_called_once()
    assert "LLM call failed for TOC generation" in mock_log.call_args[0][0]

def test_generate_toc_without_llm_client(generator, tmp_path):
    """Test TOC generation without an LLM client."""
    # Create a test file to ensure there's content
    md_file = tmp_path / "file.md"
    md_file.write_text("# Document\n\nContent.", encoding="utf-8")
    
    # Call generate_toc with logging capture
    with patch("logging.warning") as mock_log:
        result = generator.generate_toc(tmp_path)
    
    # Assert result is None
    assert result is None
    
    # Assert warning was logged
    mock_log.assert_called_once()
    assert "No LLM client provided" in mock_log.call_args[0][0]

def test_generate_toc_scan_error(generator_with_llm, tmp_path):
    """Test TOC generation when scanning fails."""
    # Mock scan_and_build_xml to raise an exception
    with patch.object(LlmGenerator, "scan_and_build_xml", side_effect=FileIOError(message="Test error", file_path=str(tmp_path), operation="read")):
        with patch("logging.error") as mock_log:
            result = generator_with_llm.generate_toc(tmp_path)
    
    # Assert result is None
    assert result is None
    
    # Assert error was logged
    mock_log.assert_called_once()
    assert "Failed to generate TOC" in mock_log.call_args[0][0]
    
    # Assert LLM client was not called
    assert not generator_with_llm.llm_client.generate.called

def test_generate_toc_malformed_xml(generator_with_llm):
    """Test TOC generation with malformed XML."""
    # Create a test mock to return malformed XML
    with patch.object(LlmGenerator, "scan_and_build_xml", return_value="<documents><document>Unclosed tag</documents>"):
        with patch("logging.error") as mock_log:
            result = generator_with_llm.generate_toc("dummy_path")
    
    # Assert result is None
    assert result is None
    
    # Assert error about malformed XML was logged
    mock_log.assert_called_once()
    assert "Malformed XML data" in mock_log.call_args[0][0]
    
    # Assert LLM client was not called
    assert not generator_with_llm.llm_client.generate.called
