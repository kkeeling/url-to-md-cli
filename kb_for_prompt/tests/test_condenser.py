# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pytest",
#     "pytest-mock",
# ]
# ///

import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
from pathlib import Path
import sys

# --- Test Setup: Handle potential ImportError for litellm in condenser ---
# We need to decide if we mock the check or the client itself.
# Let's mock the client instantiation and the availability flag as needed.

# Import the function and constants to be tested
try:
    from kb_for_prompt.organisms.condenser import condense_knowledge_base, CONDENSE_PROMPT, CONDENSE_MODEL
    CONDENSER_AVAILABLE = True
except ImportError as e:
    # This might happen if condenser.py itself has an issue unrelated to litellm
    print(f"Failed to import condenser module: {e}", file=sys.stderr)
    CONDENSER_AVAILABLE = False


# --- Fixtures ---

@pytest.fixture
def mock_llm_client_instance():
    """Provides a mock instance of LiteLlmClient."""
    client = MagicMock()
    client.invoke = MagicMock()
    return client

@pytest.fixture
def sample_kb_content():
    """Provides sample knowledge base content."""
    return "# Sample KB\n\nThis is the first section.\n\n## Topic A\nDetails about A.\n\n## Topic B\nDetails about B."

@pytest.fixture
def sample_condensed_content():
    """Provides sample condensed content returned by the LLM."""
    return "## Summary\nKey points about Topic A and Topic B."

@pytest.fixture
def test_file_path():
    """Provides a Path object for a dummy input file."""
    # Using Path objects for consistency
    return Path("./dummy_kb.md")

@pytest.fixture
def expected_output_path(test_file_path):
    """Provides the expected output Path object."""
    return test_file_path.parent / "knowledge_base_condensed.md"


# --- Test Class ---

