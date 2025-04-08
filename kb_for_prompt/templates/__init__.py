# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "rich",
#     "halo",
#     "requests",
#     "pandas",
#     "docling",
# ]
# ///

"""
Templates module for kb_for_prompt.

In atomic design, templates are page-level objects that place components into
a layout and articulate the design's underlying content structure.
Applied to this project, templates are the display components used to
present information to the user.

This module contains display templates for banners, prompts, progress indicators,
summary reports, and error messages using the Rich library.
"""

from .banner import display_banner, display_section_header
from .errors import display_error, display_exception, display_validation_error
from .progress import (
    display_completion,
    display_processing_update,
    display_progress_bar,
    display_spinner,
)
from .prompts import (
    display_main_menu,
    prompt_for_continue,
    prompt_for_directory,
    prompt_for_file,
    prompt_for_output_directory,
    prompt_for_retry,
    prompt_for_url,
)
from .summary import display_conversion_summary, display_dataframe_summary

__all__ = [
    # banner.py
    "display_banner",
    "display_section_header",
    # prompts.py
    "display_main_menu",
    "prompt_for_file",
    "prompt_for_directory",
    "prompt_for_output_directory",
    "prompt_for_url",
    "prompt_for_retry",
    "prompt_for_continue",
    # progress.py
    "display_spinner",
    "display_processing_update",
    "display_completion",
    "display_progress_bar",
    # summary.py
    "display_conversion_summary",
    "display_dataframe_summary",
    # errors.py
    "display_error",
    "display_validation_error",
    "display_exception",
]