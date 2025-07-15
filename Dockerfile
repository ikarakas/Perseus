FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Syft for Docker image analysis
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Install Docker CLI for Docker daemon communication
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz | tar -xzC /usr/local/bin --strip=1 docker/docker

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for file uploads
RUN mkdir -p /app/data

# Create telemetry data directory
RUN mkdir -p /app/telemetry_data

# Expose ports
EXPOSE 8000 9876

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting SBOM Platform..."

# Set Python path to include the app directory
export PYTHONPATH="/app:$PYTHONPATH"

# Start main API server with integrated telemetry server
echo "Starting integrated API and telemetry server..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]