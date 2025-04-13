import os
import pandas as pd
import datetime
import glob
import re
import streamlit as st

class AmexExportParser:
    """
    Parser for American Express statement exports.
    This allows users to manually download their statements from American Express
    and then have them automatically processed by the application.
    """
    
    def __init__(self, export_directory=None):
        """Initialize the parser with the directory to scan for exports."""
        self.export_directory = export_directory or os.path.expanduser("~/Downloads")
    
    def find_recent_exports(self, days_back=7):
        """
        Find recent American Express exports in the specified directory.
        
        Args:
            days_back (int): How many days back to look for files
            
        Returns:
            list: List of file paths to potential Amex exports
        """
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        # Common patterns for Amex export filenames
        patterns = [
            "*amex*.csv",
            "*american*express*.csv",
            "*statement*.csv",
            "*transaction*.csv",
            "*.ofx",  # OFX is a common financial export format
            "*.qfx"   # QFX is Quicken's version of OFX
        ]
        
        # Find all files matching the patterns
        all_files = []
        for pattern in patterns:
            all_files.extend(glob.glob(os.path.join(self.export_directory, pattern)))
        
        # Filter for recent files
        recent_files = []
        for file_path in all_files:
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time >= cutoff_date:
                recent_files.append(file_path)
        
        return recent_files
    
    def parse_csv_export(self, file_path):
        """
        Parse an American Express CSV export file.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        try:
            # Try to read the CSV file
            df = pd.read_csv(file_path)
            
            # Standardize column names (Amex exports can have different formats)
            column_mapping = {
                # Common Amex column names and variations
                'Date': 'Date',
                'Transaction Date': 'Date',
                'Description': 'Description',
                'Merchant': 'Description',
                'Vendor': 'Description',
                'Amount': 'Amount',
                'Debit': 'Amount',
                'Credit': 'Amount',
                'Category': 'Category'
            }
            
            # Rename columns based on mapping
            df = df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping})
            
            # Ensure required columns exist
            required_columns = ['Date', 'Description', 'Amount']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in the CSV file")
            
            # Convert date to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Add Category column if it doesn't exist
            if 'Category' not in df.columns:
                df['Category'] = 'Uncategorized'
            
            # Ensure Amount is numeric and handle debit/credit
            if 'Debit' in df.columns and 'Credit' in df.columns:
                # Some exports separate debits and credits
                df['Amount'] = df['Debit'].fillna(0) - df['Credit'].fillna(0)
            else:
                # Ensure Amount is numeric
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            
            # Filter out rows with invalid dates or amounts
            df = df.dropna(subset=['Date', 'Amount'])
            
            return df[['Date', 'Description', 'Amount', 'Category']]
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    def parse_ofx_export(self, file_path):
        """
        Parse an American Express OFX/QFX export file.
        
        Args:
            file_path (str): Path to the OFX/QFX file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
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
                    'Category': 'Uncategorized'
                })
            
            if transactions:
                return pd.DataFrame(transactions)
            else:
                raise ValueError("No transactions found in the OFX file")
                
        except Exception as e:
            raise ValueError(f"Error parsing OFX file: {str(e)}")
    
    def parse_export_file(self, file_path):
        """
        Parse an export file based on its extension.
        
        Args:
            file_path (str): Path to the export file
            
        Returns:
            pd.DataFrame: DataFrame with standardized transaction data
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.csv':
            return self.parse_csv_export(file_path)
        elif ext in ['.ofx', '.qfx']:
            return self.parse_ofx_export(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def get_transactions(self, file_path=None, months=0):
        """
        Get transactions from an export file or find recent exports.
        
        Args:
            file_path (str, optional): Path to the export file. If None, will look for recent exports.
            months (int): Number of months of data to include (for filtering) - set to 0 to include all data
            
        Returns:
            tuple: (success (bool), data (pd.DataFrame) or error message (str))
        """
        try:
            if file_path:
                # Use the specified file
                df = self.parse_export_file(file_path)
                st.info(f"Processed file: {os.path.basename(file_path)}")
            else:
                # Look for recent exports
                recent_files = self.find_recent_exports(days_back=30)  # Look back 30 days by default
                
                if not recent_files:
                    return False, "No recent American Express exports found. Please download your statement from the American Express website or upload a file."
                
                # Show the found files to the user
                file_options = [os.path.basename(f) for f in recent_files]
                st.info(f"Found {len(recent_files)} potential statement files in your Downloads folder.")
                
                # Try to parse each file until one succeeds
                success = False
                for i, file in enumerate(recent_files):
                    try:
                        st.text(f"Trying to parse: {os.path.basename(file)}")
                        df = self.parse_export_file(file)
                        st.success(f"Successfully parsed: {os.path.basename(file)}")
                        success = True
                        break
                    except Exception as e:
                        st.warning(f"Could not parse {os.path.basename(file)}: {str(e)}")
                        continue
                
                if not success:
                    return False, "Could not parse any of the found export files. Please ensure they are valid American Express exports or upload a file manually."
            
            # No month filtering - we'll use date range in the app instead
            if df.empty:
                return False, "No transactions found in the file"
            
            # Sort by date
            df = df.sort_values('Date')
            
            return True, df
            
        except Exception as e:
            return False, f"Error processing export: {str(e)}"
