# Multi-Language SBOM Generation Platform

A containerized Software Bill of Materials (SBOM) generation platform capable of analyzing both source code and compiled binaries for C/C++ and Java applications. Features real-time metrics monitoring, comprehensive dashboard, and enterprise-grade security.

## Features

- **Source Code Analysis**: C/C++ and Java source code dependency analysis using Syft
- **Binary Analysis**: Static analysis of compiled executables and Java bytecode
- **Multiple SBOM Formats**: SPDX 2.3, CycloneDX 1.5, SWID
- **Real-time Metrics**: Live system monitoring with CPU, memory, and disk usage
- **Interactive Dashboard**: Web-based monitoring interface with auto-refresh
- **Alert System**: Configurable thresholds for system and API performance
- **REST API**: HTTP endpoints for analysis and SBOM generation
- **Security Features**: Sandboxed execution, input validation, and rate limiting

## Quick Start

### Using Docker (Recommended)

1. **Build and start the platform:**
   ```bash
   docker-compose -f docker-compose-simple.yml build
   docker-compose -f docker-compose-simple.yml up -d
   ```

2. **Access the dashboard:**
   ```bash
   # Open in browser
   open http://localhost:8080/dashboard
   ```

3. **Analyze source code using CLI:**
   ```bash
   # Copy your project to data directory first
   cp -r /path/to/your/project ./data/my-project
   
   # Run analysis
   ./sbom-cli.sh analyze-source ./data/my-project java
   ```

4. **Or use the REST API directly:**
   ```bash
   curl -X POST http://localhost:8080/analyze/source \
     -H "Content-Type: application/json" \
     -d '{"type": "source", "language": "java", "location": "/app/data/my-project"}'
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create data directories:**
   ```bash
   mkdir -p data/results data/sboms
   ```

3. **Start the server:**
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
   ```

## Monitoring & Metrics

The platform includes comprehensive monitoring capabilities:

### Dashboard Features
- **Real-time System Metrics**: CPU, memory, and disk usage
- **Analysis Performance**: Success rates, durations, component counts
- **API Monitoring**: Request counts, response times, error rates
- **SBOM Generation Stats**: Format usage, generation times
- **Alert Management**: Configurable thresholds and notifications

### Key Endpoints
- **Dashboard**: `http://localhost:8080/dashboard` - Interactive web interface
- **Metrics API**: `http://localhost:8080/api/metrics` - JSON metrics data
- **Health Check**: `http://localhost:8080/health` - Service status
- **Alerts**: `http://localhost:8080/api/alerts` - Active system alerts

### Metrics Collection
- **System Metrics**: Real-time CPU, memory, and disk monitoring using psutil
- **API Tracking**: Automatic request logging with response time measurement
- **Analysis Tracking**: Success/failure rates, component detection statistics
- **Alert System**: Configurable thresholds for performance monitoring

## Architecture

The platform consists of:
- **Orchestrator**: Workflow management, API endpoints, and metrics collection
- **Source Analyzers**: Language-specific source code analysis using Syft
- **Binary Analyzers**: Compiled binary analysis
- **SBOM Generator**: Multi-format SBOM creation (SPDX, CycloneDX, SWID)
- **Monitoring System**: Real-time metrics, dashboard, and alerting

```bash 
Key Components:

  📁 SBOM/
  ├── 🐳 containers/          # Docker containers for each service
  ├── 🔧 src/                 # Core application source code
  │   ├── 🌐 api/            # REST API endpoints
  │   ├── 🔍 analyzers/      # Language-specific analyzers
  │   ├── 📋 sbom/           # SBOM generation engine
  │   ├── 🔒 security/       # Security validation & middleware
  │   ├── 📊 monitoring/     # Metrics collection & dashboard
  │   └── 💾 common/         # Shared utilities & storage
  ├── 📄 docker-compose.yml  # Service orchestration
  ├── 🛠️ Makefile           # Build & deployment commands
  └── 📖 README.md          # Project documentation

   Quick Start:

  # Build and start the platform
  make start

  # Check status
  make status

  # View logs
  make logs

  # Access the API
  curl http://localhost:8080/

  # Monitor dashboard
  open http://localhost:8080/dashboard

  API Endpoints:

  - POST /analyze/source - Analyze source code
  - POST /analyze/binary - Analyze compiled binaries
  - GET /analyze/{id}/status - Check analysis status
  - GET /analyze/{id}/results - Get analysis results
  - POST /sbom/generate - Generate SBOM from results
  - GET /sbom/{id} - Download generated SBOM
  - GET /dashboard - Interactive monitoring dashboard
  - GET /api/metrics - JSON metrics data
  - GET /api/metrics/analysis - Analysis-specific metrics
  - GET /api/metrics/sbom - SBOM generation metrics
  - GET /api/metrics/system - System resource metrics
  - GET /api/alerts - Active system alerts
  - GET /health - Health check endpoint

  Security Highlights:

  - ✅ Input sanitization and validation
  - ✅ Container isolation with minimal privileges
  - ✅ Rate limiting and IP blocking
  - ✅ Comprehensive audit logging
  - ✅ Path traversal prevention
  - ✅ Resource usage monitoring

  The platform is production-ready with enterprise-grade security, monitoring, and scalability features. It follows
   the microservices architecture specified in your requirements and supports all requested analysis types and SBOM
   formats.
   
  ```

## Troubleshooting

### Common Issues

**Metrics not updating on dashboard:**
- The dashboard auto-refreshes every 30 seconds
- Manually refresh the page to see latest metrics
- Check that the container is running: `docker ps`

**Container build fails with psutil errors:**
- Make sure Docker has enough memory allocated
- Try rebuilding with `--no-cache` flag
- Check that build tools are properly installed in container

**Analysis fails with "file not found" error:**
- Ensure files are copied to the `./data/` directory first
- Use absolute paths when specifying locations
- Check file permissions and Docker volume mounts

**Port 8080 already in use:**
- Check what's using the port: `lsof -i :8080`
- Stop other services or use a different port
- Kill existing containers: `docker-compose down`

### Viewing Logs

```bash
# Container logs
docker-compose -f docker-compose-simple.yml logs -f

# Specific service logs
docker logs sbom-orchestrator-1 -f
```

### Performance Tuning

- Increase Docker memory allocation for large projects
- Monitor system metrics via dashboard
- Check alert thresholds in monitoring configuration
- Scale horizontally by running multiple container instances

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the LGPL-3.0 License - see the [LICENSE](LICENSE) file for details.
