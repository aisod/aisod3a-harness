# AISOD 3A Harness — Docker deployment
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY aisod3a_harness.py .
COPY api_server.py .

# Expose the API port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
