import os
import streamlit as st
import pandas as pd
import datetime
import tempfile
from dotenv import load_dotenv

# Import custom modules
from amex_scraper import AmexScraper
from data_processor import categorize_transactions, create_pivot_table
from visualizer import plot_spending_by_category, plot_spending_over_time
from utils import load_credentials, encrypt_credentials, decrypt_credentials, save_credentials

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
if 'pivot_data' not in st.session_state:
    st.session_state.pivot_data = None
if 'date_filter' not in st.session_state:
    st.session_state.date_filter = None


def main():
    # Sidebar
    with st.sidebar:
        st.title("Amex Statement Analyzer")
        st.write("Analyze your American Express statements with ease.")
        
        # Date range selector
        st.subheader("Date Range")
        today = datetime.date.today()
        one_year_ago = today - datetime.timedelta(days=365)
        
        start_date = st.date_input("Start date", one_year_ago)
        end_date = st.date_input("End date", today)
        
        if st.button("Apply Date Filter") and st.session_state.data is not None:
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
                        file_name="amex_transactions.csv",
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
                            file_name="amex_transactions.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    # Main content
    if not st.session_state.authenticated:
        st.title("Login to American Express")
        
        # Try to load saved credentials
        saved_credentials = load_credentials()
        
        use_saved = False
        if saved_credentials:
            use_saved = st.checkbox("Use saved credentials", value=True)
        
        if use_saved and saved_credentials:
            username = saved_credentials["username"]
            password = "********"  # Masked for security
            st.info(f"Using saved credentials for {username}")
        else:
            username = st.text_input("Username/Email")
            password = st.text_input("Password", type="password")
            save_creds = st.checkbox("Save credentials securely", value=False)
        
        download_months = st.slider("Number of months to download", min_value=1, max_value=12, value=6)
        
        if st.button("Login & Download Statements"):
            with st.spinner("Logging in to American Express..."):
                try:
                    # Initialize the scraper
                    scraper = AmexScraper()
                    
                    # Use saved credentials if selected
                    if use_saved and saved_credentials:
                        decrypted_password = decrypt_credentials(saved_credentials["password"])
                        success, data = scraper.login_and_download(saved_credentials["username"], decrypted_password, download_months)
                    else:
                        success, data = scraper.login_and_download(username, password, download_months)
                        
                        # Save credentials if requested
                        if save_creds and success:
                            encrypted_password = encrypt_credentials(password)
                            save_credentials({"username": username, "password": encrypted_password})
                    
                    if success:
                        st.session_state.data = data
                        
                        # Categorize transactions
                        st.session_state.data, st.session_state.categories = categorize_transactions(data)
                        
                        # Create pivot table
                        st.session_state.pivot_data = create_pivot_table(st.session_state.data)
                        
                        st.session_state.authenticated = True
                        st.success("Login successful! Statement data downloaded.")
                        st.rerun()
                    else:
                        st.error("Failed to login or download statements. Please check your credentials.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    else:
        # Display data analysis after authentication
        st.title("Amex Statement Analysis")
        
        # Use filtered data if available, otherwise use all data
        display_data = st.session_state.date_filter if st.session_state.date_filter is not None else st.session_state.data
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", len(display_data))
        with col2:
            st.metric("Total Spend", f"${display_data['Amount'].sum():.2f}")
        with col3:
            st.metric("Average Transaction", f"${display_data['Amount'].mean():.2f}")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["Transactions", "Pivot Table", "Visualizations"])
        
        with tab1:
            st.subheader("Transaction Data")
            st.dataframe(display_data, use_container_width=True)
        
        with tab2:
            st.subheader("Expense Pivot Table")
            
            # Recalculate pivot if date filter is applied
            if st.session_state.date_filter is not None:
                pivot_data = create_pivot_table(display_data)
            else:
                pivot_data = st.session_state.pivot_data
                
            st.dataframe(pivot_data, use_container_width=True)
        
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
        
        # Logout option
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.data = None
            st.session_state.categories = None
            st.session_state.pivot_data = None
            st.session_state.date_filter = None
            st.rerun()


if __name__ == "__main__":
    main()
