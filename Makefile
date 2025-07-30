# Perseus SBOM Platform - Multi-tier Deployment Makefile
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0

.PHONY: help dev prod k8s-deploy k8s-clean docker-build test clean

# Default target
help:
	@echo "Perseus SBOM Platform - Deployment Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Start development environment (docker-compose)"
	@echo "  make dev-clean   - Clean development environment"
	@echo ""
	@echo "Production Docker:"
	@echo "  make prod        - Start production Docker environment"
	@echo "  make prod-clean  - Clean production Docker environment"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy  - Deploy to Kubernetes"
	@echo "  make k8s-clean   - Clean Kubernetes deployment"
	@echo "  make k8s-status  - Check Kubernetes deployment status"
	@echo ""
	@echo "Utilities:"
	@echo "  make build       - Build Docker images"
	@echo "  make test        - Run verification tests"
	@echo "  make clean       - Clean all environments"

# Development environment (default)
dev:
	@echo "🚀 Starting Perseus development environment..."
	docker-compose up -d
	@echo "✅ Development environment started"
	@echo "📊 Dashboard: http://localhost:8000/dashboard"

dev-clean:
	@echo "🧹 Cleaning development environment..."
	docker-compose down -v
	docker system prune -f

# Production Docker environment
prod:
	@echo "🚀 Starting Perseus production environment..."
	@if [ ! -f docker-compose.prod.yml ]; then \
		echo "⚠️  docker-compose.prod.yml not found. Creating from template..."; \
		cp docker-compose.yml docker-compose.prod.yml; \
		echo "📝 Please edit docker-compose.prod.yml for production settings"; \
	fi
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

prod-clean:
	@echo "🧹 Cleaning production environment..."
	docker-compose -f docker-compose.prod.yml down -v

# Kubernetes deployment
k8s-deploy: build
	@echo "🚀 Deploying Perseus to Kubernetes..."
	@if ! kubectl cluster-info > /dev/null 2>&1; then \
		echo "❌ No Kubernetes cluster found. Please connect to a cluster first."; \
		exit 1; \
	fi
	kubectl apply -f k8s/
	@echo "✅ Perseus deployed to Kubernetes"
	@echo "🔍 Check status with: make k8s-status"
	@echo "🌐 Access via: kubectl port-forward -n perseus svc/perseus-api 8000:8000"

k8s-clean:
	@echo "🧹 Cleaning Kubernetes deployment..."
	kubectl delete -f k8s/ --ignore-not-found=true
	@echo "✅ Kubernetes deployment cleaned"

k8s-status:
	@echo "📊 Perseus Kubernetes Status"
	@echo "============================"
	@echo ""
	@echo "Namespace:"
	kubectl get namespace perseus 2>/dev/null || echo "  ❌ perseus namespace not found"
	@echo ""
	@echo "Deployments:"
	kubectl get deployments -n perseus 2>/dev/null || echo "  ❌ No deployments found"
	@echo ""
	@echo "Pods:"
	kubectl get pods -n perseus 2>/dev/null || echo "  ❌ No pods found"
	@echo ""
	@echo "Services:"
	kubectl get services -n perseus 2>/dev/null || echo "  ❌ No services found"

# Build Docker images
build:
	@echo "🔨 Building Perseus Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

# Run verification tests
test:
	@echo "🧪 Running Perseus verification tests..."
	@if ! curl -s http://localhost:8000/health > /dev/null; then \
		echo "❌ Perseus API not running. Start with 'make dev' first."; \
		exit 1; \
	fi
	cd tests && python3 comprehensive_verification.py
	@echo "✅ Verification tests completed"

# Clean all environments
clean: dev-clean prod-clean k8s-clean
	@echo "🧹 Cleaning Docker system..."
	docker system prune -f
	@echo "✅ All environments cleaned"

# Quick status check
status:
	@echo "📊 Perseus System Status"
	@echo "======================="
	@echo ""
	@echo "Docker Compose (Development):"
	@if docker-compose ps | grep -q "Up"; then \
		echo "  ✅ Running"; \
		docker-compose ps; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo ""
	@echo "Kubernetes:"
	@if kubectl get namespace perseus > /dev/null 2>&1; then \
		echo "  ✅ Deployed"; \
		make k8s-status; \
	else \
		echo "  ❌ Not deployed"; \
	fi

# Legacy aliases for backward compatibility
up: dev
down: dev-clean
logs:
	docker-compose logs -f
start: build dev