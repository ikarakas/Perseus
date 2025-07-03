# SBOM Platform Architecture

**Powered by Syft v1.28.0 for Industry-Standard SBOM Generation**

## Overview

This platform provides a containerized Software Bill of Materials (SBOM) generation solution that leverages **Syft** as the core analysis engine. The platform supports multi-language source code and binary analysis with industry-standard SBOM format output.

## Architecture

### Core Components

1. **Orchestrator Container**
   - FastAPI-based REST API
   - Syft integration for analysis
   - SBOM generation engine
   - Web dashboard and CLI interface

2. **Syft Analysis Engine**
   - Industry-standard dependency detection
   - 50+ package manager support
   - Binary and source code analysis
   - PURL generation and metadata extraction

3. **Storage Layer**
   - Analysis result storage
   - SBOM artifact management
   - Metrics and audit logs

### Technology Stack

- **Container Platform**: Docker with Alpine Linux
- **API Framework**: FastAPI with Pydantic models
- **Analysis Engine**: Syft v1.28.0
- **SBOM Formats**: SPDX 2.3, CycloneDX 1.5, SWID
- **Languages**: Python 3.11
- **Monitoring**: psutil-based metrics

## Supported Ecosystems

### Languages and Package Managers
- **Java**: Maven, Gradle, JAR archives
- **C/C++**: Conan, vcpkg, CMake
- **Python**: pip, Poetry, Pipenv, conda
- **Node.js**: npm, Yarn, pnpm
- **Go**: Go modules, dep
- **Rust**: Cargo
- **And 40+ more ecosystems**

### Binary Analysis
- Container images (Docker, OCI)
- Java archives (JAR, WAR, EAR)
- System packages (deb, rpm, apk)
- Native executables

## Key Features

### Enhanced Analysis
- **Deep dependency scanning** with Syft's proven algorithms
- **License detection** from package metadata
- **Vulnerability surface mapping** for security analysis
- **Transitive dependency resolution**

### SBOM Generation
- **Industry-standard formats** (SPDX 2.3, CycloneDX 1.5)
- **Package URLs (PURLs)** for precise identification
- **Rich metadata** including source locations and versions
- **Multi-project aggregation** support

### User Interfaces
- **REST API** for programmatic access
- **Web Dashboard** with interactive forms
- **CLI Helper Script** for command-line workflows
- **Auto-path resolution** for any file location

## Security Features

- Input validation and sanitization
- Rate limiting and request monitoring
- Container security scanning
- Audit logging for compliance

## Performance Characteristics

- **Analysis Speed**: 5-30 seconds for typical projects
- **Scalability**: Horizontal scaling ready
- **Memory Usage**: Optimized for large codebases
- **Accuracy**: Industry-leading detection rates

## Deployment

### Requirements
- Docker and Docker Compose
- 2GB RAM minimum
- 1GB disk space for containers

### Quick Start
```bash
# Start the platform
docker-compose -f docker-compose-simple.yml up -d

# Analyze a project
./sbom-cli.sh analyze-source /path/to/project java

# Generate SBOM
./sbom-cli.sh generate-sbom "analysis-id" spdx
```

## API Endpoints

- `POST /analyze/source` - Source code analysis
- `POST /analyze/binary` - Binary file analysis
- `GET /analyze/{id}/status` - Analysis status
- `GET /analyze/{id}/results` - Analysis results
- `POST /sbom/generate` - SBOM generation
- `GET /sbom/{id}` - SBOM download
- `GET /dashboard` - Web interface
- `GET /health` - Platform health

## Integration

The platform is designed for integration with:
- **CI/CD pipelines** for automated SBOM generation
- **Security scanning tools** for vulnerability assessment
- **Compliance systems** for regulatory requirements
- **Container registries** for supply chain security

## Migration from Legacy

This platform evolved from custom analyzers to Syft-based analysis:

| Aspect | Legacy | Current (Syft) |
|--------|--------|----------------|
| **Analysis** | Custom regex parsing | Industry-standard Syft engine |
| **Languages** | Java, C++ | 50+ ecosystems |
| **Accuracy** | Basic | Enterprise-grade |
| **Maintenance** | Custom code | Community-driven |
| **Standards** | Basic PURL | Full specification compliance |

---

**Built with ❤️ using Syft and FastAPI**