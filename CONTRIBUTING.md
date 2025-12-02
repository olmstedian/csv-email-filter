# Contributing to CSV Email Filter

Thank you for your interest in contributing to CSV Email Filter!

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the bug
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Python version and operating system
- Sample CSV or VCF file (if applicable, anonymize sensitive data)

### Suggesting Features

Feature suggestions are welcome! Please open an issue describing:
- The feature you'd like to see
- Why it would be useful
- How it might work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test your changes thoroughly
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add feature: description'`)
7. Push to your branch (`git push origin feature/your-feature-name`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small
- Write clear docstrings

### Testing

Before submitting a PR, please:
- Test with various CSV formats
- Test with VCF (vCard) files if making changes to file processing
- Test with edge cases (empty files, malformed CSVs/VCFs, etc.)
- Ensure no linting errors
- Test both GUI and command-line modes

## Development Setup

1. Clone the repository
2. No virtual environment required (uses only standard library)
3. Run `python main.py` to test

## Questions?

Feel free to open an issue for any questions or discussions!

