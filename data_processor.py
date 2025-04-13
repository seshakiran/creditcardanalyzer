import pandas as pd
import re


def categorize_transactions(data):
    """
    Categorize credit card transactions based on merchant descriptions.
    
    Args:
        data (pd.DataFrame): DataFrame containing transaction data
        
    Returns:
        tuple: (categorized_data (pd.DataFrame), category_list (list))
    """
    # Ensure we have a copy to avoid modifying the original
    df = data.copy()
    
    # Initialize category column if it doesn't exist
    if 'Category' not in df.columns:
        df['Category'] = 'Uncategorized'
    
    # Define category patterns
    category_patterns = {
        'Dining': [
            r'restaurant', r'dining', r'café', r'cafe', r'coffee', r'bakery', 
            r'starbucks', r'dunkin', r'mcdonald', r'burger', r'pizza', r'taco', 
            r'chipotle', r'wendy', r'subway', r'grubhub', r'doordash', r'ubereats',
            r'deli', r'bar & grill', r'bistro', r'steakhouse', r'sushi'
        ],
        'Groceries': [
            r'grocery', r'market', r'supermarket', r'food market', r'whole foods',
            r'kroger', r'safeway', r'trader joe', r'aldi', r'walmart', r'target',
            r'costco', r'sam\'s club', r'publix', r'wegmans', r'instacart'
        ],
        'Gas & Automotive': [
            r'gas', r'fuel', r'shell', r'exxon', r'mobil', r'chevron', r'bp',
            r'auto parts', r'autozone', r'jiffy lube', r'meineke', r'valvoline',
            r'car wash', r'parking', r'garage', r'toll'
        ],
        'Travel': [
            r'airline', r'flight', r'delta', r'united', r'american air', r'southwest',
            r'jetblue', r'airbnb', r'hotel', r'motel', r'inn', r'resort', r'marriott',
            r'hilton', r'hyatt', r'expedia', r'travelocity', r'booking.com', r'uber',
            r'lyft', r'taxi', r'car rental', r'hertz', r'avis', r'enterprise'
        ],
        'Entertainment': [
            r'movie', r'cinema', r'theater', r'theatre', r'netflix', r'hulu', 
            r'disney+', r'spotify', r'apple music', r'concert', r'ticketmaster',
            r'amazon prime', r'hbo', r'youtube', r'game', r'playstation', r'xbox',
            r'theme park', r'museum', r'zoo', r'aquarium'
        ],
        'Shopping': [
            r'amazon', r'walmart', r'target', r'best buy', r'macy', r'nordstrom',
            r'clothing', r'apparel', r'shoe', r'jewelry', r'accessory', r'cosmetic',
            r'sephora', r'ulta', r'mall', r'department store', r'nike', r'adidas',
            r'apple store', r'microsoft', r'home depot', r'lowe', r'ikea', r'furniture'
        ],
        'Health & Medical': [
            r'pharmacy', r'drug store', r'cvs', r'walgreens', r'rite aid', r'doctor',
            r'hospital', r'clinic', r'medical', r'dental', r'healthcare', r'insurance',
            r'vision', r'optometrist', r'chiropractor', r'therapy'
        ],
        'Utilities & Bills': [
            r'electric', r'water', r'gas bill', r'utility', r'phone', r'mobile',
            r'internet', r'cable', r'tv', r'telecom', r'at&t', r'verizon', r'comcast',
            r'xfinity', r'spectrum', r'bill pay', r'utilities'
        ],
        'Subscriptions & Memberships': [
            r'subscription', r'membership', r'monthly', r'annual fee', r'gym',
            r'fitness', r'magazine', r'newspaper', r'software', r'service fee',
            r'recurring', r'monthly service'
        ],
        'Education': [
            r'tuition', r'school', r'university', r'college', r'campus', r'education',
            r'book store', r'textbook', r'course', r'library', r'student'
        ],
        'Income & Transfers': [
            r'deposit', r'transfer', r'payment', r'payroll', r'direct deposit',
            r'venmo', r'paypal', r'zelle', r'cash app', r'refund', r'reimbursement'
        ]
    }
    
    # Categorize each transaction
    for index, row in df.iterrows():
        description = row['Description'].lower()
        
        # Check each category pattern
        for category, patterns in category_patterns.items():
            if any(re.search(pattern, description, re.IGNORECASE) for pattern in patterns):
                df.at[index, 'Category'] = category
                break
    
    # Get list of unique categories
    category_list = df['Category'].unique().tolist()
    
    return df, category_list


def create_pivot_table(data):
    """
    Create pivot tables from transaction data.
    
    Args:
        data (pd.DataFrame): DataFrame containing categorized transaction data
        
    Returns:
        tuple: (category_pivot, merchant_pivot, category_merchant_pivot) - Three pivot tables for analysis
    """
    # Ensure date is in datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Extract month and year
    data['Month'] = data['Date'].dt.strftime('%Y-%m')
    
    # Create pivot table by category: Categories as rows, Months as columns
    category_pivot = pd.pivot_table(
        data,
        values='Amount',
        index='Category',
        columns='Month',
        aggfunc='sum',
        fill_value=0
    )
    
    # Add a Total column
    category_pivot['Total'] = category_pivot.sum(axis=1)
    
    # Add a Total row
    category_pivot.loc['Total'] = category_pivot.sum()
    
    # Sort columns chronologically
    category_pivot = category_pivot.reindex(sorted(category_pivot.columns), axis=1)
    
    # Create a second pivot table by merchant
    # First, clean up merchant names to group similar ones
    data['Merchant'] = data['Description'].str.upper()  # Convert to uppercase for consistency
    
    # Create merchant pivot table: Merchants as rows, Months as columns
    merchant_pivot = pd.pivot_table(
        data,
        values='Amount',
        index=['Merchant', 'Category'],  # Include category as a secondary index
        columns='Month',
        aggfunc='sum',
        fill_value=0
    )
    
    # Add a Total column
    merchant_pivot['Total'] = merchant_pivot.sum(axis=1)
    
    # Sort by total amount spent (descending)
    merchant_pivot = merchant_pivot.sort_values('Total', ascending=False)
    
    # Sort columns chronologically
    merchant_pivot = merchant_pivot.reindex(sorted(merchant_pivot.columns), axis=1)
    
    # Create a nested pivot table with categories and merchants
    # This will have categories as main rows and merchants nested underneath
    category_merchant_pivot = pd.pivot_table(
        data,
        values='Amount',
        index=['Category', 'Merchant'],  # Category as primary index, Merchant as secondary
        aggfunc='sum',
        fill_value=0
    )
    
    # Sort by category and then by amount within each category
    category_merchant_pivot = category_merchant_pivot.sort_values(['Category', 'Amount'], ascending=[True, False])
    
    return category_pivot, merchant_pivot, category_merchant_pivot
