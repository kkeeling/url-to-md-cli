import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import xml.etree.ElementTree as ET

# Import rich here, as LlmGenerator uses it
pytest.importorskip("rich")
from rich.console import Console # noqa: E402 - Import after importorskip

# Import the specific component being tested
from kb_for_prompt.organisms.llm_generator import LlmGenerator, TEMPLATE_DIR # noqa: E402
from kb_for_prompt.atoms.error_utils import FileIOError # noqa: E402

# Define sample test data to be used across tests
@pytest.fixture
def sample_data():
    return {
        "xml_data": """
<documents>
  <document path="test_docs/intro.md">Introduction content.</document>
  <document path="test_docs/usage/guide.md">Usage guide content.</document>
</documents>
        """.strip(),
        
        "empty_xml_data": "<documents></documents>",
        "malformed_xml_data": "<documents><document path='test.md'>", # Missing closing tag
        
        "toc_md": """
# Documentation Overview

## Introduction
- [Introduction](test_docs/intro.md)

## Usage
- [Usage Guide](test_docs/usage/guide.md)
        """.strip(),
        
        "kb_md": """
# Knowledge Base

## Introduction

This section covers the basics. (Source: test_docs/intro.md)

## Usage Guide

Details on how to use the system. (Source: test_docs/usage/guide.md)
        """.strip(),
        
        "kb_template_content": """
Given the documents below, perform the following tasks:
...
## Documents
{{documents}}
        """.strip()
    }

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = MagicMock()
    client.invoke = MagicMock()
    return client

@pytest.fixture
def generator(mock_llm_client):
    """Create an LlmGenerator instance with mock LLM client."""
    return LlmGenerator(llm_client=mock_llm_client)

# Path to mock template
MOCK_TEMPLATE_PATH = TEMPLATE_DIR / "kb_extraction_prompt.md"

# --- Tests for _load_prompt_template ---

@patch('pathlib.Path.is_file')
@patch('pathlib.Path.read_text')
def test_load_prompt_template_success(mock_read_text, mock_is_file, generator, sample_data):
    """Test successful loading of a prompt template."""
    mock_is_file.return_value = True
    mock_read_text.return_value = sample_data["kb_template_content"]
    template_path = Path("dummy/path/template.md")

    content = generator._load_prompt_template(template_path)

    mock_is_file.assert_called_once()
    mock_read_text.assert_called_once_with(encoding="utf-8")
    assert content == sample_data["kb_template_content"]

@patch('pathlib.Path.is_file')
@patch('pathlib.Path.read_text')
def test_load_prompt_template_file_not_found(mock_read_text, mock_is_file, generator, caplog):
    """Test loading when the template file does not exist."""
    mock_is_file.return_value = False
    template_path = Path("non/existent/path/template.md")

    with caplog.at_level(logging.ERROR):
        content = generator._load_prompt_template(template_path)

    mock_is_file.assert_called_once()
    assert not mock_read_text.called
    assert content is None
    assert f"Prompt template file not found: {template_path}" in caplog.text

@patch('pathlib.Path.is_file')
@patch('pathlib.Path.read_text', side_effect=IOError("Permission denied"))
def test_load_prompt_template_read_error(mock_read_text, mock_is_file, generator, caplog):
    """Test loading when reading the template file raises an IOError."""
    mock_is_file.return_value = True
    template_path = Path("dummy/path/template.md")

    with caplog.at_level(logging.ERROR):
        content = generator._load_prompt_template(template_path)

    mock_is_file.assert_called_once()
    mock_read_text.assert_called_once_with(encoding="utf-8")
    assert content is None
    assert f"Error reading prompt template file {template_path}: Permission denied" in caplog.text

# --- Tests for generate_toc ---

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_success(mock_scan, generator, mock_llm_client, sample_data):
    """Test successful TOC generation."""
    mock_scan.return_value = sample_data["xml_data"]
    mock_llm_client.invoke.return_value = sample_data["toc_md"]

    toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    mock_llm_client.invoke.assert_called_once()
    
    # Check prompt argument passed to invoke
    call_args, call_kwargs = mock_llm_client.invoke.call_args
    prompt_arg = call_args[0]
    assert isinstance(prompt_arg, str)
    assert "You are a documentation indexing assistant" in prompt_arg
    assert "{{documents}}" not in prompt_arg  # Placeholder should be replaced
    assert "<document" in prompt_arg  # XML should be injected
    
    # Check model argument passed to invoke
    assert call_kwargs.get('model') == "gemini/gemini-2.5-pro-preview-03-25"
    
    # Check result
    assert toc == sample_data["toc_md"]

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_no_documents_in_xml(mock_scan, generator, mock_llm_client, sample_data, caplog):
    """Test TOC generation when scan returns XML with no document elements."""
    mock_scan.return_value = sample_data["empty_xml_data"]

    with caplog.at_level(logging.INFO):
        toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called  # LLM should not be called
    assert toc is None
    assert "No markdown documents found in the XML, skipping TOC generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_empty_xml_string(mock_scan, generator, mock_llm_client, caplog):
    """Test TOC generation when scan returns an empty string."""
    mock_scan.return_value = ""  # Simulate empty result from scan

    with caplog.at_level(logging.INFO):
        toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called  # LLM should not be called
    assert toc is None
    assert "Scan returned empty XML data, skipping TOC generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_malformed_xml(mock_scan, generator, mock_llm_client, sample_data, caplog):
    """Test TOC generation when scan returns malformed XML."""
    mock_scan.return_value = sample_data["malformed_xml_data"]

    with caplog.at_level(logging.ERROR):
        toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called  # LLM should not be called
    assert toc is None
    assert "Malformed XML data from scan, cannot generate TOC" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_llm_error(mock_scan, generator, mock_llm_client, sample_data, caplog):
    """Test TOC generation when the LLM client raises an error."""
    mock_scan.return_value = sample_data["xml_data"]
    mock_llm_client.invoke.side_effect = Exception("LLM API Error")

    with caplog.at_level(logging.ERROR):
        toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    mock_llm_client.invoke.assert_called_once()  # Ensure it was called
    assert toc is None  # Should return None on error
    assert "LLM call failed for TOC generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_toc_scan_error(mock_scan, generator, mock_llm_client, caplog):
    """Test TOC generation when scan_and_build_xml raises an error."""
    mock_scan.side_effect = FileIOError(message="Failed to scan directory", file_path="./test_output_dir", operation="read")

    with caplog.at_level(logging.ERROR):
        toc = generator.generate_toc(Path("./test_output_dir"))

    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called  # LLM should not be called
    assert toc is None
    assert "Failed to scan directory for TOC generation" in caplog.text

