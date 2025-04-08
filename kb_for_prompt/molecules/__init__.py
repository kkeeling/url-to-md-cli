"""
Molecules module for kb_for_prompt.

In atomic design, molecules are groups of atoms bonded together.
Applied to this project, molecules are the individual conversion functions
that combine atomic utilities to perform specific document conversion tasks.

This module contains conversion functions for URLs, Word documents (.doc/.docx),
and PDF files, transforming them into Markdown format.
"""

# Import conversion functions to make them accessible
from kb_for_prompt.molecules.url_converter import convert_url_to_markdown
from kb_for_prompt.molecules.doc_converter import convert_doc_to_markdown
from kb_for_prompt.molecules.pdf_converter import convert_pdf_to_markdown

# Export public functions
__all__ = ['convert_url_to_markdown', 'convert_doc_to_markdown', 'convert_pdf_to_markdown']