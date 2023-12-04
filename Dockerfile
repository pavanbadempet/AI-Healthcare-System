# Use slim python image for smaller size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (gcc for building some python libs if needed, curl for healthcheck)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose ports for both services (documentation only)
EXPOSE 8000
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["bash"]
