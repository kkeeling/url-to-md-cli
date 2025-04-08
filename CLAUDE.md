# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run script: `python url_to_md.py` or `uv run --script url_to_md.py`
- Install dependencies: `pip install -r requirements.txt` or `uv pip install -r requirements.txt`
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