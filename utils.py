import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key():
    """
    Generate or retrieve the encryption key for securing credentials.
    
    Returns:
        bytes: Encryption key
    """
    # Try to get key from environment or generate a new one
    key_env = os.getenv("ENCRYPTION_KEY")
    
    if key_env:
        # Use key from environment variable
        return base64.urlsafe_b64decode(key_env)
    else:
        # Generate a new key based on a hash of the machine
        # This is a simplified approach and not for production use
        machine_id = os.getenv("MACHINE_ID", "default_machine_id")
        salt = b'amex_analyzer_salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key


def encrypt_credentials(password):
    """
    Encrypt password for secure storage.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Encrypted password
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_credentials(encrypted_password):
    """
    Decrypt stored password.
    
    Args:
        encrypted_password (str): Encrypted password
        
    Returns:
        str: Plain text password
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_password.encode())
    return decrypted.decode()


def save_credentials(credentials):
    """
    Save encrypted credentials to file.
    
    Args:
        credentials (dict): Dictionary with username and encrypted password
    """
    user_data_dir = os.path.expanduser('~/.amex_analyzer')
    os.makedirs(user_data_dir, exist_ok=True)
    
    credentials_file = os.path.join(user_data_dir, 'credentials.json')
    
    with open(credentials_file, 'w') as f:
        json.dump(credentials, f)


def load_credentials():
    """
    Load credentials from file.
    
    Returns:
        dict or None: Dictionary with username and encrypted password, or None if not found
    """
    credentials_file = os.path.expanduser('~/.amex_analyzer/credentials.json')
    
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    return None


def get_months_between_dates(start_date, end_date):
    """
    Get a list of months between two dates.
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        list: List of months in format YYYY-MM
    """
    months = []
    current_date = start_date
    
    while current_date <= end_date:
        month_str = current_date.strftime('%Y-%m')
        if month_str not in months:
            months.append(month_str)
        
        # Move to next month (simplified approach)
        next_month = current_date.month + 1
        next_year = current_date.year
        
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        # Set to first day of next month
        try:
            current_date = current_date.replace(year=next_year, month=next_month, day=1)
        except ValueError:
            # Handle month with fewer days
            current_date = current_date.replace(year=next_year, month=next_month, day=1)
    
    return months
