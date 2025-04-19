# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pytest",
#     "pytest-mock",
#     "litellm",
# ]
# ///

import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
import sys
from typing import Optional, List, Dict, Any, Type

# --- Test Setup: Handle potential ImportError for litellm ---

# Attempt to import litellm and its exceptions
try:
    import litellm
    # Define the specific exceptions we expect the client to handle
    from litellm.exceptions import APIError, RateLimitError, ServiceUnavailableError, Timeout, AuthenticationError, BadRequestError
    LITELLM_AVAILABLE = True

except ImportError:
    LITELLM_AVAILABLE = False
    # Define dummy exceptions if litellm is not installed for the tests to parse
    # These won't be used directly in the patched tests if litellm is missing,
    # but are needed for the file to be syntactically valid if the client
    # explicitly imports them (which it does).
    class APIError(Exception): pass
    class RateLimitError(Exception): pass
    class ServiceUnavailableError(Exception): pass
    class Timeout(Exception): pass
    class AuthenticationError(Exception): pass
    class BadRequestError(Exception): pass

# Conditionally import the client *after* potentially defining dummy exceptions
# This ensures the client module can be imported even if litellm is missing,
# allowing us to test the ImportError handling during instantiation.
try:
    from kb_for_prompt.organisms.llm_client import LiteLlmClient
except ImportError as e:
    # If the client itself fails to import (e.g., due to syntax errors), re-raise
    if "litellm" not in str(e): # Check if the import error is *not* about litellm
         raise e
    # If the import error *is* about litellm, define a dummy client for test collection
    # This dummy client will raise the ImportError during __init__ if LITELLM_AVAILABLE is False
    class LiteLlmClient:
        def __init__(self, api_key: Optional[str] = None):
             if not LITELLM_AVAILABLE:
                 raise ImportError("The 'litellm' library is required to use LiteLlmClient. Please install it.")
             self.api_key = api_key
             logging.info("Dummy LiteLlmClient initialized.") # Add log for clarity
        def invoke(self, prompt: str, model: str) -> Optional[str]:
             # This dummy invoke won't be called if LITELLM_AVAILABLE is False
             # due to the skipif marker or the __init__ check.
             logging.warning("Dummy LiteLlmClient invoke called.") # Add log for clarity
             return None


# --- Mock Response Structure ---

# Helper function to create a mock litellm response object
def create_mock_litellm_response(content: Optional[str]) -> MagicMock:
    """Creates a mock litellm completion response object."""
    mock_response = MagicMock()
    if content is not None:
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = content
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
    else:
        # Simulate cases where the structure might be different or empty
        mock_response.choices = [] # Or None, or missing .message, etc.
    return mock_response

# --- Test Class for LiteLlmClient ---

