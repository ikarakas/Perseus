#!/bin/bash
# Docker startup script for SBOM Platform

echo "🚀 Starting SBOM Platform with Docker..."

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose down

# Create required directories
echo "Creating required directories..."
mkdir -p data logs telemetry_data

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Main API is running at http://localhost:8000"
else
    echo "❌ Main API is not responding"
fi

if nc -z localhost 9876; then
    echo "✅ Telemetry server is running on port 9876"
else
    echo "❌ Telemetry server is not responding"
fi

# Show logs
echo ""
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "📡 API Docs: http://localhost:8000/docs"
echo "🔍 Telemetry API: http://localhost:8000/telemetry/status"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""

# Find Docker host IP for agent configuration
echo "🖥️  For VM agent configuration:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   Use host: host.docker.internal (Docker Desktop)"
    echo "   Or use your Mac IP: $(ipconfig getifaddr en0 || ipconfig getifaddr en1)"
else
    DOCKER_IP=$(docker network inspect bridge | grep Gateway | awk '{print $2}' | tr -d '",' | head -1)
    echo "   Use host: $DOCKER_IP (Docker bridge gateway)"
fi

echo ""
echo "📦 Deploy agent package: telemetry-agent-docker.tar.gz"