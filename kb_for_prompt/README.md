# KB for Prompt

A CLI tool that converts online and local documents (URLs, Word, and PDF files) into Markdown files using the docling library.

## Features

- Supports multiple input types:
  - URLs
  - Word documents (.doc/.docx)
  - PDF files
- Provides two conversion modes:
  - Batch conversion (using a CSV file with a mix of URLs and file paths)
  - Single item conversion
- Interactive menu for user-friendly operation
- Automatic input type detection
- Validation of local file inputs
- Error handling with retries
- Detailed conversion summary

## Installation

### Requirements

- Python >= 3.12
- uv (optional but recommended)

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/kb-for-prompt.git
cd kb-for-prompt

# Run with uv
uv run --script kb_for_prompt/pages/kb_for_prompt.py
```

### Traditional Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kb-for-prompt.git
cd kb-for-prompt

# Install dependencies
pip install -r requirements.txt

# Run the application
python kb_for_prompt/pages/kb_for_prompt.py
```

## Usage

The application provides an interactive menu to guide you through the conversion process. Here are the basic operations:

### Batch Conversion

1. Prepare a CSV file with URLs and/or local file paths
2. Select "Batch conversion mode" from the main menu
3. Enter the path to your CSV file
4. Specify the output directory
5. The application will process all inputs and generate markdown files in the output directory

### Single Item Conversion

1. Select "Single item conversion mode" from the main menu
2. Enter a URL or local file path
3. Enter an output file name (or accept the default)
4. Enter an output directory (or accept the default)
5. The application will convert the input and generate a markdown file

## Project Structure

The project follows atomic design principles for clear separation of concerns:

- **atoms**: Basic utility functions (file path resolution, validation, etc.)
- **molecules**: Individual conversion functions (URL, Word, PDF)
- **organisms**: Orchestration of conversion processes (batch, single item)
- **templates**: Display components for the CLI interface
- **pages**: Main entry points for the application

## Development

### Code Style

Follow PEP 8 guidelines and maintain clear separation between different atomic design layers.

### Testing

```bash
# Run tests
pytest
```

## License

MIT

## Acknowledgments

- docling library for document conversion
- Rich library for beautiful terminal interfaces