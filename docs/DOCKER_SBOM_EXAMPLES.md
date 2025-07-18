# Docker Image SBOM Generation Examples

This document provides examples of how to use the Docker image SBOM generation feature.

## API Endpoint

The platform now supports Docker image analysis through the `/analyze/docker` endpoint.

## Basic Docker Image Analysis

### Analyze a Docker Hub Image

```bash
curl -X POST http://localhost:8000/analyze/docker \
  -H "Content-Type: application/json" \
  -d '{
    "type": "docker",
    "location": "nginx:latest",
    "options": {
      "deep_scan": true
    }
  }'
```

### Analyze a Specific Version

```bash
curl -X POST http://localhost:8000/analyze/docker \
  -H "Content-Type: application/json" \
  -d '{
    "type": "docker",
    "location": "python:3.9-slim",
    "options": {
      "deep_scan": false
    }
  }'
```

## Private Registry Images

### With Basic Authentication

```bash
curl -X POST http://localhost:8000/analyze/docker \
  -H "Content-Type: application/json" \
  -d '{
    "type": "docker",
    "location": "registry.example.com/myapp:v1.0",
    "options": {
      "deep_scan": true,
      "docker_auth": {
        "registry": "registry.example.com",
        "username": "myuser",
        "password": "mypassword"
      }
    }
  }'
```

### Using Existing Docker Config

```bash
curl -X POST http://localhost:8000/analyze/docker \
  -H "Content-Type: application/json" \
  -d '{
    "type": "docker",
    "location": "private.registry.io/team/service:production",
    "options": {
      "docker_auth": {
        "config_path": "/home/user/.docker"
      }
    }
  }'
```

## Image Reference Formats

The platform supports various Docker image reference formats:

1. **Simple image name** (uses latest tag from Docker Hub):
   - `nginx`
   - `redis`

2. **Image with tag**:
   - `nginx:1.21`
   - `python:3.9-alpine`

3. **Image with digest**:
   - `nginx@sha256:1234567890abcdef...`

4. **Full registry path**:
   - `registry.example.com/namespace/image:tag`
   - `gcr.io/project/image:version`

5. **Docker prefix** (optional):
   - `docker:nginx:latest`
   - `docker:alpine:3.14`

## Analysis Options

- **deep_scan**: When `true`, analyzes all image layers. When `false`, only analyzes the squashed image.
- **timeout_minutes**: Custom timeout for large images (default: 30 minutes, Docker images use 10 minutes by default)
- **docker_auth**: Authentication configuration for private registries

## Check Analysis Status

```bash
# Get the analysis_id from the initial response
curl http://localhost:8000/analyze/{analysis_id}/status
```

## Get Analysis Results

```bash
curl http://localhost:8000/analyze/{analysis_id}/results
```

## Generate SBOM from Docker Analysis

Once the Docker image analysis is complete, generate an SBOM:

```bash
curl -X POST http://localhost:8000/sbom/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_ids": ["docker-analysis-id-here"],
    "format": "spdx",
    "include_licenses": true,
    "include_vulnerabilities": true
  }'
```

## Common Use Cases

### 1. Security Scanning Base Images

```bash
# Analyze common base images
for image in "alpine:latest" "ubuntu:22.04" "node:18-alpine"; do
  curl -X POST http://localhost:8000/analyze/docker \
    -H "Content-Type: application/json" \
    -d "{\"type\": \"docker\", \"location\": \"$image\"}"
done
```

### 2. CI/CD Pipeline Integration

```bash
# In your CI/CD pipeline
IMAGE_TAG="myapp:${CI_COMMIT_SHA}"

# Build and push image
docker build -t $IMAGE_TAG .
docker push $IMAGE_TAG

# Generate SBOM
ANALYSIS_RESPONSE=$(curl -X POST http://localhost:8000/analyze/docker \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"docker\", \"location\": \"$IMAGE_TAG\"}")

ANALYSIS_ID=$(echo $ANALYSIS_RESPONSE | jq -r '.analysis_id')

# Wait for completion and get SBOM
# ... (polling logic here)
```

### 3. Comparing Different Versions

```bash
# Analyze multiple versions of the same image
for version in "1.20" "1.21" "1.22"; do
  curl -X POST http://localhost:8000/analyze/docker \
    -H "Content-Type: application/json" \
    -d "{\"type\": \"docker\", \"location\": \"nginx:$version\"}"
done
```

## Error Handling

Common errors and their meanings:

- **404 "Docker image not found"**: The specified image doesn't exist or cannot be pulled
- **401 "Docker authentication failed"**: Invalid credentials for private registry
- **408 "Docker pull timeout"**: Image download took too long (large images or slow connection)
- **400 "Invalid Docker image reference"**: The image reference format is incorrect

## Best Practices

1. **Use specific tags**: Avoid using `latest` in production; use specific version tags
2. **Cache results**: Store SBOM results for frequently used base images
3. **Regular updates**: Re-analyze images periodically to catch new vulnerabilities
4. **Layer analysis**: Use `deep_scan: true` for comprehensive component discovery
5. **Authentication**: Use Docker config path method for better security in production

## Limitations

- Requires Docker daemon access or ability to pull images
- Large images may take significant time to analyze
- Network connectivity required for remote registry images
- Some proprietary package formats may not be detected