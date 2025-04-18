"""
Tests for project structure initialization.
"""

import os
import importlib.util
import sys
from pathlib import Path


def test_directory_structure():
    """Test that all required directories exist."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Check all directories exist
    assert (base_dir / "atoms").is_dir(), "atoms directory missing"
    assert (base_dir / "molecules").is_dir(), "molecules directory missing"
    assert (base_dir / "organisms").is_dir(), "organisms directory missing"
    assert (base_dir / "templates").is_dir(), "templates directory missing"
    assert (base_dir / "pages").is_dir(), "pages directory missing"
    assert (base_dir / "tests").is_dir(), "tests directory missing"


def test_init_files_exist():
    """Test that all __init__.py files exist."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Check all __init__.py files exist
    assert (base_dir / "__init__.py").is_file(), "package __init__.py missing"
    assert (base_dir / "atoms" / "__init__.py").is_file(), "atoms/__init__.py missing"
    assert (base_dir / "molecules" / "__init__.py").is_file(), "molecules/__init__.py missing"
    assert (base_dir / "organisms" / "__init__.py").is_file(), "organisms/__init__.py missing"
    assert (base_dir / "templates" / "__init__.py").is_file(), "templates/__init__.py missing"
    assert (base_dir / "pages" / "__init__.py").is_file(), "pages/__init__.py missing"


def test_init_files_content():
    """Test that __init__.py files have appropriate docstrings."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Check root __init__.py content
    with open(base_dir / "__init__.py", "r") as f:
        content = f.read()
        assert "__version__" in content, "__version__ missing in package __init__.py"
        assert "kb_for_prompt package" in content, "Docstring missing in package __init__.py"
    
    # Check atoms/__init__.py content
    with open(base_dir / "atoms" / "__init__.py", "r") as f:
        content = f.read()
        assert "Atoms module" in content, "Docstring missing in atoms/__init__.py"
    
    # Check molecules/__init__.py content
    with open(base_dir / "molecules" / "__init__.py", "r") as f:
        content = f.read()
        assert "Molecules module" in content, "Docstring missing in molecules/__init__.py"
    
    # Check organisms/__init__.py content
    with open(base_dir / "organisms" / "__init__.py", "r") as f:
        content = f.read()
        assert "Organisms module" in content, "Docstring missing in organisms/__init__.py"
    
    # Check templates/__init__.py content
    with open(base_dir / "templates" / "__init__.py", "r") as f:
        content = f.read()
        assert "Templates module" in content, "Docstring missing in templates/__init__.py"
    
    # Check pages/__init__.py content
    with open(base_dir / "pages" / "__init__.py", "r") as f:
        content = f.read()
        assert "Pages module" in content, "Docstring missing in pages/__init__.py"


def test_main_entry_point_exists():
    """Test that the main entry point exists and has proper uv script header."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entry_point = base_dir / "pages" / "kb_for_prompt.py"
    
    assert entry_point.is_file(), "kb_for_prompt.py missing"
    
    with open(entry_point, "r") as f:
        content = f.read()
        assert "# /// script" in content, "uv script header missing"
        assert "requires-python" in content, "requires-python missing in uv script header"
        assert "dependencies" in content, "dependencies missing in uv script header"
        assert "docling" in content, "docling missing in dependencies"
        assert "click" in content, "click missing in dependencies"
        assert "rich" in content, "rich missing in dependencies"
        assert "if __name__ == \"__main__\":" in content, "Entry point missing"


def test_main_entry_point_has_main_function():
    """Test that the main entry point has a main function."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entry_point = base_dir / "pages" / "kb_for_prompt.py"
    
    with open(entry_point, "r") as f:
        content = f.read()
        assert "def main(" in content, "main function definition missing in kb_for_prompt.py"
        assert "if __name__ == \"__main__\":" in content, "Entry point guard missing"
        assert "sys.exit(main())" in content, "main() call missing in entry point"
    

def test_readme_exists():
    """Test that README.md exists and has appropriate content."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    readme_path = base_dir / "README.md"
    
    assert readme_path.is_file(), "README.md missing"
    
    with open(readme_path, "r") as f:
        content = f.read()
        assert "# KB for Prompt" in content, "Title missing in README.md"
        assert "Installation" in content, "Installation section missing in README.md"
        assert "Usage" in content, "Usage section missing in README.md"
        assert "Project Structure" in content, "Project Structure section missing in README.md"