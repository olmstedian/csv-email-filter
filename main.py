#!/usr/bin/env python3
"""
CSV Email Filter

A Python application that extracts email addresses from CSV files, automatically
associates them with names (First Name, Last Name), and filters out suspicious emails.
Also supports converting VCF (vCard) files to CSV format.

Features:
- Extracts emails from all CSV cells
- Automatically detects and extracts First Name and Last Name columns
- Filters suspicious emails using multiple heuristics
- Converts VCF (vCard) files to CSV format
- Supports GUI and command-line interfaces
- Batch processing of multiple CSV and VCF files
- No external dependencies required

Author: CSV Email Filter Contributors
License: MIT
"""

import csv
import re
import sys
import os
from pathlib import Path
from typing import List, Set, Optional, Tuple, Dict
from dataclasses import dataclass
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


@dataclass(frozen=False)
class EmailRecord:
    """Represents an email record with name information."""
    first_name: str
    last_name: str
    email: str


def parse_vcf_file(vcf_file: str) -> List[EmailRecord]:
    """
    Parse a VCF (vCard) file and extract contact information.
    
    Args:
        vcf_file: Path to the VCF file
        
    Returns:
        List of EmailRecord objects extracted from the VCF file
    """
    email_records: Dict[str, EmailRecord] = {}
    
    try:
        with open(vcf_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
        # Split VCF file into individual vCard entries
        # VCF files use "BEGIN:VCARD" and "END:VCARD" to delimit entries
        vcard_pattern = r'BEGIN:VCARD(.*?)END:VCARD'
        vcards = re.findall(vcard_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not vcards:
            # Try to parse as single vCard or different format
            vcards = [content]
        
        for vcard in vcards:
            # Handle VCF line folding (lines starting with space or tab are continuations)
            # First, unfold lines
            lines = vcard.split('\n')
            unfolded_lines = []
            for line in lines:
                if line and (line[0] in [' ', '\t']):
                    # This is a continuation line
                    if unfolded_lines:
                        unfolded_lines[-1] += line[1:]  # Remove leading space/tab
                else:
                    unfolded_lines.append(line)
            vcard_unfolded = '\n'.join(unfolded_lines)
            
            # Extract FN (Full Name) or N (Name) field
            full_name = ""
            first_name = ""
            last_name = ""
            
            # Try to get FN (Full Name) - handle various formats
            fn_match = re.search(r'^FN(?:;.*?)?:(.*?)(?:\r?\n|$)', vcard_unfolded, re.IGNORECASE | re.MULTILINE)
            if fn_match:
                full_name = fn_match.group(1).strip()
            
            # Try to get N (Name) field - format: N:Last;First;Middle;Prefix;Suffix
            n_match = re.search(r'^N(?:;.*?)?:(.*?)(?:\r?\n|$)', vcard_unfolded, re.IGNORECASE | re.MULTILINE)
            if n_match:
                n_parts = [part.strip() for part in n_match.group(1).split(';')]
                if len(n_parts) >= 2:
                    last_name = n_parts[0] if n_parts[0] else ""
                    first_name = n_parts[1] if n_parts[1] else ""
                elif len(n_parts) == 1 and n_parts[0]:
                    last_name = n_parts[0]
            
            # If we have full_name but not first/last, try to split it
            if full_name and not first_name and not last_name:
                name_parts = full_name.split(None, 1)
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[1]
                elif len(name_parts) == 1:
                    first_name = name_parts[0]
            
            # Extract all EMAIL fields (can have multiple)
            # Handle formats like: EMAIL:user@example.com, EMAIL;TYPE=INTERNET:user@example.com, etc.
            email_pattern = r'^EMAIL(?:;.*?)?:(.*?)(?:\r?\n|$)'
            emails = re.findall(email_pattern, vcard_unfolded, re.IGNORECASE | re.MULTILINE)
            
            # Clean up emails
            cleaned_emails = []
            for email in emails:
                email = email.strip()
                # Remove any trailing semicolons, colons, or whitespace
                email = email.rstrip(';: \t')
                if email and '@' in email:
                    # Validate it looks like an email
                    if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
                        cleaned_emails.append(email)
            
            # If no emails found, skip this contact
            if not cleaned_emails:
                continue
            
            # Create records for each email
            for email in cleaned_emails:
                if email not in email_records:
                    email_records[email] = EmailRecord(first_name, last_name, email)
                else:
                    # Update names if they're empty
                    existing = email_records[email]
                    if not existing.first_name and first_name:
                        existing.first_name = first_name
                    if not existing.last_name and last_name:
                        existing.last_name = last_name
    
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{vcf_file}' not found.")
    except Exception as e:
        raise Exception(f"Error reading VCF file: {e}")
    
    # Sort by email address
    return sorted(list(email_records.values()), key=lambda x: x.email)


def extract_emails_from_text(text: str) -> Set[str]:
    """
    Extract email addresses from a text string using regex.
    
    Args:
        text: The text to search for emails
        
    Returns:
        Set of unique email addresses found
    """
    # Email regex pattern - matches standard email format
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, str(text))
    return set(emails)


def is_suspicious_email(email: str) -> bool:
    """
    Check if an email address is suspicious based on various patterns.
    Uses conservative heuristics to minimize false positives.
    
    Args:
        email: Email address to check
        
    Returns:
        True if email is suspicious, False otherwise
    """
    email_lower = email.lower()
    local_part, domain = email.split('@', 1) if '@' in email else ('', '')
    
    # Pattern 1: Very long random-looking local part (more than 40 chars, mostly alphanumeric, no vowels pattern)
    # Only flag if it's extremely long and looks like random gibberish
    if len(local_part) > 40:
        # Check if it's mostly alphanumeric without meaningful structure
        if re.match(r'^[a-z0-9]{35,}$', local_part):
            # Check if it has very few vowels (indicates random generation)
            vowel_count = sum(1 for c in local_part if c in 'aeiou')
            if vowel_count < len(local_part) * 0.15:  # Less than 15% vowels
                return True
    
    # Pattern 2: Multiple consecutive special characters (3+ in a row)
    # Allow normal patterns like firstname.lastname
    if re.search(r'\.{3,}|_{3,}|-{3,}', local_part):
        return True
    
    # Pattern 3: Excessive numbers in local part (more than 70% digits, and long)
    # Allow years and normal numbers, but flag if it's mostly random digits
    if len(local_part) > 15:
        digit_ratio = sum(1 for c in local_part if c.isdigit()) / len(local_part)
        if digit_ratio > 0.7:
            return True
    
    # Pattern 4: Suspicious domain patterns (very restrictive)
    # Only flag obviously suspicious domains
    suspicious_domain_patterns = [
        r'^[a-z0-9]{25,}\.(com|net|org)$',  # Extremely long random domain (25+ chars)
    ]
    for pattern in suspicious_domain_patterns:
        if re.match(pattern, domain):
            return True
    
    # Pattern 5: Unsubscribe/marketing patterns with very long random local parts
    suspicious_keywords = [
        'unsub', 'unsubscribe', 'remove', 'optout',
        'noreply', 'no-reply', 'donotreply',
    ]
    if any(keyword in email_lower for keyword in suspicious_keywords):
        # Only flag if combined with a very long random-looking local part
        if len(local_part) > 30 and re.match(r'^[a-z0-9]{25,}$', local_part):
            # Check for low vowel ratio (random generation indicator)
            vowel_count = sum(1 for c in local_part if c in 'aeiou')
            if vowel_count < len(local_part) * 0.15:
                return True
    
    # Pattern 6: Repeated characters (more than 8 in a row - very unusual)
    if re.search(r'(.)\1{8,}', email_lower):
        return True
    
    # Pattern 7: Base64-like pattern (very long uppercase/number mix, 30+ chars)
    # Only flag if extremely long and looks like encoded data
    if len(local_part) > 30 and re.match(r'^[A-Z0-9]{25,}$', email):
        # Check if it looks like base64 (has both letters and numbers, no lowercase)
        has_letters = bool(re.search(r'[A-Z]', local_part))
        has_numbers = bool(re.search(r'[0-9]', local_part))
        if has_letters and has_numbers:
            return True
    
    # Pattern 8: Very long local part with mixed case and numbers that looks encoded
    # Only flag if 35+ chars and has encoding-like patterns
    if len(local_part) > 35:
        # Check for patterns like: long alphanumeric string with dots/underscores separating encoded segments
        if re.match(r'^[A-Z0-9]+\.[0-9]+\.[0-9]+\.[0-9]+@', email):
            return True
    
    return False


def filter_suspicious_emails(records: List[EmailRecord]) -> tuple[List[EmailRecord], List[EmailRecord]]:
    """
    Separate email records into valid and suspicious lists.
    
    Args:
        records: List of EmailRecord objects
        
    Returns:
        Tuple of (valid_records, suspicious_records)
    """
    valid_records = []
    suspicious_records = []
    
    for record in records:
        if is_suspicious_email(record.email):
            suspicious_records.append(record)
        else:
            valid_records.append(record)
    
    return valid_records, suspicious_records


def find_emails_in_csv(input_file: str) -> List[EmailRecord]:
    """
    Read CSV file and extract email addresses with associated names.
    
    Args:
        input_file: Path to the input CSV file
        
    Returns:
        List of unique EmailRecord objects found
    """
    email_records: Dict[str, EmailRecord] = {}  # Use dict to ensure uniqueness by email
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            # Read the entire file content first
            content = file.read()
            
            # Try to detect delimiter
            delimiter = ','
            try:
                sample = content[:1024] if len(content) > 1024 else content
                if sample.strip():  # Only try if there's actual content
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
            except (csv.Error, AttributeError):
                # If delimiter detection fails, try common delimiters
                # Check which delimiter appears most frequently
                delimiters = [',', ';', '\t', '|']
                delimiter_counts = {d: content.count(d) for d in delimiters}
                if max(delimiter_counts.values()) > 0:
                    delimiter = max(delimiter_counts, key=delimiter_counts.get)
                else:
                    # No delimiter found, treat as plain text
                    delimiter = None
            
            if delimiter is None:
                # No delimiter found, extract emails from entire content
                emails = extract_emails_from_text(content)
                for email in emails:
                    if email not in email_records:
                        email_records[email] = EmailRecord("", "", email)
            else:
                # Parse as CSV
                file.seek(0)
                reader = csv.reader(file, delimiter=delimiter)
                rows = list(reader)
                
                if not rows:
                    return []
                
                # Try to find header row with column names
                header_row = None
                first_name_col = None
                last_name_col = None
                email_cols = []  # Can have multiple email columns
                
                # Check first few rows for headers
                for i, row in enumerate(rows[:5]):
                    row_lower = [cell.lower().strip() for cell in row]
                    # Look for first name column
                    if first_name_col is None:
                        for j, cell in enumerate(row_lower):
                            if 'first' in cell and 'name' in cell:
                                first_name_col = j
                                header_row = i
                                break
                    # Look for last name column
                    if last_name_col is None:
                        for j, cell in enumerate(row_lower):
                            if 'last' in cell and 'name' in cell:
                                last_name_col = j
                                if header_row is None:
                                    header_row = i
                                break
                    # Look for email columns
                    for j, cell in enumerate(row_lower):
                        if 'email' in cell or 'e-mail' in cell or 'mail' in cell:
                            if j not in email_cols:
                                email_cols.append(j)
                                if header_row is None:
                                    header_row = i
                
                # Process data rows (skip header if found)
                start_row = header_row + 1 if header_row is not None else 0
                
                for row_idx, row in enumerate(rows[start_row:], start=start_row):
                    # Extract first and last name
                    first_name = ""
                    last_name = ""
                    
                    if first_name_col is not None and first_name_col < len(row):
                        first_name = row[first_name_col].strip()
                    if last_name_col is not None and last_name_col < len(row):
                        last_name = row[last_name_col].strip()
                    
                    # Extract emails from email columns and all other cells
                    found_emails = set()
                    
                    # Check email columns first
                    for email_col in email_cols:
                        if email_col < len(row) and row[email_col].strip():
                            emails = extract_emails_from_text(row[email_col])
                            found_emails.update(emails)
                    
                    # Also check all cells for emails (in case email is in a different column)
                    for cell in row:
                        if cell and cell.strip():
                            emails = extract_emails_from_text(cell)
                            found_emails.update(emails)
                    
                    # Create records for each email found in this row
                    for email in found_emails:
                        if email not in email_records:
                            # Use names from this row
                            email_records[email] = EmailRecord(first_name, last_name, email)
                        else:
                            # If email already exists but names are empty, update them
                            existing = email_records[email]
                            if not existing.first_name and first_name:
                                existing.first_name = first_name
                            if not existing.last_name and last_name:
                                existing.last_name = last_name
    
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{input_file}' not found.")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {e}")
    
    # Sort by email address
    return sorted(list(email_records.values()), key=lambda x: x.email)


def write_emails_to_csv(records: List[EmailRecord], output_file: str):
    """
    Write email records to a CSV file with First Name, Last Name, and Email columns.
    
    Args:
        records: List of EmailRecord objects to write
        output_file: Path to the output CSV file
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(['First Name', 'Last Name', 'Email'])
            # Write each record as a row
            for record in records:
                writer.writerow([record.first_name, record.last_name, record.email])
        print(f"Successfully wrote {len(records)} email record(s) to '{output_file}'")
        return True
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return False


def process_vcf_file(input_file: str, output_file: Optional[str] = None, 
                     output_folder: Optional[str] = None, filter_suspicious: bool = True) -> bool:
    """
    Process a single VCF file and convert it to CSV format.
    
    Args:
        input_file: Path to the input VCF file
        output_file: Optional path to the output CSV file
        output_folder: Optional folder for output files
        filter_suspicious: Whether to filter out suspicious emails
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return False
    
    try:
        print(f"Reading VCF file: {input_file}")
        emails = parse_vcf_file(input_file)
        
        if not emails:
            print(f"No email addresses found in '{input_file}'.")
            return False
        
        # Filter suspicious emails if enabled
        if filter_suspicious:
            valid_emails, suspicious_emails = filter_suspicious_emails(emails)
            print(f"Found {len(emails)} total email(s): {len(valid_emails)} valid, {len(suspicious_emails)} suspicious")
        else:
            valid_emails = emails
            suspicious_emails = []
            print(f"Found {len(emails)} unique email address(es)")
        
        # Determine output directory
        if output_folder:
            output_dir = Path(output_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(input_file).parent
        
        # Determine output file paths
        input_path = Path(input_file)
        if output_file is None:
            valid_output = output_dir / f"{input_path.stem}_emails.csv"
            suspicious_output = output_dir / f"{input_path.stem}_suspicious.csv"
        else:
            output_path = Path(output_file)
            valid_output = output_dir / output_path.name
            suspicious_output = output_dir / f"{output_path.stem}_suspicious.csv"
        
        # Write valid emails
        success = write_emails_to_csv(valid_emails, str(valid_output))
        
        # Write suspicious emails if any were found
        if suspicious_emails:
            write_emails_to_csv(suspicious_emails, str(suspicious_output))
            print(f"Suspicious emails saved to: {suspicious_output}")
        
        return success
    except Exception as e:
        print(f"Error processing '{input_file}': {e}")
        return False


def process_csv_file(input_file: str, output_file: Optional[str] = None, 
                     output_folder: Optional[str] = None, filter_suspicious: bool = True) -> bool:
    """
    Process a single CSV file and extract emails.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Optional path to the output CSV file
        output_folder: Optional folder for output files
        filter_suspicious: Whether to filter out suspicious emails
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return False
    
    try:
        print(f"Reading CSV file: {input_file}")
        emails = find_emails_in_csv(input_file)
        
        if not emails:
            print(f"No email addresses found in '{input_file}'.")
            return False
        
        # Filter suspicious emails if enabled
        if filter_suspicious:
            valid_emails, suspicious_emails = filter_suspicious_emails(emails)
            print(f"Found {len(emails)} total email(s): {len(valid_emails)} valid, {len(suspicious_emails)} suspicious")
        else:
            valid_emails = emails
            suspicious_emails = []
            print(f"Found {len(emails)} unique email address(es)")
        
        # Determine output directory
        if output_folder:
            output_dir = Path(output_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(input_file).parent
        
        # Determine output file paths
        input_path = Path(input_file)
        if output_file is None:
            valid_output = output_dir / f"{input_path.stem}_emails{input_path.suffix}"
            suspicious_output = output_dir / f"{input_path.stem}_suspicious{input_path.suffix}"
        else:
            output_path = Path(output_file)
            valid_output = output_dir / output_path.name
            suspicious_output = output_dir / f"{output_path.stem}_suspicious{output_path.suffix}"
        
        # Write valid emails
        success = write_emails_to_csv(valid_emails, str(valid_output))
        
        # Write suspicious emails if any were found
        if suspicious_emails:
            write_emails_to_csv(suspicious_emails, str(suspicious_output))
            print(f"Suspicious emails saved to: {suspicious_output}")
        
        return success
    except Exception as e:
        print(f"Error processing '{input_file}': {e}")
        return False


def process_folder(folder_path: str, output_folder: Optional[str] = None, filter_suspicious: bool = True):
    """
    Process all CSV and VCF files in a folder.
    
    Args:
        folder_path: Path to the folder containing CSV and VCF files
        output_folder: Optional folder for output files (defaults to 'output_csv' folder)
        filter_suspicious: Whether to filter out suspicious emails
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"Error: Folder '{folder_path}' not found or is not a directory.")
        return
    
    csv_files = list(folder.glob("*.csv"))
    vcf_files = list(folder.glob("*.vcf"))
    
    if not csv_files and not vcf_files:
        print(f"No CSV or VCF files found in '{folder_path}'.")
        return
    
    # Use default output folder if not specified
    if output_folder is None:
        output_path = Path("output_csv")
    else:
        output_path = Path(output_folder)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    total_files = len(csv_files) + len(vcf_files)
    print(f"Found {len(csv_files)} CSV file(s) and {len(vcf_files)} VCF file(s) in '{folder_path}'")
    print(f"Output folder: {output_path}")
    print("-" * 50)
    
    processed = 0
    for csv_file in csv_files:
        if process_csv_file(str(csv_file), output_folder=str(output_path), filter_suspicious=filter_suspicious):
            processed += 1
        print("-" * 50)
    
    for vcf_file in vcf_files:
        if process_vcf_file(str(vcf_file), output_folder=str(output_path), filter_suspicious=filter_suspicious):
            processed += 1
        print("-" * 50)
    
    print(f"Processed {processed} out of {total_files} file(s) successfully.")


def select_file_gui() -> Optional[str]:
    """
    Open a file dialog to select a CSV or VCF file.
    
    Returns:
        Selected file path or None if cancelled
    """
    if not GUI_AVAILABLE:
        print("GUI not available. Please use command-line mode.")
        return None
    
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    file_path = filedialog.askopenfilename(
        title="Select CSV or VCF File",
        filetypes=[
            ("CSV files", "*.csv"),
            ("VCF files", "*.vcf"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    return file_path if file_path else None


def select_folder_gui() -> Optional[str]:
    """
    Open a folder dialog to select a folder.
    
    Returns:
        Selected folder path or None if cancelled
    """
    if not GUI_AVAILABLE:
        print("GUI not available. Please use command-line mode.")
        return None
    
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    folder_path = filedialog.askdirectory(title="Select Folder with CSV Files")
    
    root.destroy()
    return folder_path if folder_path else None


def interactive_mode():
    """
    Run the application in interactive GUI mode.
    """
    if not GUI_AVAILABLE:
        print("GUI not available. Please use command-line mode.")
        return
    
    root = tk.Tk()
    root.title("CSV Email Filter")
    root.geometry("400x200")
    
    def process_single_file():
        file_path = select_file_gui()
        if file_path:
            output_folder = "output_csv"
            file_ext = Path(file_path).suffix.lower()
            success = False
            
            if file_ext == '.vcf':
                success = process_vcf_file(file_path, output_folder=output_folder)
            else:
                success = process_csv_file(file_path, output_folder=output_folder)
            
            if success:
                messagebox.showinfo("Success", f"Emails extracted successfully!\nOutput folder: {output_folder}")
            else:
                messagebox.showerror("Error", "Failed to process file.")
    
    def process_folder_files():
        folder_path = select_folder_gui()
        if folder_path:
            output_folder = "output_csv"
            process_folder(folder_path, output_folder=output_folder)
            messagebox.showinfo("Complete", f"Folder processing complete!\nOutput folder: {output_folder}")
    
    # Create buttons
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(expand=True, fill='both')
    
    tk.Label(frame, text="CSV Email Filter", font=("Arial", 16, "bold")).pack(pady=10)
    
    tk.Button(
        frame,
        text="Select CSV/VCF File",
        command=process_single_file,
        width=25,
        height=2
    ).pack(pady=5)
    
    tk.Button(
        frame,
        text="Process Folder",
        command=process_folder_files,
        width=25,
        height=2
    ).pack(pady=5)
    
    tk.Button(
        frame,
        text="Exit",
        command=root.quit,
        width=25,
        height=1
    ).pack(pady=10)
    
    root.mainloop()


def main():
    """Main function to run the email filter."""
    # Check for special modes
    if len(sys.argv) == 1:
        # No arguments - run in interactive GUI mode
        interactive_mode()
        return
    
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        
        # Check if it's a folder
        if os.path.isdir(arg):
            process_folder(arg)
            return
        
        # Check for special flags
        if arg in ['--gui', '-g', '--interactive', '-i']:
            interactive_mode()
            return
        
        # Otherwise treat as input file - check extension
        file_ext = Path(arg).suffix.lower()
        if file_ext == '.vcf':
            process_vcf_file(arg)
        else:
            process_csv_file(arg)
        return
    
    if len(sys.argv) == 3:
        arg1, arg2 = sys.argv[1], sys.argv[2]
        
        # Check if first arg is a folder flag
        if arg1 in ['--folder', '-f', '--dir', '-d']:
            if os.path.isdir(arg2):
                process_folder(arg2)
            else:
                print(f"Error: '{arg2}' is not a valid directory.")
            return
        
        # Check if second arg is output folder
        if os.path.isdir(arg2):
            # Process single file, output to folder
            file_ext = Path(arg1).suffix.lower()
            if file_ext == '.vcf':
                process_vcf_file(arg1, output_folder=arg2)
            else:
                process_csv_file(arg1, output_folder=arg2)
            return
        
        # Both are files (input and output)
        file_ext = Path(arg1).suffix.lower()
        if file_ext == '.vcf':
            process_vcf_file(arg1, output_file=arg2)
        else:
            process_csv_file(arg1, output_file=arg2)
        return
    
    if len(sys.argv) == 4:
        if sys.argv[1] in ['--folder', '-f', '--dir', '-d']:
            folder_path = sys.argv[2]
            output_folder = sys.argv[3]
            process_folder(folder_path, output_folder=output_folder)
            return
        
        # Input file, output file, and output folder
        if os.path.isdir(sys.argv[3]):
            file_ext = Path(sys.argv[1]).suffix.lower()
            if file_ext == '.vcf':
                process_vcf_file(sys.argv[1], output_file=sys.argv[2], output_folder=sys.argv[3])
            else:
                process_csv_file(sys.argv[1], output_file=sys.argv[2], output_folder=sys.argv[3])
            return
    
    # Show usage
    print("Usage:")
    print("  python main.py                          # Interactive GUI mode")
    print("  python main.py <input.csv>              # Process single CSV file (output to output_csv/)")
    print("  python main.py <input.vcf>              # Process single VCF file (output to output_csv/)")
    print("  python main.py <input.csv> <output.csv> # Process with custom output file")
    print("  python main.py <input.vcf> <output.csv> # Convert VCF to CSV with custom output file")
    print("  python main.py <input.csv> <output_folder> # Process file, output to folder")
    print("  python main.py --folder <folder>         # Process all CSV and VCF files in folder (output to output_csv/)")
    print("  python main.py --folder <folder> <output_folder>  # Process folder with custom output")
    print("\nExamples:")
    print("  python main.py data.csv")
    print("  python main.py contacts.vcf")
    print("  python main.py data.csv emails.csv")
    print("  python main.py contacts.vcf contacts.csv")
    print("  python main.py data.csv output_csv")
    print("  python main.py --folder input_csv")
    print("  python main.py --folder input_csv output_csv")
    print("\nNote: Suspicious emails are automatically filtered and saved separately.")
    print("      Supports both CSV and VCF (vCard) file formats.")


if __name__ == "__main__":
    main()

