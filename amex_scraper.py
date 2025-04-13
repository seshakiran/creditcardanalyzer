import os
import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import datetime
import io
import logging


class AmexScraper:
    """
    A class to handle American Express web scraping functionality.
    """
    
    def __init__(self):
        """Initialize the AmexScraper with necessary configurations."""
        self.base_url = "https://www.americanexpress.com/en-us/account/login"
        self.driver = None
    
    def _setup_driver(self):
        """Setup and configure the Selenium WebDriver."""
        chrome_options = Options()
        
        # Set up headless mode for production use
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set user agent to avoid detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Set download preferences
        download_dir = os.path.join(os.getcwd(), 'temp_downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def login_and_download(self, username, password, months=12):
        """
        Login to American Express and download statements.
        
        Args:
            username (str): American Express login username/email
            password (str): American Express login password
            months (int): Number of months of statements to download (default: 12)
            
        Returns:
            tuple: (success (bool), data (pd.DataFrame) or error message (str))
        """
        try:
            self._setup_driver()
            
            # Navigate to the login page
            self.driver.get(self.base_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "eliloUserID"))
            )
            
            # Enter username
            username_field = self.driver.find_element(By.ID, "eliloUserID")
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "eliloPassword")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "loginSubmit")
            login_button.click()
            
            # Wait for login to complete and dashboard to load
            # This selector might need adjustment based on Amex's actual website structure
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .account-summary, .account-home"))
            )
            
            # Navigate to statements page
            # The selector might need adjustment based on Amex's actual website structure
            statements_link = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Statements') or contains(@href, 'statements') or contains(text(), 'Activity')]"))
            )
            statements_link.click()
            
            # Wait for statements page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".statements-container, .activity-container, .transaction-list"))
            )
            
            # Get transactions for the requested number of months
            all_transactions = []
            
            # Current date
            current_date = datetime.datetime.now()
            
            for i in range(months):
                # Calculate the statement month (going back from current month)
                target_date = current_date - datetime.timedelta(days=30 * i)
                month_year = target_date.strftime("%B %Y")
                
                try:
                    # Find and click on the statement for this month
                    statement_selector = f"//div[contains(text(), '{month_year}')]"
                    statement_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, statement_selector))
                    )
                    statement_element.click()
                    
                    # Wait for statement details to load
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".statement-details"))
                    )
                    
                    # Click download/export button
                    export_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'Export')]"))
                    )
                    export_button.click()
                    
                    # Select CSV format if there's an option
                    try:
                        csv_option = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'CSV') or contains(@value, 'csv')]"))
                        )
                        csv_option.click()
                    except (TimeoutException, NoSuchElementException):
                        # CSV might be the default or only option
                        pass
                    
                    # Confirm download
                    download_confirm = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'Confirm')]"))
                    )
                    download_confirm.click()
                    
                    # Set up Chrome download preferences to a specific directory
                    download_dir = os.path.join(os.getcwd(), 'temp_downloads')
                    os.makedirs(download_dir, exist_ok=True)
                    
                    # Wait for download to complete
                    # Look for download confirmation or check download directory
                    download_wait = 10  # seconds to wait for download
                    time.sleep(download_wait)
                    
                    # Find downloaded CSV file in the download directory
                    csv_files = [f for f in os.listdir(download_dir) if f.endswith('.csv') and 'statement' in f.lower()]
                    
                    if csv_files:
                        # Get the most recent file
                        latest_file = max([os.path.join(download_dir, f) for f in csv_files], key=os.path.getctime)
                        
                        # Read the CSV file
                        try:
                            # Try different encodings if needed
                            df = pd.read_csv(latest_file)
                            
                            # Process the dataframe to extract transaction data
                            # Adjust column names to match expected format
                            if 'Date' not in df.columns and 'Transaction Date' in df.columns:
                                df.rename(columns={'Transaction Date': 'Date'}, inplace=True)
                            
                            if 'Description' not in df.columns and 'Merchant' in df.columns:
                                df.rename(columns={'Merchant': 'Description'}, inplace=True)
                            
                            # Convert to list of dictionaries
                            statement_data = df.to_dict('records')
                            all_transactions.extend(statement_data)
                            
                            # Clean up - remove the file after processing
                            os.remove(latest_file)
                        except Exception as e:
                            print(f"Error processing CSV file: {str(e)}")
                    else:
                        # If no CSV found, try to parse from the web page
                        statement_data = self._parse_statement_page()
                        all_transactions.extend(statement_data)
                    
                    # Go back to statements list
                    back_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Back') or contains(@aria-label, 'Back')]"))
                    )
                    back_button.click()
                    
                except (TimeoutException, NoSuchElementException) as e:
                    print(f"Could not process statement for {month_year}: {str(e)}")
                    continue
            
            # Convert to DataFrame
            if all_transactions:
                df = pd.DataFrame(all_transactions)
                return True, df
            else:
                return False, "No transaction data found"
                
        except Exception as e:
            print(f"Error during login or download: {str(e)}")
            return False, str(e)
        finally:
            if self.driver:
                self.driver.quit()
    
    def _parse_statement_page(self):
        """
        Parse the transaction data directly from the statement page when CSV download fails.
        This is a fallback method when direct CSV download doesn't work.
        
        Returns:
            list: List of transaction dictionaries
        """
        try:
            # Find the transaction table on the page - try multiple possible selectors
            # The exact selector will depend on Amex's actual website structure
            selectors = [
                ".transaction-table", 
                ".statement-transactions", 
                ".transaction-list", 
                ".activity-table",
                "table.transactions"
            ]
            
            transaction_table = None
            for selector in selectors:
                try:
                    transaction_table = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if transaction_table:
                        break
                except:
                    continue
            
            if not transaction_table:
                print("Could not find transaction table on page")
                return []
            
            # Find all transaction rows
            rows = transaction_table.find_elements(By.TAG_NAME, "tr")
            transactions = []
            
            # Skip header row if it exists
            for row in rows[1:] if len(rows) > 1 else rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # Amex tables typically have date, description, and amount columns
                # The exact indices may vary based on the actual table structure
                if len(cells) >= 3:
                    # Try to extract date, description, and amount
                    # The indices might need adjustment based on the actual table structure
                    date_text = cells[0].text.strip()
                    description = cells[1].text.strip()
                    amount_text = cells[2].text.strip().replace('$', '').replace(',', '')
                    
                    try:
                        # Try to parse date in various formats
                        try:
                            date = pd.to_datetime(date_text)
                        except:
                            # Try different date formats if standard parsing fails
                            date_formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%b %d, %Y']
                            for fmt in date_formats:
                                try:
                                    date = pd.to_datetime(date_text, format=fmt)
                                    break
                                except:
                                    continue
                        
                        # Try to parse amount
                        # Remove any non-numeric characters except decimal point and minus sign
                        amount_text = re.sub(r'[^\d.-]', '', amount_text)
                        amount = float(amount_text)
                        
                        transactions.append({
                            'Date': date,
                            'Description': description,
                            'Amount': amount,
                            'Category': 'Uncategorized'  # Default category
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing row: {str(e)}")
                        # Skip rows with parsing errors
                        continue
            
            return transactions
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error parsing statement page: {str(e)}")
            # If we can't find or parse the transaction table, return empty list
            return []
