# CSV Email Filter

A Python application that extracts email addresses from CSV files and VCF (vCard) files, automatically associates them with names, and filters out suspicious emails. Perfect for cleaning contact lists, extracting email addresses from exports, converting vCard contacts to CSV, and identifying potentially problematic email addresses.

## Features

- ✅ Extracts email addresses from all cells in a CSV file
- ✅ **VCF (vCard) to CSV conversion** - Converts VCF contact files to CSV format
- ✅ **Automatic name extraction** - Associates First Name and Last Name with emails
- ✅ **Suspicious email filtering** - Identifies and filters out suspicious emails using regex patterns
- ✅ **Separate output files** - Valid emails and suspicious emails saved to different files
- ✅ **Interactive GUI mode** - Easy-to-use graphical interface
- ✅ **Batch processing** - Process multiple CSV and VCF files at once
- ✅ **No dependencies** - Uses only Python standard library
- ✅ **Smart CSV parsing** - Automatically detects delimiters and column headers

## Usage

### Interactive GUI Mode (Recommended)

Run without arguments to open the GUI:

```bash
python main.py
```

This opens a window with two options:

- **Select CSV/VCF File** - Choose a single CSV or VCF file to process
- **Process Folder** - Process all CSV and VCF files in a selected folder

### Command Line Usage

#### Process Single CSV File

```bash
python main.py input.csv
```

This will create files in the `output_csv/` folder:

- `input_emails.csv` - Valid email addresses
- `input_suspicious.csv` - Suspicious email addresses (if any found)

#### Convert VCF to CSV

```bash
python main.py contacts.vcf
```

This will convert the VCF file to CSV format and create files in the `output_csv/` folder:

- `contacts_emails.csv` - Valid email addresses extracted from VCF
- `contacts_suspicious.csv` - Suspicious email addresses (if any found)

#### Specify Output File

```bash
python main.py input.csv output.csv
python main.py contacts.vcf contacts.csv
```

#### Process All CSV and VCF Files in a Folder

```bash
python main.py --folder input_csv
```

This processes all `.csv` and `.vcf` files in the `input_csv` folder and creates corresponding files in the `output_csv/` folder:

- `*_emails.csv` - Valid email addresses for each file
- `*_suspicious.csv` - Suspicious email addresses for each file (if any found)

#### Process Folder with Custom Output Directory

```bash
python main.py --folder input_csv output_csv
```

This processes all CSV and VCF files from `input_csv` and saves the results to `output_csv` folder.

### Using the Default Folders

1. Place your CSV and/or VCF files in the `input_csv` folder
2. Run: `python main.py --folder input_csv`
3. Find the extracted emails in the `output_csv` folder:
   - Valid emails: `*_emails.csv`
   - Suspicious emails: `*_suspicious.csv`

## Examples

### CSV File Example

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

### VCF File Example

Given an input VCF file `contacts.vcf`:

```
BEGIN:VCARD
VERSION:3.0
FN:John Doe
N:Doe;John;;;
EMAIL:john@example.com
END:VCARD
BEGIN:VCARD
VERSION:3.0
FN:Jane Smith
N:Smith;Jane;;;
EMAIL:jane.smith@company.com
END:VCARD
```

Running:

```bash
python main.py contacts.vcf contacts.csv
```

Will create `contacts.csv`:

```csv
First Name,Last Name,Email
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

### For CSV Files:
1. Reads the input CSV file
2. **Extracts First Name and Last Name** from CSV columns (automatically detects column headers)
3. Scans all cells for email addresses using regex pattern matching
4. **Associates names with emails** from the same row
5. Collects unique email addresses (by email, preserving name information)
6. **Filters suspicious emails** using multiple regex patterns
7. Writes valid emails to `*_emails.csv` and suspicious emails to `*_suspicious.csv` in the `output_csv/` folder

### For VCF Files:
1. Reads the input VCF (vCard) file
2. Parses vCard entries (delimited by BEGIN:VCARD and END:VCARD)
3. **Extracts names** from FN (Full Name) and N (Name) fields
4. **Extracts email addresses** from EMAIL fields
5. Associates names with emails from the same vCard entry
6. Collects unique email addresses (by email, preserving name information)
7. **Filters suspicious emails** using multiple regex patterns:
   - Very long random-looking local parts
   - Excessive numbers or special characters
   - Suspicious domain patterns
   - Automated/unsubscribe patterns
   - Repeated characters
8. Writes valid emails to `*_emails.csv` and suspicious emails to `*_suspicious.csv` in the `output_csv/` folder

### Output Format:
All output CSV files have three columns: **First Name, Last Name, Email**

## Notes

### CSV Files:
- Email addresses are extracted from any cell in the CSV, not just specific columns
- **First Name and Last Name** are automatically extracted from CSV columns (looks for "First Name" and "Last Name" column headers)
- If names are not found in the CSV, they will be empty in the output

### VCF Files:
- Supports standard vCard format (VERSION:2.1, VERSION:3.0, etc.)
- Extracts names from FN (Full Name) and N (Name) fields
- Extracts all EMAIL fields from each vCard entry
- If a vCard has multiple emails, each email gets its own row in the output
- If names are not found in the VCF, they will be empty in the output

### General:
- The output contains unique emails only (duplicates are removed, keeping the first occurrence's name information)
- Emails are sorted alphabetically in the output
- **Output format**: All output CSV files have three columns: `First Name`, `Last Name`, `Email`
- **Suspicious email detection** uses multiple heuristics to identify potentially problematic emails (spam, automated, random-generated)
- Valid and suspicious emails are saved to separate files for easy review
- By default, all output files are saved to the `output_csv/` folder
- When processing folders, each file gets its own output files with `_emails` and `_suspicious` suffixes
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