# Only run these tests if litellm is actually installed
@pytest.mark.skipif(not LITELLM_AVAILABLE, reason="litellm library not installed")
class TestLiteLlmClientWithLiteLLM:
    """Tests for the LiteLlmClient class when litellm is available."""

    @pytest.fixture(autouse=True) # Apply mock to all tests in this class
    def mock_litellm_completion(self):
        """Fixture to mock the litellm.completion function."""
        # Important: Patch the correct location where 'completion' is looked up
        # in the module under test.
        with patch('kb_for_prompt.organisms.llm_client.completion') as mock_completion:
            yield mock_completion

    # Test initialization
    def test_init_with_litellm(self):
        """Test initialization when litellm is available."""
        client = LiteLlmClient()
        assert client.api_key is None
        client_with_key = LiteLlmClient(api_key="test-key")
        assert client_with_key.api_key == "test-key"

    # Test successful invocation
    def test_invoke_success(self, mock_litellm_completion):
        """Test successful invocation returns content."""
        prompt = "What is the weather?"
        model = "gemini/gemini-pro"
        expected_content = "The weather is sunny."
        api_key = "my-api-key"

        mock_response = create_mock_litellm_response(expected_content)
        mock_litellm_completion.return_value = mock_response

        client = LiteLlmClient(api_key=api_key)
        result = client.invoke(prompt, model)

        assert result == expected_content
        mock_litellm_completion.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )

    def test_invoke_success_no_api_key(self, mock_litellm_completion):
        """Test successful invocation without providing an API key."""
        prompt = "Another prompt"
        model = "gpt-4"
        expected_content = "Another response"

        mock_response = create_mock_litellm_response(expected_content)
        mock_litellm_completion.return_value = mock_response

        client = LiteLlmClient() # No API key
        result = client.invoke(prompt, model)

        assert result == expected_content
        # Ensure api_key is not passed if not provided during init
        mock_litellm_completion.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}]
            # No api_key argument expected here
        )

    # --- Individual Exception Handling Tests ---

    def test_api_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.APIError."""
        error_message = "Mock API Error"
        # Patch the specific exception class *within the client module's namespace*
        with patch('kb_for_prompt.organisms.llm_client.APIError', create=True) as MockAPIError:
            # Create a mock instance that behaves like the exception
            mock_exception_instance = Exception(error_message) # Use base Exception for simplicity
            MockAPIError.side_effect = mock_exception_instance # Raise the base exception when APIError is called
            mock_litellm_completion.side_effect = MockAPIError # Make completion raise the *mocked* APIError

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower()
            assert error_message in caplog.text

    def test_authentication_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.AuthenticationError."""
        error_message = "Mock Authentication Error"
        with patch('kb_for_prompt.organisms.llm_client.AuthenticationError', create=True) as MockAuthError:
            mock_exception_instance = Exception(error_message)
            MockAuthError.side_effect = mock_exception_instance
            mock_litellm_completion.side_effect = MockAuthError

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower() # Client logs generic "API error"
            assert error_message in caplog.text

    def test_rate_limit_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.RateLimitError."""
        error_message = "Mock Rate Limit Error"
        with patch('kb_for_prompt.organisms.llm_client.RateLimitError', create=True) as MockRateLimitError:
            mock_exception_instance = Exception(error_message)
            MockRateLimitError.side_effect = mock_exception_instance
            mock_litellm_completion.side_effect = MockRateLimitError

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower()
            assert error_message in caplog.text

    def test_service_unavailable_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.ServiceUnavailableError."""
        error_message = "Mock Service Unavailable Error"
        with patch('kb_for_prompt.organisms.llm_client.ServiceUnavailableError', create=True) as MockServiceUnavailableError:
            mock_exception_instance = Exception(error_message)
            MockServiceUnavailableError.side_effect = mock_exception_instance
            mock_litellm_completion.side_effect = MockServiceUnavailableError

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower()
            assert error_message in caplog.text

    def test_timeout_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.Timeout."""
        error_message = "Mock Timeout Error"
        with patch('kb_for_prompt.organisms.llm_client.Timeout', create=True) as MockTimeout:
            mock_exception_instance = Exception(error_message)
            MockTimeout.side_effect = mock_exception_instance
            mock_litellm_completion.side_effect = MockTimeout

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower()
            assert error_message in caplog.text

    def test_bad_request_error_handling(self, mock_litellm_completion, caplog):
        """Test handling of litellm.exceptions.BadRequestError."""
        error_message = "Mock Bad Request Error"
        with patch('kb_for_prompt.organisms.llm_client.BadRequestError', create=True) as MockBadRequestError:
            mock_exception_instance = Exception(error_message)
            MockBadRequestError.side_effect = mock_exception_instance
            mock_litellm_completion.side_effect = MockBadRequestError

            client = LiteLlmClient()
            with caplog.at_level(logging.ERROR):
                result = client.invoke("prompt", "model")

            assert result is None
            mock_litellm_completion.assert_called_once()
            assert "api error" in caplog.text.lower()
            assert error_message in caplog.text

    def test_generic_exception_handling(self, mock_litellm_completion, caplog):
        """Test handling of unexpected generic exceptions."""
        error_message = "Some unexpected error"
        mock_litellm_completion.side_effect = Exception(error_message)

        client = LiteLlmClient()
        with caplog.at_level(logging.ERROR):
            result = client.invoke("prompt", "model")

        assert result is None
        mock_litellm_completion.assert_called_once()
        assert "unexpected error" in caplog.text.lower()
        assert error_message in caplog.text


    # Test response handling
    @pytest.mark.parametrize(
        "malformed_response_setup",
        [
            # Case 1: Response object is None
            lambda: None,
            # Case 2: Response object has no 'choices' attribute (or it's None)
            lambda: MagicMock(choices=None),
            # Case 3: Response.choices is an empty list
            lambda: MagicMock(choices=[]),
            # Case 4: Choice object has no 'message' attribute (or it's None)
            lambda: MagicMock(choices=[MagicMock(message=None)]),
            # Case 5: Message object has no 'content' attribute (or it's None)
            lambda: MagicMock(choices=[MagicMock(message=MagicMock(content=None))]),
            # Case 6: Message object is None (same effective check as Case 4)
            # lambda: MagicMock(choices=[MagicMock(message=None)]), # Redundant with Case 4
            # Case 7: Choice object itself is None in the list
            lambda: MagicMock(choices=[None]),
        ],
        ids=[
            "NoneResponse",
            "NoChoicesAttr",
            "EmptyChoicesList",
            "NoMessageAttr",
            "NoContentAttr",
            # "NoneMessageObject", # Covered by NoMessageAttr
            "NoneChoiceObject"
        ]
    )
    def test_response_parsing_malformed(self, mock_litellm_completion, malformed_response_setup, caplog):
        """Test handling of various malformed/unexpected responses."""
        prompt = "Generate something"
        model = "test-model"

        mock_response = malformed_response_setup()
        mock_litellm_completion.return_value = mock_response

        client = LiteLlmClient()

        with caplog.at_level(logging.ERROR):
            result = client.invoke(prompt, model)

        assert result is None # Expect None for malformed responses
        mock_litellm_completion.assert_called_once()
        # Check that an error was logged about the unexpected structure
        assert len(caplog.records) >= 1 # Allow for potential multiple logs in edge cases
        assert "returned an unexpected response structure" in caplog.text.lower()


# --- Test LiteLLM Not Installed Scenario ---

# This test runs only if litellm is *not* available
@pytest.mark.skipif(LITELLM_AVAILABLE, reason="litellm library IS installed")
def test_init_without_litellm():
    """Test initialization raises ImportError when litellm is not available."""
    with pytest.raises(ImportError, match="The 'litellm' library is required"):
        # Use the potentially dummy LiteLlmClient defined earlier if litellm is missing
        LiteLlmClient()
