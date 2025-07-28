#!/bin/bash
# Update vulnerability database script

echo "🔄 Updating vulnerability database..."

if command -v docker-compose &> /dev/null; then
    # If using Docker
    echo "Using Docker container..."
    docker-compose -f docker-compose.dev.yml exec sbom-platform grype db update
    docker-compose -f docker-compose.dev.yml exec sbom-platform grype db status
elif command -v grype &> /dev/null; then
    # If Grype installed locally
    echo "Using local Grype installation..."
    grype db update
    grype db status
else
    echo "❌ Neither Docker nor local Grype found!"
    exit 1
fi

echo "✅ Vulnerability database updated!"