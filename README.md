# Credit Card Statement Analyzer

A secure application that analyzes statements from multiple banks (American Express, Chase, Discover, and more), categorizes expenses, and creates interactive pivot tables for financial analysis - without risking your account security.

## Features

- **Multi-Bank Support**: Analyze statements from American Express, Chase, Discover, and other banks
- **Statement Import**: Easily import multiple statement files at once
- **Auto-Detection**: Automatically finds recent statement downloads in your Downloads folder
- **Flexible Time Periods**: Select from predefined time periods or custom date ranges
- **Transaction Categorization**: Automatically categorizes spending across all your cards
- **Merchant Analysis**: View spending by merchant within each category
- **Source Tracking**: See which card was used for each transaction
- **Collapsible Categories**: Expand/collapse categories to see merchant details
- **Visualization**: Interactive charts and pivot tables
- **Data Security**: All processing happens locally on your machine
- **Export Options**: Export analyzed data to CSV or Excel

## Running Locally with Docker

For maximum security and privacy, you can run this application on your local machine using Docker. This ensures all your financial data stays on your computer.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Setup

1. Clone this repository to your local machine
2. Navigate to the project directory
3. Run the application:

```bash
docker-compose up
```

4. Open your browser and go to `http://localhost:5000`

### Security Features

- No automated logins to bank websites - you download your own statements
- Zero risk of account lockout due to suspicious login activity
- All data processing happens locally on your machine
- Transaction data is not persistently stored unless you export it
- No credentials required - just your statement files

## Configuration

If you want to customize the application, you can:

1. Create a `.env` file based on `.env.example` to set environment variables
2. Modify the Docker Compose file to change ports or volume mapping
3. Adjust your browser's download settings to control where exported files are saved

## Usage

1. Log in to your bank accounts (American Express, Chase, Discover, etc.)
2. Download your statement(s) in CSV, OFX, or QFX format
   - Usually found in the "Statements & Activity" section
   - Look for "Download" or "Export" options
3. Launch the Credit Analyzer application
4. Either:
   - Upload multiple statement files at once, or
   - Let the app automatically find recent statement downloads
5. Select a time period (Last 30 days, This month, Last quarter, etc.) or use a custom date range
6. Explore the analysis in the different tabs:
   - Transactions: Raw transaction data from all sources
   - Pivot Table: Expense analysis by category, merchant, and month
   - Visualizations: Charts showing spending patterns
   - Source Summary: Breakdown of spending by card/bank source
7. Use the collapsible category view to drill down into merchant details
8. Export analyzed data as needed in CSV or Excel format

## Notes on Data Privacy

This application prioritizes your data privacy:
- No data is sent to third-party servers
- Data is processed in-memory and is cleared when you log out
- When running locally via Docker, all processing stays on your machine