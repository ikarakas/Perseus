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
	@echo "📦 Creating namespace..."
	kubectl apply -f k8s/namespace.yaml
	@echo "⏳ Waiting for namespace to be ready..."
	@sleep 2
	@echo "🚀 Deploying all resources..."
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

# Advanced Kubernetes operations
k8s-logs:
	@echo "📋 Perseus Kubernetes Logs"
	@echo "========================="
	@echo ""
	@echo "API logs:"
	kubectl logs -n perseus -l app=perseus-api --tail=50
	@echo ""
	@echo "Background job logs:"
	kubectl logs -n perseus -l app=perseus-background-jobs --tail=20

k8s-scale:
	@read -p "Number of API replicas (current: 3): " api_replicas; \
	read -p "Number of background job replicas (current: 2): " job_replicas; \
	kubectl scale deployment perseus-api -n perseus --replicas=$$api_replicas; \
	kubectl scale deployment perseus-background-jobs -n perseus --replicas=$$job_replicas; \
	echo "✅ Scaled to $$api_replicas API replicas and $$job_replicas background job replicas"

k8s-restart:
	@echo "🔄 Restarting Perseus deployments..."
	kubectl rollout restart deployment -n perseus
	@echo "✅ All deployments restarted"

k8s-db-backup:
	@echo "💾 Backing up Perseus database..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	kubectl exec -n perseus postgres-0 -- pg_dump -U sbom_user sbom_platform > backup_$$timestamp.sql; \
	echo "✅ Database backed up to backup_$$timestamp.sql"

k8s-db-shell:
	@echo "🐘 Connecting to PostgreSQL shell..."
	kubectl exec -it -n perseus postgres-0 -- psql -U sbom_user -d sbom_platform

k8s-port-forward:
	@echo "🔌 Starting port forwarding..."
	@echo "Perseus will be available at http://localhost:8001"
	kubectl port-forward -n perseus svc/perseus-api 8001:8000

# Development shortcuts
analyze-docker:
	@echo "🔍 Analyzing Docker image with Perseus..."
	@read -p "Docker image to analyze: " image; \
	curl -X POST http://localhost:8000/analyze/docker \
		-H "Content-Type: application/json" \
		-d "{\"image_name\": \"$$image\"}" | jq

analyze-source:
	@echo "📁 Analyzing source code with Perseus..."
	@read -p "Source path: " path; \
	read -p "Language (java/python/go): " lang; \
	curl -X POST http://localhost:8000/analyze/source \
		-H "Content-Type: application/json" \
		-d "{\"location\": \"$$path\", \"type\": \"source\", \"language\": \"$$lang\"}" | jq

# Quick analysis of common targets
analyze-nginx:
	@echo "🔍 Analyzing nginx:latest..."
	@curl -X POST http://localhost:8000/analyze/docker \
		-H "Content-Type: application/json" \
		-d '{"image_name": "nginx:latest"}' | jq

analyze-python:
	@echo "🔍 Analyzing python:3.11-slim..."
	@curl -X POST http://localhost:8000/analyze/docker \
		-H "Content-Type: application/json" \
		-d '{"image_name": "python:3.11-slim"}' | jq

# Database operations
db-stats:
	@echo "📊 Database Statistics"
	@echo "===================="
	@if [ -z "$$(docker-compose ps -q postgres 2>/dev/null)" ]; then \
		kubectl exec -n perseus postgres-0 -- psql -U sbom_user -d sbom_platform -c \
			"SELECT 'Components' as type, COUNT(*) from components \
			UNION ALL SELECT 'Vulnerabilities', COUNT(*) from vulnerabilities \
			UNION ALL SELECT 'Analyses', COUNT(*) from analyses \
			UNION ALL SELECT 'SBOMs', COUNT(*) from sboms;"; \
	else \
		docker-compose exec postgres psql -U sbom_user -d sbom_platform -c \
			"SELECT 'Components' as type, COUNT(*) from components \
			UNION ALL SELECT 'Vulnerabilities', COUNT(*) from vulnerabilities \
			UNION ALL SELECT 'Analyses', COUNT(*) from analyses \
			UNION ALL SELECT 'SBOMs', COUNT(*) from sboms;"; \
	fi

db-clean-orphans:
	@echo "🧹 Cleaning orphan vulnerabilities..."
	@curl -X POST http://localhost:8000/api/v1/counts/cleanup/orphans | jq

# Monitoring
watch-pods:
	@echo "👁️  Watching Perseus pods..."
	watch -n 2 "kubectl get pods -n perseus"

watch-resources:
	@echo "📊 Watching resource usage..."
	kubectl top pods -n perseus

# Quick checks
check-api:
	@echo "🏥 Health check:"
	@curl -s http://localhost:8000/health | jq || curl -s http://localhost:8080/health | jq

check-version:
	@echo "📌 Perseus version:"
	@curl -s http://localhost:8000/api/v1/version | jq || curl -s http://localhost:8080/api/v1/version | jq

# Help sections
help-dev:
	@echo "🛠️  Development Commands"
	@echo "====================="
	@echo "  make analyze-docker    - Analyze a Docker image"
	@echo "  make analyze-source    - Analyze source code"
	@echo "  make db-stats         - Show database statistics"
	@echo "  make db-clean-orphans - Clean orphan vulnerabilities"
	@echo "  make check-api        - Quick health check"
	@echo "  make logs             - View application logs"

help-k8s:
	@echo "☸️  Kubernetes Commands"
	@echo "===================="
	@echo "  make k8s-logs         - View K8s logs"
	@echo "  make k8s-scale        - Scale deployments"
	@echo "  make k8s-restart      - Restart all pods"
	@echo "  make k8s-db-backup    - Backup database"
	@echo "  make k8s-db-shell     - PostgreSQL shell"
	@echo "  make k8s-port-forward - Forward to localhost:8001"
	@echo "  make watch-pods       - Watch pod status"