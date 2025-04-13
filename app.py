import os
import streamlit as st
import pandas as pd
import datetime
import tempfile
import calendar
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# Import custom modules
from bank_parsers import MultiStatementParser
from data_processor import categorize_transactions, create_pivot_table
from visualizer import plot_spending_by_category, plot_spending_over_time

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Amex Statement Analyzer",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'data' not in st.session_state:
    st.session_state.data = None
if 'categories' not in st.session_state:
    st.session_state.categories = None
if 'category_pivot' not in st.session_state:
    st.session_state.category_pivot = None
if 'merchant_pivot' not in st.session_state:
    st.session_state.merchant_pivot = None
if 'category_merchant_pivot' not in st.session_state:
    st.session_state.category_merchant_pivot = None
if 'date_filter' not in st.session_state:
    st.session_state.date_filter = None


def main():
    # Sidebar
    with st.sidebar:
        st.title("Credit Card Analyzer")
        st.write("Analyze statements from multiple credit cards with ease.")
        
        # Date range selector - only shown when data is loaded
        if st.session_state.data is not None:
            st.subheader("Date Range")
            today = datetime.date.today()
            one_year_ago = today - datetime.timedelta(days=365)
            
            # Get min and max dates from the data for better defaults
            min_date = st.session_state.data['Date'].min().date()
            max_date = st.session_state.data['Date'].max().date()
            
            start_date = st.date_input("Start date", min_date)
            end_date = st.date_input("End date", max_date)
            
            if st.button("Apply Date Filter"):
                filtered_data = st.session_state.data[
                    (st.session_state.data['Date'] >= pd.Timestamp(start_date)) & 
                    (st.session_state.data['Date'] <= pd.Timestamp(end_date))
                ]
                st.session_state.date_filter = filtered_data
                st.rerun()
        
        # Download options
        if st.session_state.data is not None:
            st.subheader("Export Data")
            export_format = st.selectbox("Format", ["CSV", "Excel"])
            
            if st.button("Export Data"):
                data_to_export = st.session_state.date_filter if st.session_state.date_filter is not None else st.session_state.data
                
                if export_format == "CSV":
                    csv = data_to_export.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="credit_card_transactions.csv",
                        mime="text/csv"
                    )
                else:  # Excel
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                        data_to_export.to_excel(tmp.name, index=False)
                        with open(tmp.name, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="Download Excel",
                            data=excel_data,
                            file_name="credit_card_transactions.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    # Main content
    if not st.session_state.authenticated:
        st.title("Credit Card Statement Analyzer")
        
        st.write("### Upload Your Credit Card Statements")
        st.write("Upload statement exports from American Express, Chase, Discover, or other banks for analysis.")
        
        # File upload option - multiple files
        uploaded_files = st.file_uploader("Upload bank statement exports (CSV, OFX, QFX)", 
                                        type=["csv", "ofx", "qfx"],
                                        accept_multiple_files=True)
        
        # Or scan for recent downloads
        st.write("Or let the app scan your Downloads folder for recent bank statement exports:")
        
        # Time period selection
        st.subheader("Select Time Period")
        
        # Define time period options
        time_period_options = [
            "Custom date range",
            "Last 30 days",
            "Last 60 days",
            "Last 90 days",
            "Last 6 months",
            "Last 12 months",
            "This month",
            "Last month",
            "This quarter",
            "Last quarter",
            "This year",
            "Last year"
        ]
        
        time_period = st.selectbox("Time period", time_period_options)
        
        # Calculate date range based on selection
        today = datetime.date.today()
        
        if time_period == "Custom date range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", today - datetime.timedelta(days=90))
            with col2:
                end_date = st.date_input("End date", today)
        else:
            # Calculate start and end dates based on selection
            if time_period == "Last 30 days":
                start_date = today - datetime.timedelta(days=30)
                end_date = today
            elif time_period == "Last 60 days":
                start_date = today - datetime.timedelta(days=60)
                end_date = today
            elif time_period == "Last 90 days":
                start_date = today - datetime.timedelta(days=90)
                end_date = today
            elif time_period == "Last 6 months":
                start_date = today - relativedelta(months=6)
                end_date = today
            elif time_period == "Last 12 months":
                start_date = today - relativedelta(months=12)
                end_date = today
            elif time_period == "This month":
                start_date = today.replace(day=1)
                end_date = today
            elif time_period == "Last month":
                first_day_of_month = today.replace(day=1)
                last_month = first_day_of_month - datetime.timedelta(days=1)
                start_date = last_month.replace(day=1)
                end_date = first_day_of_month - datetime.timedelta(days=1)
            elif time_period == "This quarter":
                current_quarter = (today.month - 1) // 3 + 1
                start_date = datetime.date(today.year, 3 * current_quarter - 2, 1)
                if current_quarter < 4:
                    end_date = datetime.date(today.year, 3 * current_quarter + 1, 1) - datetime.timedelta(days=1)
                else:
                    end_date = datetime.date(today.year, 12, 31)
            elif time_period == "Last quarter":
                current_quarter = (today.month - 1) // 3 + 1
                last_quarter = current_quarter - 1 if current_quarter > 1 else 4
                year = today.year if current_quarter > 1 else today.year - 1
                start_date = datetime.date(year, 3 * last_quarter - 2, 1)
                if last_quarter < 4:
                    end_date = datetime.date(year, 3 * last_quarter + 1, 1) - datetime.timedelta(days=1)
                else:
                    end_date = datetime.date(year, 12, 31)
            elif time_period == "This year":
                start_date = datetime.date(today.year, 1, 1)
                end_date = today
            elif time_period == "Last year":
                start_date = datetime.date(today.year - 1, 1, 1)
                end_date = datetime.date(today.year - 1, 12, 31)
            
            # Display the calculated date range
            st.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        if st.button("Process Statements"):
            with st.spinner("Processing bank statement exports..."):
                try:
                    # Initialize the multi-statement parser
                    parser = MultiStatementParser()
                    
                    file_paths = []
                    temp_files = []
                    
                    if uploaded_files:
                        # Save the uploaded files to temporary locations
                        for uploaded_file in uploaded_files:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                tmp.write(uploaded_file.getvalue())
                                file_paths.append(tmp.name)
                                temp_files.append(tmp.name)
                        
                        st.info(f"Processing {len(uploaded_files)} uploaded files...")
                    else:
                        # Scan for recent downloads
                        file_paths = parser.find_recent_statements(days_back=30)
                        if not file_paths:
                            st.warning("No recent statement files found. Please upload files manually.")
                            return
                        
                        st.info(f"Found {len(file_paths)} potential statement files in your Downloads folder.")
                    
                    # Parse all files
                    success, data = parser.parse_multiple_files(file_paths)
                    
                    # Clean up temporary files
                    for temp_file in temp_files:
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
                    
                    if success:
                        if isinstance(data, pd.DataFrame) and not data.empty:
                            # Filter by date range
                            data = data[
                                (data['Date'] >= pd.Timestamp(start_date)) & 
                                (data['Date'] <= pd.Timestamp(end_date))
                            ]
                            
                            if data.empty:
                                st.warning("No transactions found in the selected date range. Please adjust your dates.")
                            else:
                                # Show summary of data sources
                                source_counts = data['Source'].value_counts()
                                st.success(f"Successfully processed {len(data)} transactions from {len(source_counts)} sources!")
                                
                                # Display source breakdown
                                source_text = ", ".join([f"{source}: {count} transactions" for source, count in source_counts.items()])
                                st.info(f"Sources: {source_text}")
                                
                                st.session_state.data = data
                                
                                # Categorize transactions
                                st.session_state.data, st.session_state.categories = categorize_transactions(data)
                                
                                # Create pivot tables
                                category_pivot, merchant_pivot, category_merchant_pivot = create_pivot_table(st.session_state.data)
                                st.session_state.category_pivot = category_pivot
                                st.session_state.merchant_pivot = merchant_pivot
                                st.session_state.category_merchant_pivot = category_merchant_pivot
                                
                                st.session_state.authenticated = True
                                st.rerun()
                        else:
                            st.warning("No transaction data was found in the exports. Check if your exports contain transaction data.")
                    else:
                        error_msg = data if isinstance(data, str) else "Unknown error"
                        st.error(f"Failed to process statement exports: {error_msg}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    else:
        # Display data analysis after authentication
        st.title("Credit Card Statement Analysis")
        
        # Use filtered data if available, otherwise use all data
        display_data = st.session_state.date_filter if st.session_state.date_filter is not None else st.session_state.data
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", len(display_data))
        with col2:
            st.metric("Total Spend", f"${display_data['Amount'].sum():.2f}")
        with col3:
            st.metric("Average Transaction", f"${display_data['Amount'].mean():.2f}")
        with col4:
            # Count unique sources
            sources = display_data['Source'].nunique()
            st.metric("Card Sources", sources)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Transactions", "Pivot Table", "Visualizations", "Source Summary"])
        
        with tab1:
            st.subheader("Transaction Data")
            st.dataframe(display_data, use_container_width=True)
        
        with tab2:
            st.subheader("Expense Analysis")
            
            # Create tabs for different pivot views
            pivot_tab1, pivot_tab2, pivot_tab3 = st.tabs(["By Category", "By Merchant", "Category-Merchant Nested"])
            
            # Recalculate pivots if date filter is applied
            if st.session_state.date_filter is not None:
                category_pivot, merchant_pivot, category_merchant_pivot = create_pivot_table(display_data)
            else:
                category_pivot = st.session_state.category_pivot
                merchant_pivot = st.session_state.merchant_pivot
                category_merchant_pivot = st.session_state.category_merchant_pivot
            
            with pivot_tab1:
                st.write("### Spending by Category")
                st.dataframe(category_pivot, use_container_width=True)
                
            with pivot_tab2:
                st.write("### Spending by Merchant")
                st.dataframe(merchant_pivot, use_container_width=True)
                
            with pivot_tab3:
                st.write("### Category-Merchant Breakdown (Collapsible)")
                
                # Get unique categories
                categories = category_merchant_pivot.index.get_level_values('Category').unique()
                
                # Create a summary table with just the category totals
                category_totals = {}
                for category in categories:
                    # Get all rows for this category
                    category_data = category_merchant_pivot.loc[category]
                    # Calculate the total for this category
                    category_total = category_data['Total'].sum() if 'Total' in category_data.columns else category_data.sum().sum()
                    category_totals[category] = category_total
                
                # Create a DataFrame for the category totals
                category_summary = pd.DataFrame(list(category_totals.items()), columns=['Category', 'Total'])
                category_summary = category_summary.sort_values('Total', ascending=False)
                
                # Format the total as currency
                category_summary['Total'] = category_summary['Total'].map('${:,.2f}'.format)
                
                # Display the category summary
                st.dataframe(category_summary, use_container_width=True)
                
                # Add collapsible sections for each category
                st.write("#### Click on a category to see merchants:")
                
                for category in categories:
                    # Get data for this category
                    category_data = category_merchant_pivot.loc[category]
                    
                    # Calculate total for this category
                    category_total = category_data['Total'].sum() if 'Total' in category_data.columns else category_data.sum().sum()
                    
                    # Create an expander for this category
                    with st.expander(f"{category} - ${category_total:.2f}"):
                        # Create a DataFrame with merchant names and amounts
                        merchant_df = pd.DataFrame(columns=['Merchant', 'Total'])
                        
                        # Handle different data structures
                        if isinstance(category_data, pd.Series):
                            # Single merchant case
                            merchant_name = category_data.name
                            if isinstance(merchant_name, tuple):
                                merchant_name = merchant_name[1]  # Extract merchant from tuple
                            merchant_df = pd.DataFrame({'Merchant': [merchant_name], 'Total': [category_data.sum()]})
                        else:
                            # Get the index which contains the merchant names
                            merchant_df = category_data.copy()
                            
                            # If we have a multi-index DataFrame, reset the index to get the merchant names
                            if isinstance(merchant_df.index, pd.MultiIndex):
                                merchant_df = merchant_df.reset_index()
                            else:
                                # If it's a single-level index, add it as a column
                                merchant_df = merchant_df.reset_index()
                                merchant_df.rename(columns={'index': 'Merchant'}, inplace=True)
                            
                            # Calculate total if needed
                            if 'Total' not in merchant_df.columns:
                                merchant_df['Total'] = merchant_df.sum(axis=1, numeric_only=True)
                                
                            # Keep only the Merchant and Total columns
                            merchant_cols = [col for col in merchant_df.columns if col in ['Merchant', 'Total']]
                            merchant_df = merchant_df[merchant_cols]
                        
                        # Sort by total amount
                        merchant_df = merchant_df.sort_values('Total', ascending=False)
                        
                        # Format as currency
                        merchant_df['Total'] = merchant_df['Total'].map('${:,.2f}'.format)
                        
                        # Display the merchant breakdown
                        st.dataframe(merchant_df, use_container_width=True)
        
        with tab3:
            st.subheader("Spending Visualizations")
            
            # Category breakdown chart
            st.write("### Spending by Category")
            category_fig = plot_spending_by_category(display_data)
            st.plotly_chart(category_fig, use_container_width=True)
            
            # Time series chart
            st.write("### Spending Over Time")
            time_fig = plot_spending_over_time(display_data)
            st.plotly_chart(time_fig, use_container_width=True)
            
        with tab4:
            st.subheader("Source Summary")
            
            # Create a summary by source
            source_summary = display_data.groupby('Source').agg({
                'Amount': ['sum', 'mean', 'count'],
                'Date': ['min', 'max']
            }).reset_index()
            
            # Flatten the multi-index columns
            source_summary.columns = ['Source', 'Total Amount', 'Average Transaction', 'Transaction Count', 'First Date', 'Last Date']
            
            # Format the columns
            source_summary['Total Amount'] = source_summary['Total Amount'].map('${:,.2f}'.format)
            source_summary['Average Transaction'] = source_summary['Average Transaction'].map('${:,.2f}'.format)
            
            # Display the summary
            st.write("### Summary by Source")
            st.dataframe(source_summary, use_container_width=True)
            
            # Show a more detailed breakdown by source and month
            st.write("### Monthly Breakdown by Source")
            
            # Create pivot table by source and month
            source_pivot = pd.pivot_table(
                display_data,
                values='Amount',
                index='Source',
                columns='Month',
                aggfunc='sum',
                fill_value=0
            )
            
            # Add a Total column
            source_pivot['Total'] = source_pivot.sum(axis=1)
            
            # Sort columns chronologically
            source_pivot = source_pivot.reindex(sorted(source_pivot.columns), axis=1)
            
            # Format as currency
            formatted_pivot = source_pivot.applymap('${:,.2f}'.format)
            
            st.dataframe(formatted_pivot, use_container_width=True)
            
            # Show a breakdown by source and category
            st.write("### Category Breakdown by Source")
            
            # Create pivot table by source and category
            source_category_pivot = pd.pivot_table(
                display_data,
                values='Amount',
                index=['Source', 'Category'],
                aggfunc='sum',
                fill_value=0
            )
            
            # Sort by total amount spent (descending)
            source_category_pivot = source_category_pivot.sort_values('Amount', ascending=False)
            
            # Format as currency
            formatted_source_category = source_category_pivot.applymap('${:,.2f}'.format)
            
            st.dataframe(formatted_source_category, use_container_width=True)
        
        # Logout option
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.data = None
            st.session_state.categories = None
            st.session_state.category_pivot = None
            st.session_state.merchant_pivot = None
            st.session_state.category_merchant_pivot = None
            st.session_state.date_filter = None
            st.rerun()


if __name__ == "__main__":
    main()