# Only run tests if the condenser module could be imported
@pytest.mark.skipif(not CONDENSER_AVAILABLE, reason="Condenser module not available for import")
class TestCondenseKnowledgeBase:
    """Tests for the condense_knowledge_base function."""

    # --- Success Path ---

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_condense_success(
        self,
        mock_write_text,
        mock_read_text,
        mock_is_file,
        MockLiteLlmClient,
        mock_llm_client_instance, # Use the instance fixture
        test_file_path,
        expected_output_path,
        sample_kb_content,
        sample_condensed_content,
        caplog
    ):
        """Test successful condensation of a knowledge base file."""
        # Arrange
        mock_is_file.return_value = True
        mock_read_text.return_value = sample_kb_content
        MockLiteLlmClient.return_value = mock_llm_client_instance # Make constructor return our mock instance
        mock_llm_client_instance.invoke.return_value = sample_condensed_content

        expected_full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=sample_kb_content)

        # Act
        with caplog.at_level(logging.INFO):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path == expected_output_path
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with() # Check client instantiation
        mock_llm_client_instance.invoke.assert_called_once_with(
            prompt=expected_full_prompt,
            model=CONDENSE_MODEL
        )
        mock_write_text.assert_called_once_with(sample_condensed_content, encoding='utf-8')

        # Check logs
        assert f"Starting condensation process for: {test_file_path}" in caplog.text
        assert f"Reading content from {test_file_path}" in caplog.text
        assert "LiteLlmClient instantiated successfully." in caplog.text
        assert f"Sending request to LLM model: {CONDENSE_MODEL}" in caplog.text
        assert "Received condensed content from LLM." in caplog.text
        assert f"Attempting to write condensed knowledge base to: {expected_output_path}" in caplog.text
        assert f"Successfully wrote condensed file: {expected_output_path}" in caplog.text

    # --- Input File Error Handling ---

    @patch('pathlib.Path.is_file', return_value=False)
    @patch('pathlib.Path.exists', return_value=False) # Simulate file truly not existing
    def test_condense_input_file_not_found(self, mock_exists, mock_is_file, test_file_path, caplog):
        """Test handling when the input file does not exist."""
        # Arrange
        # is_file and exists are patched

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_exists.assert_called_once_with() # Check that exists() was called after is_file() failed
        assert f"Input file not found: {test_file_path}" in caplog.text

    @patch('pathlib.Path.is_file', return_value=False)
    @patch('pathlib.Path.exists', return_value=True) # Simulate path exists but is not a file
    def test_condense_input_path_is_directory(self, mock_exists, mock_is_file, test_file_path, caplog):
        """Test handling when the input path is a directory."""
        # Arrange
        # is_file and exists are patched

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_exists.assert_called_once_with()
        assert f"Input path exists but is not a file: {test_file_path}" in caplog.text

    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text', side_effect=IOError("Permission denied"))
    def test_condense_read_error(self, mock_read_text, mock_is_file, test_file_path, caplog):
        """Test handling of IOError during file reading."""
        # Arrange
        # is_file and read_text are patched

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        assert f"Error reading file {test_file_path}: Permission denied" in caplog.text

    # --- LLM Client / Prerequisite Error Handling ---

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', False)
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text') # Need to mock read_text even if not used after check
    def test_condense_litellm_not_available(self, mock_read_text, mock_is_file, test_file_path, sample_kb_content, caplog):
        """Test handling when the litellm library is not available."""
        # Arrange
        mock_read_text.return_value = sample_kb_content # Set return value even if not reached after check

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8') # Read happens before check
        assert "Cannot condense knowledge base: The 'litellm' library is not installed or failed to load." in caplog.text

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient', side_effect=ImportError("Mock LLM Client Init Error"))
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text')
    def test_condense_llm_client_init_error(self, mock_read_text, mock_is_file, MockLiteLlmClient, test_file_path, sample_kb_content, caplog):
        """Test handling when LiteLlmClient instantiation fails."""
        # Arrange
        mock_read_text.return_value = sample_kb_content

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with() # Attempted instantiation
        assert "Failed to instantiate LiteLlmClient: Mock LLM Client Init Error" in caplog.text

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text')
    def test_condense_llm_invoke_error(
        self,
        mock_read_text,
        mock_is_file,
        MockLiteLlmClient,
        mock_llm_client_instance, # Use the instance fixture
        test_file_path,
        sample_kb_content,
        caplog
    ):
        """Test handling when the LLM client's invoke method raises an error."""
        # Arrange
        mock_is_file.return_value = True
        mock_read_text.return_value = sample_kb_content
        MockLiteLlmClient.return_value = mock_llm_client_instance
        # Simulate an error during the invoke call (e.g., APIError, Timeout)
        # Using a generic Exception here as LiteLlmClient should catch specific ones
        mock_llm_client_instance.invoke.side_effect = Exception("LLM API Error")

        expected_full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=sample_kb_content)

        # Act
        # Note: The internal invoke method might log its own error. We check for the condenser's log.
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with()
        mock_llm_client_instance.invoke.assert_called_once_with(
            prompt=expected_full_prompt,
            model=CONDENSE_MODEL
        )
        # Check if the error from invoke was caught and logged by condense_knowledge_base
        # This depends on whether invoke itself raises or returns None on error.
        # Assuming invoke *raises* an exception that condense_knowledge_base catches:
        assert "An unexpected error occurred during the LLM invoke call: LLM API Error" in caplog.text
        # OR, if invoke returns None on error and logs internally:
        # assert f"LLM call failed or returned empty content for model {CONDENSE_MODEL}" in caplog.text


    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text')
    def test_condense_llm_returns_none(
        self,
        mock_read_text,
        mock_is_file,
        MockLiteLlmClient,
        mock_llm_client_instance,
        test_file_path,
        sample_kb_content,
        caplog
    ):
        """Test handling when the LLM client's invoke method returns None."""
        # Arrange
        mock_is_file.return_value = True
        mock_read_text.return_value = sample_kb_content
        MockLiteLlmClient.return_value = mock_llm_client_instance
        mock_llm_client_instance.invoke.return_value = None # Simulate LLM returning None

        expected_full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=sample_kb_content)

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with()
        mock_llm_client_instance.invoke.assert_called_once_with(
            prompt=expected_full_prompt,
            model=CONDENSE_MODEL
        )
        assert f"LLM call failed or returned empty content for model {CONDENSE_MODEL}" in caplog.text

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text')
    def test_condense_llm_returns_empty(
        self,
        mock_read_text,
        mock_is_file,
        MockLiteLlmClient,
        mock_llm_client_instance,
        test_file_path,
        sample_kb_content,
        caplog
    ):
        """Test handling when the LLM client's invoke method returns an empty string."""
        # Arrange
        mock_is_file.return_value = True
        mock_read_text.return_value = sample_kb_content
        MockLiteLlmClient.return_value = mock_llm_client_instance
        mock_llm_client_instance.invoke.return_value = "" # Simulate LLM returning empty string

        expected_full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=sample_kb_content)

        # Act
        with caplog.at_level(logging.ERROR): # Error is logged when content is falsey
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with()
        mock_llm_client_instance.invoke.assert_called_once_with(
            prompt=expected_full_prompt,
            model=CONDENSE_MODEL
        )
        assert f"LLM call failed or returned empty content for model {CONDENSE_MODEL}" in caplog.text


    # --- Output File Error Handling ---

    @patch('kb_for_prompt.organisms.condenser.LITELLM_AVAILABLE', True)
    @patch('kb_for_prompt.organisms.condenser.LiteLlmClient')
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text', side_effect=IOError("Disk full"))
    def test_condense_write_error(
        self,
        mock_write_text,
        mock_read_text,
        mock_is_file,
        MockLiteLlmClient,
        mock_llm_client_instance,
        test_file_path,
        expected_output_path,
        sample_kb_content,
        sample_condensed_content,
        caplog
    ):
        """Test handling of IOError during file writing."""
        # Arrange
        mock_is_file.return_value = True
        mock_read_text.return_value = sample_kb_content
        MockLiteLlmClient.return_value = mock_llm_client_instance
        mock_llm_client_instance.invoke.return_value = sample_condensed_content

        expected_full_prompt = CONDENSE_PROMPT.format(knowledge_base_content=sample_kb_content)

        # Act
        with caplog.at_level(logging.ERROR):
            result_path = condense_knowledge_base(test_file_path)

        # Assert
        assert result_path is None
        mock_is_file.assert_called_once_with()
        mock_read_text.assert_called_once_with(encoding='utf-8')
        MockLiteLlmClient.assert_called_once_with()
        mock_llm_client_instance.invoke.assert_called_once_with(
            prompt=expected_full_prompt,
            model=CONDENSE_MODEL
        )
        mock_write_text.assert_called_once_with(sample_condensed_content, encoding='utf-8')
        assert f"Error writing condensed file {expected_output_path}: Disk full" in caplog.text

