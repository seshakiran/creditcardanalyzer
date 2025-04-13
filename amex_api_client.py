import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv

class AmexApiClient:
    """
    Client for interacting with the American Express API.
    This uses the official Amex for Developers API instead of web scraping.
    """
    
    def __init__(self):
        """Initialize the API client with necessary configurations."""
        load_dotenv()
        
        # API credentials should be stored in environment variables
        self.client_id = os.getenv("AMEX_CLIENT_ID")
        self.client_secret = os.getenv("AMEX_CLIENT_SECRET")
        self.private_key_path = os.getenv("AMEX_PRIVATE_KEY_PATH")
        
        # API endpoints
        self.base_url = "https://api.americanexpress.com"
        self.token_url = f"{self.base_url}/oauth/token"
        self.transactions_url = f"{self.base_url}/api/servicing/v1/financials/transactions"
        
        # Access token
        self.access_token = None
        self.token_expiry = None
    
    def _load_private_key(self):
        """Load the private key for API authentication."""
        if not self.private_key_path:
            raise ValueError("Private key path not specified in environment variables")
        
        with open(self.private_key_path, "rb") as key_file:
            private_key = load_pem_private_key(
                key_file.read(),
                password=None
            )
        return private_key
    
    def _get_access_token(self):
        """
        Get an OAuth access token from the Amex API.
        Tokens are cached until they expire.
        """
        # Check if we have a valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        if not self.client_id or not self.client_secret:
            raise ValueError("API credentials not specified in environment variables")
        
        # Create the authentication signature
        private_key = self._load_private_key()
        timestamp = int(datetime.now().timestamp())
        message = f"{self.client_id}:{timestamp}"
        
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        encoded_signature = base64.b64encode(signature).decode()
        
        # Request body
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "signature": encoded_signature,
            "timestamp": timestamp
        }
        
        # Make the request
        response = requests.post(self.token_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            # Set expiry time (usually 1 hour)
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {response.text}")
    
    def get_transactions(self, months=12):
        """
        Get transactions from the Amex API.
        
        Args:
            months (int): Number of months of transactions to retrieve
            
        Returns:
            tuple: (success (bool), data (pd.DataFrame) or error message (str))
        """
        try:
            # Get access token
            token = self._get_access_token()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # Format dates as required by API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Request headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Request parameters
            params = {
                "start_date": start_date_str,
                "end_date": end_date_str
            }
            
            # Make the request
            response = requests.get(
                self.transactions_url,
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Process the response into a DataFrame
                transactions = []
                
                for transaction in data.get("transactions", []):
                    transactions.append({
                        "Date": transaction.get("transaction_date"),
                        "Description": transaction.get("description", ""),
                        "Amount": float(transaction.get("amount", 0)),
                        "Category": transaction.get("category", "Uncategorized")
                    })
                
                if transactions:
                    df = pd.DataFrame(transactions)
                    df["Date"] = pd.to_datetime(df["Date"])
                    return True, df
                else:
                    return False, "No transactions found in the specified date range"
            else:
                return False, f"API error: {response.status_code} - {response.text}"
        
        except Exception as e:
            return False, f"Error retrieving transactions: {str(e)}"
