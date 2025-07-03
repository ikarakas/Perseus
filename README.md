# Multi-Language SBOM Generation Platform

A containerized Software Bill of Materials (SBOM) generation platform capable of analyzing both source code and compiled binaries for C/C++ and Java applications.

## Features

- **Source Code Analysis**: C/C++ and Java source code dependency analysis
- **Binary Analysis**: Static analysis of compiled executables and Java bytecode
- **Multiple SBOM Formats**: SPDX 2.3, CycloneDX 1.5, SWID
- **Container-based Architecture**: Microservices design with Docker containers
- **REST API**: HTTP endpoints for analysis and SBOM generation
- **Security Features**: Sandboxed execution and input validation

## Quick Start

1. Build containers:
   ```bash
   docker-compose build
   ```

2. Start the platform:
   ```bash
   docker-compose up -d
   ```

3. Submit source code for analysis:
   ```bash
   curl -X POST http://localhost:8080/analyze/source \
     -H "Content-Type: application/json" \
     -d '{"type": "source", "language": "java", "location": "file:///path/to/project"}'
   ```

## Architecture

The platform consists of:
- **Orchestrator**: Workflow management and API endpoints
- **Source Analyzers**: Language-specific source code analysis
- **Binary Analyzers**: Compiled binary analysis
- **SBOM Generator**: Multi-format SBOM creation

## Documentation

See `docs/` directory for detailed documentation.

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
  - POST /sbom/generate - Generate SBOM from results
  - GET /dashboard - Monitoring dashboard
  - GET /health - Health check

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
