#!/bin/bash

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
docker-compose down

# Rebuild and start the container
echo "Building and starting sbom-platform container..."
docker-compose up -d --build

# Check status
echo "Checking container status..."
docker-compose ps