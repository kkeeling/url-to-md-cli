# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run script: `uv run url_to_md.py`
- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest test_name`
- Install dependencies: `uv pip install -r requirements.txt`
- Lint: `flake8 url_to_md.py`
- Type check: `mypy url_to_md.py`

## Code Style
- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Include docstrings for all functions and classes
- Group imports: stdlib first, third-party second, local imports third
- Error handling: Use try/except blocks with specific exceptions
- Function length: Keep functions focused and concise
- Variable names: Use descriptive, lowercase names with underscores
- Constants: Define at module level in UPPERCASE

## Project Structure
- Single-file script with CLI interface via click
- Uses ThreadPoolExecutor for concurrent processing
- Rich and Halo libraries for console output
- Exception handling through custom ConversionError class

## Must-Follow Instructions
- Always read the table of contents for the documentation at `specs/docs/toc.md` to understand what documentation exists and is relevant to the task at hand.

## Testing
- Since we are using 'uv', we do not want to install dependencies globally. Run the tests with `uv run` and if you still get errors about dependencies, add the following header to the test files with the appropriate dependencies:
```
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
```

## Dependencies
- You should never need to install dependencies. If a dependency is missing, add it to the `///script` header