# Use Python 3.12
FROM python:3.12-slim

# Install system dependencies including SSL certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
    libssl-dev && \
    rm -rf /var/lib/apt/lists/* && \
    update-ca-certificates

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Functions Framework for running Cloud Functions
RUN pip install --no-cache-dir functions-framework==3.*

# Copy all application code
COPY . .

# Cloud Run provides PORT environment variable
ENV PORT=8080

# Run the function using Functions Framework
CMD exec functions-framework --target=cloud_update_gtfs --port=$PORT