def test_generate_toc_no_llm_client(caplog):
    """Test TOC generation when no LLM client is provided."""
    generator_no_client = LlmGenerator(llm_client=None)

    with caplog.at_level(logging.WARNING):
        toc = generator_no_client.generate_toc(Path("./test_output_dir"))

    assert toc is None
    assert "No LLM client provided, cannot generate TOC" in caplog.text

# --- Tests for generate_kb ---

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_success(mock_scan, mock_load_template, generator, mock_llm_client, sample_data):
    """Test successful KB generation."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.return_value = sample_data["xml_data"]
    mock_llm_client.invoke.return_value = sample_data["kb_md"]

    kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    mock_llm_client.invoke.assert_called_once()
    
    # Check prompt argument passed to invoke
    call_args, call_kwargs = mock_llm_client.invoke.call_args
    prompt_arg = call_args[0]
    assert isinstance(prompt_arg, str)
    
    # Create XML without path attributes for comparison
    # We're doing this because our new implementation removes path attributes
    root = ET.fromstring(sample_data["xml_data"])
    for doc in root.findall("document"):
        if 'path' in doc.attrib:
            del doc.attrib['path']
    xml_without_paths = ET.tostring(root, encoding="unicode", xml_declaration=False, short_empty_elements=False)
    
    expected_final_prompt = sample_data["kb_template_content"].replace("{{documents}}", xml_without_paths)
    assert prompt_arg == expected_final_prompt
    
    # Check model argument passed to invoke
    assert call_kwargs.get('model') == "gemini/gemini-2.5-pro-preview-03-25"
    
    # Check result
    assert kb == sample_data["kb_md"]

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_template_load_fails(mock_scan, mock_load_template, generator, mock_llm_client):
    """Test KB generation when loading the template fails."""
    mock_load_template.return_value = None  # Simulate load failure

    kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    assert not mock_scan.called
    assert not mock_llm_client.invoke.called
    assert kb is None

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_scan_error(mock_scan, mock_load_template, generator, mock_llm_client, sample_data, caplog):
    """Test KB generation when scan_and_build_xml raises an error."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.side_effect = FileIOError(message="Failed to scan directory", file_path="./test_output_dir", operation="read")

    with caplog.at_level(logging.ERROR):
        kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called
    assert kb is None
    assert "Failed to scan directory for KB generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_no_documents_in_xml(mock_scan, mock_load_template, generator, mock_llm_client, sample_data, caplog):
    """Test KB generation when scan returns XML with no document elements."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.return_value = sample_data["empty_xml_data"]

    with caplog.at_level(logging.INFO):
        kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called
    assert kb is None
    assert "No markdown documents found in the XML, skipping KB generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_empty_xml_string(mock_scan, mock_load_template, generator, mock_llm_client, sample_data, caplog):
    """Test KB generation when scan returns an empty string."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.return_value = ""  # Simulate empty result

    with caplog.at_level(logging.INFO):
        kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called
    assert kb is None
    assert "Scan returned empty XML data, skipping KB generation" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_malformed_xml(mock_scan, mock_load_template, generator, mock_llm_client, sample_data, caplog):
    """Test KB generation when scan returns malformed XML."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.return_value = sample_data["malformed_xml_data"]

    with caplog.at_level(logging.ERROR):
        kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    assert not mock_llm_client.invoke.called
    assert kb is None
    assert "Malformed XML data from scan, cannot generate KB" in caplog.text

@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator._load_prompt_template')
@patch('kb_for_prompt.organisms.llm_generator.LlmGenerator.scan_and_build_xml')
def test_generate_kb_llm_error(mock_scan, mock_load_template, generator, mock_llm_client, sample_data, caplog):
    """Test KB generation when the LLM client raises an error."""
    mock_load_template.return_value = sample_data["kb_template_content"]
    mock_scan.return_value = sample_data["xml_data"]
    mock_llm_client.invoke.side_effect = Exception("LLM API Error")

    with caplog.at_level(logging.ERROR):
        kb = generator.generate_kb(Path("./test_output_dir"))

    mock_load_template.assert_called_once_with(MOCK_TEMPLATE_PATH)
    mock_scan.assert_called_once()
    mock_llm_client.invoke.assert_called_once()  # Ensure it was called
    assert kb is None  # Should return None on error
    assert "LLM call failed for KB generation" in caplog.text

def test_generate_kb_no_llm_client(caplog):
    """Test KB generation when no LLM client is provided."""
    generator_no_client = LlmGenerator(llm_client=None)

    with caplog.at_level(logging.WARNING):
        kb = generator_no_client.generate_kb(Path("./test_output_dir"))

    assert kb is None
    assert "No LLM client provided, cannot generate KB" in caplog.text