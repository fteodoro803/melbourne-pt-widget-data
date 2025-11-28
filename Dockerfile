# Python version
FROM python:3.12-slim

# Working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Run the app with gunicorn
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 60 main:app