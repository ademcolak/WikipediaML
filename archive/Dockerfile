# WikipediaML Training - Docker Image
# Optimized for cloud training with GPU support

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_ML=true
ENV VERBOSE=true

# Default command - can be overridden
CMD ["python", "train_ml_model_curated.py"]