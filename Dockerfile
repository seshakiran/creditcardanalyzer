FROM python:3.11-slim

# Install required system dependencies for Selenium and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-app.txt

# Create directory for secure credential storage
RUN mkdir -p /root/.amex_analyzer

# Expose the Streamlit port
EXPOSE 5000

# Set environment variables for Chrome WebDriver
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0", "--server.headless=true"]