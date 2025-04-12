# Amex Statement Analyzer

A secure application that retrieves American Express statements, categorizes expenses, and creates interactive pivot tables for financial analysis.

## Features

- **Secure Login**: Connects to American Express to download statements
- **Transaction Categorization**: Automatically categorizes spending
- **Visualization**: Interactive charts and pivot tables
- **Data Security**: In-memory processing with optional encrypted credential storage
- **Export Options**: Export data to CSV or Excel

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

- Your American Express credentials are never stored in plain text
- All data processing happens in memory
- Transaction data is not persistently stored unless you export it
- Optional encrypted credential storage with secure key generation

## Configuration

If you want to customize the application, you can:

1. Create a `.env` file based on `.env.example` to set environment variables
2. Modify the Docker Compose file to change ports or volume mapping
3. Adjust your browser's download settings to control where exported files are saved

## Usage

1. Log in with your American Express credentials
2. Select how many months of statements to download
3. Optionally save credentials (securely encrypted)
4. Filter data by date range if needed
5. Explore the analysis in the different tabs:
   - Transactions: Raw transaction data
   - Pivot Table: Expense analysis by category and month
   - Visualizations: Charts showing spending patterns
6. Export data as needed in CSV or Excel format

## Notes on Data Privacy

This application prioritizes your data privacy:
- No data is sent to third-party servers
- Data is processed in-memory and is cleared when you log out
- When running locally via Docker, all processing stays on your machine