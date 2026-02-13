FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media directories
RUN mkdir -p media_store/uploads media_store/thumbnails

EXPOSE 8000

# Default: run both bot and web app
CMD ["python", "main.py"]
