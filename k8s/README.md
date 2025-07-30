# Perseus Kubernetes Deployment

This directory contains Kubernetes manifests for deploying Perseus SBOM Platform in production environments.

## Overview

Perseus supports three deployment tiers:

1. **Development**: `docker-compose.yml` (single node, easy setup)
2. **Production Docker**: `docker-compose.prod.yml` (multi-replica, external DB)
3. **Kubernetes**: `k8s/` (production-grade with HA, auto-scaling)

## Quick Start

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=perseus

# Access the application
kubectl port-forward svc/perseus-api 8000:8000
```

## Components

- `namespace.yaml` - Dedicated namespace for Perseus
- `postgres.yaml` - PostgreSQL StatefulSet with persistent storage
- `api.yaml` - Perseus API deployment with multiple replicas
- `background-jobs.yaml` - Background task processors
- `services.yaml` - Service definitions for load balancing
- `ingress.yaml` - Optional ingress configuration

## Configuration

All configuration is managed through ConfigMaps and Secrets. See individual manifests for environment variables and customization options.

## Monitoring

Health checks are configured for all components:
- Readiness probes ensure pods are ready to receive traffic
- Liveness probes restart unhealthy containers
- Resource limits prevent resource exhaustion

## Scaling

Perseus API pods can be scaled horizontally:

```bash
kubectl scale deployment perseus-api --replicas=5
```

Background job processors can also be scaled based on workload.