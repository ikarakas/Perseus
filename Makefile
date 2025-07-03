# SBOM Generation Platform Makefile

.PHONY: build up down logs clean test help

# Default target
help:
	@echo "Available targets:"
	@echo "  build    - Build all Docker containers"
	@echo "  up       - Start all services"
	@echo "  down     - Stop all services"
	@echo "  logs     - Show logs from all services"
	@echo "  clean    - Remove all containers and volumes"
	@echo "  test     - Run tests"
	@echo "  help     - Show this help message"

# Build all containers
build:
	docker-compose build --no-cache

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Clean up
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	python -m pytest tests/ -v

# Quick start (build and run)
start: build up
	@echo "SBOM Platform started. API available at http://localhost:8080"
	@echo "Use 'make logs' to view logs"

# Check status
status:
	docker-compose ps