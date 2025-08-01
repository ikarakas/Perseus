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

# Install Grype for vulnerability scanning
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Set environment variables for tool paths
ENV SYFT_PATH=/usr/local/bin/syft
ENV GRYPE_PATH=/usr/local/bin/grype
ENV CONTAINER_ENV=true

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

# Wait for database to be ready
echo "Waiting for database connection..."
while ! python -c "from src.database import test_connection; exit(0 if test_connection() else 1)" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done

# Initialize database tables
echo "Initializing database..."
python scripts/init_database.py

# Start main API server with integrated telemetry server and better concurrency
echo "Starting integrated API and telemetry server..."
# Use single worker to avoid telemetry port conflicts and session storage issues
# TODO: Implement Redis for session storage to support multiple workers
WORKERS=${UVICORN_WORKERS:-1}
echo "Starting with $WORKERS worker(s)..."

python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 \
  --workers $WORKERS \
  --timeout-keep-alive 5 \
  --timeout-graceful-shutdown 10 \
  --loop asyncio \
  --access-log \
  --log-level info
EOF

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]