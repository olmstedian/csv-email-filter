# CSV Email Filter

A Python application that extracts email addresses from CSV files, automatically associates them with names, and filters out suspicious emails. Perfect for cleaning contact lists, extracting email addresses from exports, and identifying potentially problematic email addresses.

## Features

- ✅ Extracts email addresses from all cells in a CSV file
- ✅ **Automatic name extraction** - Associates First Name and Last Name with emails
- ✅ **Suspicious email filtering** - Identifies and filters out suspicious emails using regex patterns
- ✅ **Separate output files** - Valid emails and suspicious emails saved to different files
- ✅ **Interactive GUI mode** - Easy-to-use graphical interface
- ✅ **Batch processing** - Process multiple CSV files at once
- ✅ **No dependencies** - Uses only Python standard library
- ✅ **Smart CSV parsing** - Automatically detects delimiters and column headers

## Usage

### Interactive GUI Mode (Recommended)

Run without arguments to open the GUI:

```bash
python main.py
```

This opens a window with two options:

- **Select CSV File** - Choose a single file to process
- **Process Folder** - Process all CSV files in a selected folder

### Command Line Usage

#### Process Single File

```bash
python main.py input.csv
```

This will create files in the `output_csv/` folder:

- `input_emails.csv` - Valid email addresses
- `input_suspicious.csv` - Suspicious email addresses (if any found)

#### Specify Output File

```bash
python main.py input.csv output.csv
```

#### Process All CSV Files in a Folder

```bash
python main.py --folder input_csv
```

This processes all `.csv` files in the `input_csv` folder and creates corresponding files in the `output_csv/` folder:

- `*_emails.csv` - Valid email addresses for each file
- `*_suspicious.csv` - Suspicious email addresses for each file (if any found)

#### Process Folder with Custom Output Directory

```bash
python main.py --folder input_csv output_csv
```

This processes all CSV files from `input_csv` and saves the results to `output_csv` folder.

### Using the Default Folders

1. Place your CSV files in the `input_csv` folder
2. Run: `python main.py --folder input_csv`
3. Find the extracted emails in the `output_csv` folder:
   - Valid emails: `*_emails.csv`
   - Suspicious emails: `*_suspicious.csv`

## Example

Given an input CSV file `data.csv`:

```csv
name,contact,notes
John Doe,john@example.com,Contact via email
Jane Smith,jane.smith@company.com,Preferred contact
Bob,info@test.org,General inquiries
```

Running:

```bash
python main.py data.csv emails.csv
```

Will create `emails.csv`:

```csv
First Name,Last Name,Email
Bob,,info@test.org
Jane,Smith,jane.smith@company.com
John,Doe,john@example.com
```

## Installation

No installation required! Just clone the repository and run:

```bash
git clone https://github.com/olmstedian/csv-email-filter.git
cd csv-email-filter
python main.py
```

### Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)
- tkinter (for GUI mode) - usually included with Python, but may need separate installation on Linux:
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - Fedora: `sudo dnf install python3-tkinter`
  - Arch: `sudo pacman -S tk`

## How It Works

1. Reads the input CSV file
2. **Extracts First Name and Last Name** from CSV columns (automatically detects column headers)
3. Scans all cells for email addresses using regex pattern matching
4. **Associates names with emails** from the same row
5. Collects unique email addresses (by email, preserving name information)
6. **Filters suspicious emails** using multiple regex patterns:
   - Very long random-looking local parts
   - Excessive numbers or special characters
   - Suspicious domain patterns
   - Automated/unsubscribe patterns
   - Repeated characters
7. Writes valid emails to `*_emails.csv` and suspicious emails to `*_suspicious.csv` in the `output_csv/` folder
8. **Output format**: CSV with three columns: First Name, Last Name, Email

## Notes

- Email addresses are extracted from any cell in the CSV, not just specific columns
- **First Name and Last Name** are automatically extracted from CSV columns (looks for "First Name" and "Last Name" column headers)
- If names are not found in the CSV, they will be empty in the output
- The output contains unique emails only (duplicates are removed, keeping the first occurrence's name information)
- Emails are sorted alphabetically in the output
- **Output format**: All output CSV files have three columns: `First Name`, `Last Name`, `Email`
- **Suspicious email detection** uses multiple heuristics to identify potentially problematic emails (spam, automated, random-generated)
- Valid and suspicious emails are saved to separate files for easy review
- By default, all output files are saved to the `output_csv/` folder
- When processing folders, each CSV file gets its own output files with `_emails` and `_suspicious` suffixes
- GUI mode requires tkinter (usually included with Python, but may need separate installation on Linux)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python standard library only
- Uses regex for email pattern matching
- GUI built with tkinter
