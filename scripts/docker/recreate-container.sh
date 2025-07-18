#!/bin/bash

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
docker-compose -f docker-compose-simple.yml down

# Rebuild and start the container
echo "Building and starting sbom-platform container..."
docker-compose -f docker-compose-simple.yml up -d --build

# Check status
echo "Checking container status..."
docker-compose -f docker-compose-simple.yml ps