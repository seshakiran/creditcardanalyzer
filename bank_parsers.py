import os
import pandas as pd
import datetime
import glob
import re
import streamlit as st
from abc import ABC, abstractmethod

class BankStatementParser(ABC):
    """
    Abstract base class for bank statement parsers.
    Each bank should implement its own parser by extending this class.
    """
    
    def __init__(self, bank_name):
        """Initialize the parser with the bank name."""
        self.bank_name = bank_name
    
    @abstractmethod
    def can_parse(self, file_path):
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if this parser can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, file_path):
        """
        Parse the given file into a standardized DataFrame.
        
        Args:
            file_path (str): Path to the file to parse
            
        Returns:
            pd.DataFrame: DataFrame with standardized columns
        """
        pass
    
    def find_recent_exports(self, days_back=30, download_dir=None):
        """
        Find recent statement exports in the specified directory.
        
        Args:
            days_back (int): How many days back to look for files
            download_dir (str): Directory to search, defaults to Downloads folder
            
        Returns:
            list: List of file paths to potential exports
        """
        # Use specified directory or default to Downloads
        if download_dir is None:
            download_dir = os.path.expanduser("~/Downloads")
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        # Common patterns for statement filenames
        patterns = [
            f"*{self.bank_name.lower()}*.csv",
            "*statement*.csv",
            "*transaction*.csv",
            "*.ofx",  # OFX is a common financial export format
            "*.qfx"   # QFX is Quicken's version of OFX
        ]
        
        # Find all files matching the patterns
        all_files = []
        for pattern in patterns:
            all_files.extend(glob.glob(os.path.join(download_dir, pattern)))
        
        # Filter for recent files
        recent_files = []
        for file_path in all_files:
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time >= cutoff_date:
                recent_files.append(file_path)
        
        return recent_files
    
    def standardize_dataframe(self, df, date_col, desc_col, amount_col, additional_cols=None):
        """
        Standardize a DataFrame to have consistent column names.
        
        Args:
            df (pd.DataFrame): DataFrame to standardize
            date_col (str): Name of the date column
            desc_col (str): Name of the description column
            amount_col (str): Name of the amount column
            additional_cols (dict, optional): Additional columns to include
            
        Returns:
            pd.DataFrame: Standardized DataFrame
        """
        # Create a new DataFrame with standardized columns
        result = pd.DataFrame()
        
        # Copy and rename the required columns
        result['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        result['Description'] = df[desc_col]
        
        # Handle amount - ensure it's numeric and positive values are expenses
        result['Amount'] = pd.to_numeric(df[amount_col], errors='coerce')
        
        # Add bank name as a source column
        result['Source'] = self.bank_name
        
        # Add category column (will be filled by categorization logic later)
        result['Category'] = 'Uncategorized'
        
        # Add any additional columns
        if additional_cols:
            for new_col, orig_col in additional_cols.items():
                result[new_col] = df[orig_col]
        
        # Filter out rows with invalid dates or amounts
        result = result.dropna(subset=['Date', 'Amount'])
        
        return result


class AmexStatementParser(BankStatementParser):
    """Parser for American Express statement exports."""
    
    def __init__(self):
        super().__init__("Amex")
    
    def can_parse(self, file_path):
        """Check if this is an Amex statement file."""
        try:
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.csv', '.ofx', '.qfx']:
                return False
            
            # For CSV files, check content
            if ext == '.csv':
                # Read first few lines to check format
                with open(file_path, 'r', errors='ignore') as f:
                    header = ''.join([f.readline() for _ in range(5)]).lower()
                    
                    # Check for Amex-specific patterns
                    amex_patterns = [
                        'american express',
                        'amex',
                        'date,description,amount',
                        'transaction date',
                        'reference,description,amount'
                    ]
                    
                    return any(pattern in header for pattern in amex_patterns)
            
            # For OFX/QFX files, check content
            if ext in ['.ofx', '.qfx']:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(1000).lower()  # Read first 1000 chars
                    return 'american express' in content or 'amex' in content
            
            return False
        except Exception:
            return False
    
    def parse(self, file_path):
        """Parse an Amex statement file."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.csv':
            return self._parse_csv(file_path)
        elif ext in ['.ofx', '.qfx']:
            return self._parse_ofx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _parse_csv(self, file_path):
        """Parse an Amex CSV file."""
        try:
            # Try to read the CSV file
            df = pd.read_csv(file_path)
            
            # Identify the column names
            date_col = None
            desc_col = None
            amount_col = None
            
            # Common column names in Amex exports
            date_patterns = ['date', 'transaction date', 'trans date']
            desc_patterns = ['description', 'merchant', 'vendor']
            amount_patterns = ['amount', 'debit', 'credit']
            
            # Find the matching columns
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in date_patterns):
                    date_col = col
                elif any(pattern in col_lower for pattern in desc_patterns):
                    desc_col = col
                elif any(pattern in col_lower for pattern in amount_patterns):
                    amount_col = col
            
            # Ensure required columns were found
            if not (date_col and desc_col and amount_col):
                raise ValueError("Could not identify required columns in the CSV file")
            
            # Standardize the DataFrame
            return self.standardize_dataframe(df, date_col, desc_col, amount_col)
            
        except Exception as e:
            raise ValueError(f"Error parsing Amex CSV file: {str(e)}")
    
    def _parse_ofx(self, file_path):
        """Parse an Amex OFX/QFX file."""
        try:
            # OFX files are XML-like, but not standard XML
            # This is a simplified parser that extracts transaction data
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            # Extract transactions
            transactions = []
            
            # Find all transaction blocks
            transaction_blocks = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
            
            for block in transaction_blocks:
                # Extract date (YYYYMMDD format in OFX)
                date_match = re.search(r'<DTPOSTED>(.*?)</DTPOSTED>', block)
                if date_match:
                    date_str = date_match.group(1)
                    # Convert YYYYMMDD to datetime
                    if len(date_str) >= 8:
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        date = datetime.datetime(year, month, day)
                    else:
                        continue
                else:
                    continue
                
                # Extract description
                desc_match = re.search(r'<NAME>(.*?)</NAME>', block) or re.search(r'<MEMO>(.*?)</MEMO>', block)
                description = desc_match.group(1) if desc_match else "Unknown"
                
                # Extract amount (negative for expenses in OFX)
                amount_match = re.search(r'<TRNAMT>(.*?)</TRNAMT>', block)
                if amount_match:
                    amount = float(amount_match.group(1))
                else:
                    continue
                
                transactions.append({
                    'Date': date,
                    'Description': description,
                    'Amount': amount,
                    'Source': 'Amex',
                    'Category': 'Uncategorized'
                })
            
            if transactions:
                return pd.DataFrame(transactions)
            else:
                raise ValueError("No transactions found in the OFX file")
                
        except Exception as e:
            raise ValueError(f"Error parsing Amex OFX file: {str(e)}")


class ChaseStatementParser(BankStatementParser):
    """Parser for Chase statement exports."""
    
    def __init__(self):
        super().__init__("Chase")
    
    def can_parse(self, file_path):
        """Check if this is a Chase statement file."""
        try:
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.csv', '.ofx', '.qfx']:
                return False
            
            # For CSV files, check content
            if ext == '.csv':
                # Read first few lines to check format
                with open(file_path, 'r', errors='ignore') as f:
                    header = ''.join([f.readline() for _ in range(5)]).lower()
                    
                    # Check for Chase-specific patterns
                    chase_patterns = [
                        'chase',
                        'jpmcb',
                        'jpmorgan',
                        'transaction date,post date,description,category,type,amount',
                        'details,posting date,description,amount,type,balance,check or slip #'
                    ]
                    
                    return any(pattern in header for pattern in chase_patterns)
            
            # For OFX/QFX files, check content
            if ext in ['.ofx', '.qfx']:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(1000).lower()  # Read first 1000 chars
                    return 'chase' in content or 'jpmorgan' in content
            
            return False
        except Exception:
            return False
    
    def parse(self, file_path):
        """Parse a Chase statement file."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.csv':
            return self._parse_csv(file_path)
        elif ext in ['.ofx', '.qfx']:
            return self._parse_ofx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _parse_csv(self, file_path):
        """Parse a Chase CSV file."""
        try:
            # Try to read the CSV file
            df = pd.read_csv(file_path)
            
            # Identify the column names
            date_col = None
            desc_col = None
            amount_col = None
            
            # Common column names in Chase exports
            date_patterns = ['transaction date', 'posting date', 'date']
            desc_patterns = ['description', 'details']
            amount_patterns = ['amount']
            
            # Find the matching columns
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in date_patterns):
                    date_col = col
                elif any(pattern in col_lower for pattern in desc_patterns):
                    desc_col = col
                elif any(pattern in col_lower for pattern in amount_patterns):
                    amount_col = col
            
            # Ensure required columns were found
            if not (date_col and desc_col and amount_col):
                raise ValueError("Could not identify required columns in the CSV file")
            
            # Additional columns to include
            additional_cols = {}
            if 'Category' in df.columns:
                additional_cols['OriginalCategory'] = 'Category'
            if 'Type' in df.columns:
                additional_cols['TransactionType'] = 'Type'
            
            # Standardize the DataFrame
            return self.standardize_dataframe(df, date_col, desc_col, amount_col, additional_cols)
            
        except Exception as e:
            raise ValueError(f"Error parsing Chase CSV file: {str(e)}")
    
    def _parse_ofx(self, file_path):
        """Parse a Chase OFX/QFX file."""
        # Implementation similar to Amex OFX parser
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            transactions = []
            transaction_blocks = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
            
            for block in transaction_blocks:
                date_match = re.search(r'<DTPOSTED>(.*?)</DTPOSTED>', block)
                if date_match:
                    date_str = date_match.group(1)
                    if len(date_str) >= 8:
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        date = datetime.datetime(year, month, day)
                    else:
                        continue
                else:
                    continue
                
                desc_match = re.search(r'<NAME>(.*?)</NAME>', block) or re.search(r'<MEMO>(.*?)</MEMO>', block)
                description = desc_match.group(1) if desc_match else "Unknown"
                
                amount_match = re.search(r'<TRNAMT>(.*?)</TRNAMT>', block)
                if amount_match:
                    amount = float(amount_match.group(1))
                else:
                    continue
                
                transactions.append({
                    'Date': date,
                    'Description': description,
                    'Amount': amount,
                    'Source': 'Chase',
                    'Category': 'Uncategorized'
                })
            
            if transactions:
                return pd.DataFrame(transactions)
            else:
                raise ValueError("No transactions found in the OFX file")
                
        except Exception as e:
            raise ValueError(f"Error parsing Chase OFX file: {str(e)}")


