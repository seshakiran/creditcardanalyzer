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
    Create a pivot table from transaction data.
    
    Args:
        data (pd.DataFrame): DataFrame containing categorized transaction data
        
    Returns:
        pd.DataFrame: Pivot table of expenses
    """
    # Ensure date is in datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Extract month and year
    data['Month'] = data['Date'].dt.strftime('%Y-%m')
    
    # Create pivot table: Categories as rows, Months as columns
    pivot = pd.pivot_table(
        data,
        values='Amount',
        index='Category',
        columns='Month',
        aggfunc='sum',
        fill_value=0
    )
    
    # Add a Total column
    pivot['Total'] = pivot.sum(axis=1)
    
    # Add a Total row
    pivot.loc['Total'] = pivot.sum()
    
    # Sort columns chronologically
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    
    return pivot
