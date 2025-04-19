import unittest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import xml.etree.ElementTree as ET

# Assuming llm_generator.py is in the same directory or accessible via PYTHONPATH
from llm_generator import LlmGenerator

# Suppress logging messages during tests for cleaner output
logging.disable(logging.CRITICAL)

class TestLlmGenerator(unittest.TestCase):

    def setUp(self):
        """Set up common test resources."""
        self.mock_llm_client = MagicMock()
        self.generator = LlmGenerator(llm_client=self.mock_llm_client)
        self.test_output_dir = Path("./test_docs")

        # Sample XML data returned by scan_and_build_xml
        self.sample_xml_data = """
<documents>
  <document path="test_docs/intro.md">
    <content>Introduction content.</content>
  </document>
  <document path="test_docs/usage/guide.md">
    <content>Usage guide content.</content>
  </document>
</documents>
        """.strip()

        # Sample XML data with no documents
        self.empty_xml_data = "<documents></documents>"
        self.malformed_xml_data = "<documents><document path='test.md'>" # Missing closing tag

        # Sample successful LLM response
        self.expected_toc_md = """
# Documentation Overview

## Introduction
- [Introduction](test_docs/intro.md)

## Usage
- [Usage Guide](test_docs/usage/guide.md)
        """.strip()

    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_success(self, mock_scan):
        """Test successful TOC generation."""
        # Configure mocks
        mock_scan.return_value = self.sample_xml_data
        self.mock_llm_client.invoke.return_value = self.expected_toc_md

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_called_once()
        # Check prompt argument passed to invoke
        call_args, call_kwargs = self.mock_llm_client.invoke.call_args
        prompt_arg = call_args[0]
        self.assertIn("You are a documentation indexing assistant.", prompt_arg)
        self.assertIn(self.sample_xml_data, prompt_arg)
        # Check model argument passed to invoke
        self.assertEqual(call_kwargs.get('model'), "gemini/gemini-2.5-pro-preview-03-25")
        # Check result
        self.assertEqual(toc, self.expected_toc_md)

    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_no_documents_in_xml(self, mock_scan):
        """Test TOC generation when scan returns XML with no document elements."""
        # Configure mocks
        mock_scan.return_value = self.empty_xml_data

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_not_called() # LLM should not be called
        self.assertIsNone(toc)

    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_empty_xml_string(self, mock_scan):
        """Test TOC generation when scan returns an empty string."""
        # Configure mocks
        mock_scan.return_value = "" # Simulate empty result from scan

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_not_called() # LLM should not be called
        self.assertIsNone(toc)

    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_malformed_xml(self, mock_scan):
        """Test TOC generation when scan returns malformed XML."""
        # Configure mocks
        mock_scan.return_value = self.malformed_xml_data

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_not_called() # LLM should not be called
        self.assertIsNone(toc)


    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_llm_error(self, mock_scan):
        """Test TOC generation when the LLM client raises an error."""
        # Configure mocks
        mock_scan.return_value = self.sample_xml_data
        self.mock_llm_client.invoke.side_effect = Exception("LLM API Error")

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_called_once() # Ensure it was called
        self.assertIsNone(toc) # Should return None on error

    @patch('llm_generator.LlmGenerator.scan_and_build_xml')
    def test_generate_toc_scan_error(self, mock_scan):
        """Test TOC generation when scan_and_build_xml raises an error."""
        # Configure mocks
        mock_scan.side_effect = Exception("Failed to scan directory")

        # Call the method
        toc = self.generator.generate_toc(self.test_output_dir)

        # Assertions
        mock_scan.assert_called_once_with(self.test_output_dir)
        self.mock_llm_client.invoke.assert_not_called() # LLM should not be called
        self.assertIsNone(toc)

    def test_generate_toc_no_llm_client(self):
        """Test TOC generation when no LLM client is provided."""
        generator_no_client = LlmGenerator(llm_client=None)

        # Call the method
        toc = generator_no_client.generate_toc(self.test_output_dir)

        # Assertions
        self.assertIsNone(toc)
        # No mocks to check as scan/invoke shouldn't be called if client is None

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
