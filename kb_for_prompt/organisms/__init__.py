# /// script
# requires-python = "==3.12"
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
Organisms module for kb_for_prompt.

In atomic design, organisms are groups of molecules joined together to form
a relatively complex, distinct section of an interface.
Applied to this project, organisms are the components that orchestrate
conversion processes and user interactions.

This module contains the interactive menu system, single item converter,
and batch converter functionalities that coordinate the conversion workflow.
"""

from .menu_system import MenuSystem, MenuState
from .single_item_converter import SingleItemConverter

__all__ = [
    "MenuSystem",
    "MenuState",
    "SingleItemConverter",
]