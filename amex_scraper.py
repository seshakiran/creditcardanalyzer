import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import datetime
import io


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
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set user agent to avoid detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
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
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard"))
            )
            
            # Navigate to statements page
            # Note: The exact element selectors may need adjustment based on Amex's actual website structure
            statements_link = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Statements') or contains(@href, 'statements')]"))
            )
            statements_link.click()
            
            # Wait for statements page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".statements-container"))
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
                    
                    # Wait for download to complete
                    time.sleep(5)
                    
                    # In a headless browser, we need to get the downloaded content directly
                    # This is a simplification - in a real implementation, you would need to
                    # handle the file download based on your environment
                    
                    # For demonstration, we'll simulate parsing the downloaded CSV
                    # In reality, you would need to find the downloaded file and read it
                    
                    # Simulated CSV content for demonstration
                    # In a real implementation, you would read the actual downloaded file
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
        Parse the transaction data from the statement page.
        In a real implementation, this would extract data from the downloaded CSV file.
        
        Returns:
            list: List of transaction dictionaries
        """
        # Placeholder for actual implementation
        # In a real implementation, you would:
        # 1. Find the downloaded CSV file
        # 2. Read and parse the file using pandas
        # 3. Return the parsed data
        
        # This is a simplified example to simulate the parsing process
        try:
            # Find the transaction table on the page
            transaction_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".transaction-table, .statement-transactions"))
            )
            
            rows = transaction_table.find_elements(By.TAG_NAME, "tr")
            transactions = []
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:  # Ensure enough cells
                    date_text = cells[0].text.strip()
                    description = cells[1].text.strip()
                    amount_text = cells[2].text.strip().replace('$', '').replace(',', '')
                    
                    try:
                        date = pd.to_datetime(date_text)
                        amount = float(amount_text)
                        
                        transactions.append({
                            'Date': date,
                            'Description': description,
                            'Amount': amount,
                            'Category': 'Uncategorized'  # Default category
                        })
                    except (ValueError, TypeError):
                        # Skip rows with parsing errors
                        continue
            
            return transactions
            
        except (TimeoutException, NoSuchElementException):
            # If we can't find or parse the transaction table, return empty list
            return []
