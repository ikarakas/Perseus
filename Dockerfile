FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

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

# Start telemetry server in background
echo "Starting telemetry server..."
python scripts/utility/run_telemetry_server.py &
TELEMETRY_PID=$!

# Wait a moment for telemetry server to start
sleep 2

# Start main API server
echo "Starting main API server..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# If main API exits, kill telemetry server
kill $TELEMETRY_PID 2>/dev/null || true
EOF

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]