class DiscoverStatementParser(BankStatementParser):
    """Parser for Discover statement exports."""
    
    def __init__(self):
        super().__init__("Discover")
    
    def can_parse(self, file_path):
        """Check if this is a Discover statement file."""
        try:
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.csv', '.ofx', '.qfx']:
                return False
            
            # For CSV files, check content
            if ext == '.csv':
                # Read first few lines to check format
                with open(file_path, 'r', errors='ignore') as f:
                    header = ''.join([f.readline() for _ in range(5)]).lower()
                    
                    # Check for Discover-specific patterns
                    discover_patterns = [
                        'discover',
                        'trans. date,post date,description,amount,category',
                        'transaction date,posted date,description,amount,category'
                    ]
                    
                    return any(pattern in header for pattern in discover_patterns)
            
            # For OFX/QFX files, check content
            if ext in ['.ofx', '.qfx']:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(1000).lower()  # Read first 1000 chars
                    return 'discover' in content
            
            return False
        except Exception:
            return False
    
    def parse(self, file_path):
        """Parse a Discover statement file."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.csv':
            return self._parse_csv(file_path)
        elif ext in ['.ofx', '.qfx']:
            return self._parse_ofx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _parse_csv(self, file_path):
        """Parse a Discover CSV file."""
        try:
            # Try to read the CSV file
            df = pd.read_csv(file_path)
            
            # Identify the column names
            date_col = None
            desc_col = None
            amount_col = None
            
            # Common column names in Discover exports
            date_patterns = ['trans. date', 'transaction date', 'date']
            desc_patterns = ['description']
            amount_patterns = ['amount']
            
            # Find the matching columns
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in date_patterns):
                    date_col = col
                elif any(pattern in col_lower for pattern in desc_patterns):
                    desc_col = col
                elif any(pattern in col_lower for pattern in amount_patterns):
                    amount_col = col
            
            # Ensure required columns were found
            if not (date_col and desc_col and amount_col):
                raise ValueError("Could not identify required columns in the CSV file")
            
            # Additional columns to include
            additional_cols = {}
            if 'Category' in df.columns:
                additional_cols['OriginalCategory'] = 'Category'
            
            # Standardize the DataFrame
            return self.standardize_dataframe(df, date_col, desc_col, amount_col, additional_cols)
            
        except Exception as e:
            raise ValueError(f"Error parsing Discover CSV file: {str(e)}")
    
    def _parse_ofx(self, file_path):
        """Parse a Discover OFX/QFX file."""
        # Implementation similar to other OFX parsers
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            transactions = []
            transaction_blocks = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
            
            for block in transaction_blocks:
                date_match = re.search(r'<DTPOSTED>(.*?)</DTPOSTED>', block)
                if date_match:
                    date_str = date_match.group(1)
                    if len(date_str) >= 8:
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        date = datetime.datetime(year, month, day)
                    else:
                        continue
                else:
                    continue
                
                desc_match = re.search(r'<NAME>(.*?)</NAME>', block) or re.search(r'<MEMO>(.*?)</MEMO>', block)
                description = desc_match.group(1) if desc_match else "Unknown"
                
                amount_match = re.search(r'<TRNAMT>(.*?)</TRNAMT>', block)
                if amount_match:
                    amount = float(amount_match.group(1))
                else:
                    continue
                
                transactions.append({
                    'Date': date,
                    'Description': description,
                    'Amount': amount,
                    'Source': 'Discover',
                    'Category': 'Uncategorized'
                })
            
            if transactions:
                return pd.DataFrame(transactions)
            else:
                raise ValueError("No transactions found in the OFX file")
                
        except Exception as e:
            raise ValueError(f"Error parsing Discover OFX file: {str(e)}")


class GenericStatementParser(BankStatementParser):
    """Generic parser for unknown bank statement formats."""
    
    def __init__(self):
        super().__init__("Generic")
    
    def can_parse(self, file_path):
        """This parser attempts to parse any CSV file with date and amount columns."""
        try:
            # Only handle CSV files
            _, ext = os.path.splitext(file_path.lower())
            return ext == '.csv'
        except Exception:
            return False
    
    def parse(self, file_path):
        """Parse a generic CSV file by guessing column meanings."""
        try:
            # Try to read the CSV file
            df = pd.read_csv(file_path)
            
            # Try to identify date, description, and amount columns
            date_col = None
            desc_col = None
            amount_col = None
            
            # Common patterns for column names
            date_patterns = ['date', 'time', 'when', 'day']
            desc_patterns = ['description', 'desc', 'narrative', 'details', 'merchant', 'vendor', 'payee', 'memo']
            amount_patterns = ['amount', 'sum', 'value', 'price', 'cost', 'debit', 'credit', 'payment']
            
            # Check each column
            for col in df.columns:
                col_lower = col.lower()
                
                # Try to identify date column
                if not date_col and any(pattern in col_lower for pattern in date_patterns):
                    # Verify it contains dates by trying to convert
                    try:
                        pd.to_datetime(df[col], errors='raise')
                        date_col = col
                    except:
                        pass
                
                # Try to identify description column
                if not desc_col and any(pattern in col_lower for pattern in desc_patterns):
                    desc_col = col
                
                # Try to identify amount column
                if not amount_col and any(pattern in col_lower for pattern in amount_patterns):
                    # Verify it contains numeric values
                    try:
                        pd.to_numeric(df[col], errors='raise')
                        amount_col = col
                    except:
                        pass
            
            # If we couldn't identify columns by name, try by content
            if not date_col:
                for col in df.columns:
                    try:
                        pd.to_datetime(df[col], errors='raise')
                        date_col = col
                        break
                    except:
                        pass
            
            if not amount_col:
                for col in df.columns:
                    try:
                        pd.to_numeric(df[col], errors='raise')
                        amount_col = col
                        break
                    except:
                        pass
            
            # If we still don't have a description column, use the first text column
            if not desc_col:
                for col in df.columns:
                    if col != date_col and col != amount_col:
                        if df[col].dtype == 'object':  # String column
                            desc_col = col
                            break
            
            # Ensure required columns were found
            if not (date_col and desc_col and amount_col):
                raise ValueError("Could not identify required columns in the CSV file")
            
            # Standardize the DataFrame
            return self.standardize_dataframe(df, date_col, desc_col, amount_col)
            
        except Exception as e:
            raise ValueError(f"Error parsing generic CSV file: {str(e)}")


class MultiStatementParser:
    """
    Manager class that attempts to parse statement files using the appropriate parser.
    """
    
    def __init__(self):
        """Initialize with all available parsers."""
        self.parsers = [
            AmexStatementParser(),
            ChaseStatementParser(),
            DiscoverStatementParser(),
            GenericStatementParser()  # Fallback parser
        ]
    
    def parse_file(self, file_path):
        """
        Parse a statement file using the appropriate parser.
        
        Args:
            file_path (str): Path to the file to parse
            
        Returns:
            tuple: (success (bool), data (pd.DataFrame) or error message (str))
        """
        try:
            # Try each parser until one works
            for parser in self.parsers:
                if parser.can_parse(file_path):
                    st.info(f"Using {parser.bank_name} parser for {os.path.basename(file_path)}")
                    df = parser.parse(file_path)
                    return True, df
            
            # If no parser worked, try the generic parser as a last resort
            st.warning(f"No specific parser found for {os.path.basename(file_path)}. Trying generic parser.")
            generic_parser = GenericStatementParser()
            df = generic_parser.parse(file_path)
            return True, df
            
        except Exception as e:
            return False, f"Error parsing file {os.path.basename(file_path)}: {str(e)}"
    
    def parse_multiple_files(self, file_paths):
        """
        Parse multiple statement files and combine the results.
        
        Args:
            file_paths (list): List of file paths to parse
            
        Returns:
            tuple: (success (bool), data (pd.DataFrame) or error message (str))
        """
        if not file_paths:
            return False, "No files provided"
        
        all_data = []
        failed_files = []
        
        for file_path in file_paths:
            success, result = self.parse_file(file_path)
            if success:
                all_data.append(result)
            else:
                failed_files.append((os.path.basename(file_path), result))
        
        if not all_data:
            return False, f"Failed to parse any files. Errors: {failed_files}"
        
        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by date
        combined_df = combined_df.sort_values('Date')
        
        # Report any failures
        if failed_files:
            st.warning(f"Failed to parse {len(failed_files)} files: {', '.join(f[0] for f in failed_files)}")
        
        return True, combined_df
    
    def find_recent_statements(self, days_back=30):
        """
        Find recent statement files from all supported banks.
        
        Args:
            days_back (int): How many days back to look for files
            
        Returns:
            list: List of file paths to potential statement files
        """
        all_files = []
        
        for parser in self.parsers:
            files = parser.find_recent_exports(days_back=days_back)
            all_files.extend(files)
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        return all_files
