# /// script
# requires-python = ">=3.11"
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
batch converter functionalities, and LLM XML generator that coordinate
the application's workflows.
"""
import logging

# Import LlmGenerator directly as it has fewer dependencies
from .llm_generator import LlmGenerator

# Initialize __all__ with components that are always expected
__all__ = [
    "LlmGenerator",
]

# Conditionally import other components that might have heavier dependencies
try:
    from .menu_system import MenuSystem, MenuState
    from .single_item_converter import SingleItemConverter
    from .batch_converter import BatchConverter

    # Add successfully imported components to __all__
    __all__.extend([
        "MenuSystem",
        "MenuState",
        "SingleItemConverter",
        "BatchConverter",
    ])

except ImportError as e:
    logging.warning(f"Could not import some organism components: {e}. "
                    "Functionality may be limited. Check dependencies (e.g., docling, pandas).")
    # Define placeholders if needed, or just let them be undefined
    # depending on how the rest of the application handles missing components.
    # For now, we just log a warning and don't add them to __all__.
    pass

# Ensure __all__ has unique entries (though unlikely to have duplicates here)
__all__ = sorted(list(set(__all__)))
