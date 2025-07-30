# Perseus: Enterprise SBOM & Vulnerability Management Platform
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0

<div align="center">

![Perseus Platform](https://img.shields.io/badge/Perseus-v1.6.0-blue?style=for-the-badge&logo=shield)
![License](https://img.shields.io/badge/License-NFCL%20v1.0-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

**Comprehensive Software Bill of Materials (SBOM) generation and vulnerability management platform for enterprise environments**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [API Reference](#api-reference) • [Deployment](#deployment) • [Kubernetes](#️-kubernetes-deployment)

</div>

---

## 🎯 Overview

**Perseus** is an enterprise-grade platform that combines advanced SBOM generation with comprehensive vulnerability management. Built for security-conscious organizations, it provides deep visibility into software dependencies, identifies security vulnerabilities, and enables proactive risk management across your entire software supply chain.

### Key Capabilities

- **🔍 Multi-Language Analysis**: C/C++, Java, Go, Python, and more
- **🐳 Docker Container Analysis**: Complete dependency mapping for containerized applications
- **🛡️ Vulnerability Scanning**: Integrated Grype and OSV scanning with offline capabilities
- **📊 Real-time Monitoring**: Live dashboard with metrics and alerting
- **🤖 Remote Agent Support**: Distributed analysis across multiple environments
- **🔐 Enterprise Security**: Input validation, rate limiting, and comprehensive audit logging
- **🔄 Workflow Orchestration**: Advanced task management and parallel processing
- **🧪 Debug Agent**: Dedicated debugging and analysis tools
- **✅ SBOM Validation**: Format compliance checking for generated SBOMs
- **🌐 WebSocket Communication**: Real-time telemetry data streaming

---

## 🏗️ Architecture

Perseus follows a microservices architecture designed for scalability and security:

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Tool]
        API[REST API]
        DASH[Dashboard]
    end
    
    subgraph "Orchestrator"
        ORCH[Workflow Engine]
        QUEUE[Task Queue]
        CACHE[Redis Cache]
    end
    
    subgraph "Analysis Layer"
        SYFT[Syft Analyzer]
        GRYPE[Grype Scanner]
        OSV[OSV Scanner]
        JAVA[Java Analyzer]
        CPP[C++ Analyzer]
        OS[OS Analyzer]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        S3[(S3 Storage)]
        FS[File System]
    end
    
    subgraph "Remote Agents"
        AGENT1[Agent 1]
        AGENT2[Agent 2]
        AGENT3[Agent N]
    end
    
    CLI --> API
    API --> ORCH
    ORCH --> QUEUE
    QUEUE --> SYFT
    QUEUE --> GRYPE
    QUEUE --> OSV
    SYFT --> DB
    GRYPE --> DB
    OSV --> DB
    ORCH --> AGENT1
    ORCH --> AGENT2
    ORCH --> AGENT3
    DASH --> API
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **API Gateway** | REST API and request routing | FastAPI |
| **Orchestrator** | Workflow management and task distribution | Custom Python |
| **Syft Analyzer** | SBOM generation from binaries and images | Syft |
| **Grype Scanner** | Vulnerability scanning (offline capable) | Grype |
| **OSV Scanner** | Online vulnerability database queries | OSV API |
| **Dashboard** | Real-time monitoring and metrics | Web UI |
| **Telemetry Agent** | Remote data collection | Python |
| **Workflow Engine** | Task orchestration and parallel processing | Python |
| **Debug Agent** | Advanced debugging and analysis | Python |

---

## 🚀 Quick Start

### Enhanced Makefile Commands

Perseus includes a comprehensive Makefile for easy management:

```bash
make help         # Show all available commands
make dev          # Start development environment
make k8s-deploy   # Deploy to Kubernetes
make status       # Check system status
make test         # Run verification tests
make help-dev     # Show development commands
make help-k8s     # Show Kubernetes commands
```

### Vulnerability Database Setup

**Important**: Update the vulnerability database before first use:

```bash
# Using the provided script (recommended)
./scripts/update_vuln_db.sh

# Or manually with Docker
docker-compose -f docker-compose.dev.yml exec sbom-platform grype db update

# Or if Grype is installed locally
grype db update
```

> **Note**: The vulnerability database (~500MB) is not included in the repository and must be downloaded separately. It contains the latest CVE data for accurate vulnerability detection.

### Using Docker (Recommended)

1. **Clone and start Perseus:**
   ```bash
   git clone https://github.com/ikarakas/Perseus.git
   cd Perseus
   make dev  # Starts development environment
   ```

2. **Access the dashboard:**
   ```bash
   open http://localhost:8000/dashboard
   ```

3. **Analyze your first project:**
   ```bash
   # Analyze a Java project
   ./sbom-cli.sh analyze-source /path/to/your/java-project java
   
   # Analyze a Docker image
   ./sbom-cli.sh analyze-docker nginx:latest
   
   # Scan for vulnerabilities
   ./sbom-cli.sh scan-vulnerabilities <analysis-id>
   ```

### Local Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Syft and Grype:**
   ```bash
   # Install Syft
   curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
   
   # Install Grype
   curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
   ```

3. **Start the platform:**
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

---

## 🔧 Features

### SBOM Generation

**Multi-Format Support:**
- **SPDX 2.3**: Industry-standard Software Package Data Exchange
- **CycloneDX 1.5**: OWASP standard for vulnerability reporting
- **SWID**: Software Identification tags

**Analysis Capabilities:**
- **Source Code**: C/C++, Java, Go, Python, Node.js with import analysis
- **Binary Analysis**: Executables, JAR files, shared libraries
- **Docker Images**: Complete container dependency mapping with registry authentication
- **OS Packages**: System-level package detection (APK, DEB, RPM)
- **SBOM Validation**: Format compliance checking (SPDX, CycloneDX)
- **Offline Analysis**: Air-gapped environment support

### Vulnerability Management

**Integrated Scanners:**
- **Grype**: Offline vulnerability scanning with local database
- **OSV**: Online vulnerability database with real-time updates
- **Offline Scanner**: Air-gapped environment vulnerability scanning
- **Custom Rules**: Configurable vulnerability detection rules
- **Component Scanner**: Individual component vulnerability checks via PURL

**Security Features:**
- **Severity Classification**: Critical, High, Medium, Low
- **CVE Tracking**: Complete Common Vulnerabilities and Exposures support
- **Remediation Guidance**: Suggested fixes and workarounds
- **Risk Scoring**: CVSS-based vulnerability prioritization

### Remote Agent Architecture

**Distributed Analysis:**
- **Push-based Agents**: Remote machines initiate connections
- **Secure Communication**: TLS encryption and authentication
- **Auto-discovery**: Automatic agent registration and health monitoring
- **Load Balancing**: Intelligent task distribution across agents

**Agent Capabilities:**
- **OS-level Analysis**: Kernel, packages, and system libraries
- **Heartbeat Monitoring**: Real-time agent health tracking
- **Configurable Collection**: Customizable data collection intervals
- **Offline Operation**: Local analysis with periodic sync
- **WebSocket Communication**: Real-time bidirectional data streaming
- **Command Queue**: Remote command execution capability

### Real-time Monitoring

**Dashboard Features:**
- **System Metrics**: CPU, memory, disk usage monitoring
- **Analysis Performance**: Success rates, processing times
- **Vulnerability Trends**: Security posture over time
- **Alert Management**: Configurable thresholds and notifications

**API Monitoring:**
- **Request Tracking**: Response times and error rates
- **Usage Analytics**: API endpoint utilization
- **Performance Metrics**: Throughput and latency monitoring

---

## 📁 Project Structure

```
Perseus/
├── src/                          # Core application
│   ├── analyzers/               # Language-specific analyzers
│   │   ├── syft_analyzer.py    # Syft integration
│   │   ├── java_analyzer.py    # Java source analysis
│   │   ├── cpp_analyzer.py     # C++ source analysis
│   │   └── os_analyzer.py      # OS package detection
│   ├── vulnerability/           # Vulnerability scanning
│   │   ├── grype_scanner.py    # Grype integration
│   │   ├── osv_scanner.py      # OSV API integration
│   │   ├── offline_scanner.py  # Air-gapped scanning
│   │   └── scanner.py          # Main scanner orchestrator
│   ├── api/                    # REST API endpoints
│   │   └── cicd.py            # CI/CD integration endpoints
│   ├── orchestrator/           # Workflow engine
│   ├── monitoring/             # Dashboard and metrics
│   ├── telemetry/              # Remote agent protocol
│   └── security/               # Authentication & middleware
│
├── telemetry-agent/            # Remote agent implementation
├── debug-agent/                # Debug and analysis tools
├── tools/                      # Command-line tools
│   ├── sbom-cli.sh            # Main CLI interface
│   └── perseus-ci/            # Standalone CI/CD integration
├── scripts/                    # Deployment and utility scripts
├── tests/                      # Comprehensive test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── performance/           # Performance tests
├── containers/                 # Container orchestration
├── data/                       # Analysis results (gitignored)
├── logs/                       # Application logs (gitignored)
├── Dockerfile                  # Standard container image
├── Dockerfile.minimal          # Lightweight container image
└── docker-compose-simple.yml   # Production-ready setup
```

---

## 🛠️ CLI Usage

Perseus provides a powerful command-line interface for all operations:

### Basic Analysis

```bash
# Analyze source code
./sbom-cli.sh analyze-source /path/to/project java
./sbom-cli.sh analyze-source ~/my-cpp-project c++

# Analyze Docker images
./sbom-cli.sh analyze-docker nginx:latest
./sbom-cli.sh analyze-docker registry.example.com/myapp:v1.0

# Analyze OS packages
./sbom-cli.sh analyze-os
```

### Vulnerability Scanning

Perseus provides multiple methods for vulnerability scanning and SBOM-based security analysis:

#### Method 1: Integrated Analysis (Recommended)
```bash
# Source code analysis with automatic vulnerability scanning
./sbom-cli.sh analyze-source /path/to/project java --include-vulnerabilities

# Docker image analysis with vulnerability scanning
./sbom-cli.sh analyze-docker nginx:latest --include-vulnerabilities

# Check vulnerability summary
curl http://localhost:8000/vulnerabilities/scan/<analysis-id>
```

#### Method 2: Perseus CI/CD Tool (CI/CD Integration)
```bash
# Navigate to your project directory
cd /path/to/your/project

# Run complete vulnerability scan
python3 tools/perseus-ci/perseus-ci.py scan --output vulnerabilities.json

# Scan with failure thresholds for CI/CD pipelines
python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical,high --output report.json

# Check specific project path
python3 tools/perseus-ci/perseus-ci.py scan --project-path ./my-app --output results.json
```

#### Method 3: API-Based Scanning
```bash
# Register CI/CD build for scanning
curl -X POST http://localhost:8000/api/v1/cicd/builds \
  -H "Content-Type: application/json" \
  -d '{
    "build_id": "build-123",
    "project": {
      "name": "my-app",
      "path": "/app/data/my-project",
      "type": "java"
    },
    "ci_context": {
      "platform": "jenkins",
      "build_id": "build-123"
    }
  }'

# Start vulnerability scan
curl -X POST http://localhost:8000/api/v1/cicd/builds/build-123/scan \
  -H "Content-Type: application/json" \
  -d '{"scan_type": "full", "wait": true}'

# Get vulnerability results
curl http://localhost:8000/api/v1/cicd/builds/build-123/results
```

#### Method 4: Direct SBOM Vulnerability Scanning
```bash
# Generate SBOM first
./sbom-cli.sh generate-sbom <analysis-id> cyclonedx

# Scan existing SBOM file with Grype
grype /path/to/your/sbom.json -o table

# Scan SBOM with detailed JSON output
grype /path/to/your/sbom.json -o json > vulnerabilities.json

# Scan SBOM with SARIF output for CI/CD
grype /path/to/your/sbom.json -o sarif > vulnerabilities.sarif
```

#### Method 5: Component-Level Scanning
```bash
# Scan individual components
curl -X POST http://localhost:8000/vulnerabilities/scan/component \
  -H "Content-Type: application/json" \
  -d '{
    "name": "log4j-core",
    "version": "2.14.0",
    "type": "java"
  }'

# Scan using Package URL (PURL)
curl -X POST http://localhost:8000/vulnerabilities/scan/component \
  -H "Content-Type: application/json" \
  -d '{
    "purl": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.0"
  }'
```

#### Vulnerability Database Management
```bash
# Check vulnerability database status
curl http://localhost:8000/vulnerabilities/database/status

# Update vulnerability database
curl -X POST http://localhost:8000/vulnerabilities/database/update

# Get vulnerability summary for analysis
curl http://localhost:8000/vulnerabilities/summary
```

### SBOM Generation

```bash
# Generate SBOM in multiple formats
./sbom-cli.sh generate-sbom <analysis-id> spdx
./sbom-cli.sh generate-sbom <analysis-id> cyclonedx
./sbom-cli.sh generate-sbom <analysis-id> swid

# Download generated SBOM
./sbom-cli.sh get-sbom <sbom-id>
```

### Remote Agent Management

```bash
# Deploy agent to remote system
./scripts/agent/package-agent-final.sh

# Check agent status
./sbom-cli.sh agent-status <agent-id>

# View telemetry data
./sbom-cli.sh telemetry-data <agent-id>
```

### CI/CD Integration

Perseus provides comprehensive CI/CD platform integration with automatic platform detection and configurable security policies:

#### Supported Platforms
- **Jenkins**: Automatic job and build ID detection
- **GitLab CI**: Pipeline and job integration
- **GitHub Actions**: Workflow and run ID support
- **Generic CI/CD**: Environment variable-based detection

#### Perseus CI Tool
The standalone `perseus-ci` tool provides zero-dependency CI/CD integration:

```bash
# Basic vulnerability scan
python3 tools/perseus-ci/perseus-ci.py scan

# Scan with failure thresholds
python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical,high

# Generate HTML report
python3 tools/perseus-ci/perseus-ci.py scan --output report.html --format html

# Multiple output formats
python3 tools/perseus-ci/perseus-ci.py scan --format json,csv,html
```

#### CI/CD API Integration
```bash
# Register build
curl -X POST http://localhost:8000/api/v1/cicd/builds \
  -H "Content-Type: application/json" \
  -d '{"build_id": "build-123", "project": {"name": "my-app", "type": "java"}}'

# Run synchronous scan (waits for completion)
curl -X POST http://localhost:8000/api/v1/cicd/builds/build-123/scan?wait=true

# Download artifacts
curl http://localhost:8000/api/v1/cicd/builds/build-123/artifacts/sbom
curl http://localhost:8000/api/v1/cicd/builds/build-123/artifacts/vulnerabilities
```

#### Pipeline Integration Examples

**Jenkins Pipeline:**
```groovy
stage('Security Scan') {
    steps {
        sh 'python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical'
    }
}
```

**GitLab CI:**
```yaml
security-scan:
  script:
    - python3 tools/perseus-ci/perseus-ci.py scan --output report.json
  artifacts:
    reports:
      sast: report.json
```

**GitHub Actions:**
```yaml
- name: Perseus Security Scan
  run: |
    python3 tools/perseus-ci/perseus-ci.py scan --fail-on critical,high
    
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: security-report
    path: vulnerabilities.json
```

---

## 🔌 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze/source` | POST | Analyze source code |
| `/analyze/docker` | POST | Analyze Docker images |
| `/analyze/os` | POST | Analyze OS packages |
| `/vulnerabilities/scan` | POST | Scan for vulnerabilities |
| `/vulnerabilities/scan/component` | POST | Scan individual component |
| `/vulnerabilities/database/status` | GET | Check vulnerability DB status |
| `/vulnerabilities/database/update` | POST | Update vulnerability DB |
| `/sbom/generate` | POST | Generate SBOM |
| `/sbom/validate` | POST | Validate SBOM format |
| `/api/v1/cicd/builds` | POST | Register CI/CD build |
| `/api/v1/cicd/builds/{id}/scan` | POST | Start CI/CD scan |
| `/api/v1/cicd/builds/{id}/results` | GET | Get CI/CD results |
| `/telemetry/agents` | GET | List remote agents |
| `/dashboard` | GET | Web dashboard |

### Example API Usage

```bash
# Analyze Java project
curl -X POST http://localhost:8080/analyze/source \
  -H "Content-Type: application/json" \
  -d '{
    "type": "source",
    "language": "java",
    "location": "/app/data/my-project"
  }'

# Scan for vulnerabilities
curl -X POST http://localhost:8080/vulnerabilities/scan \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "abc123",
    "scanner": "grype"
  }'

# Generate SPDX SBOM
curl -X POST http://localhost:8080/sbom/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_ids": ["abc123"],
    "format": "spdx"
  }'
```

---

## 🚀 Deployment

### Production Deployment

Perseus supports multiple deployment tiers:

#### 1. **Docker Compose (Development/Testing)**
   ```bash
   make dev         # Start development environment
   make dev-clean   # Stop and clean development environment
   ```

#### 2. **Kubernetes (Production)**
   ```bash
   make k8s-deploy  # Deploy to Kubernetes
   make k8s-status  # Check deployment status
   make k8s-clean   # Remove Kubernetes deployment
   ```

#### 3. **Quick Switching Between Environments**
   ```bash
   # Switch from Kubernetes to Docker
   make k8s-clean && make dev
   
   # Switch from Docker to Kubernetes
   make dev-clean && make k8s-deploy
   ```

2. **Optional: Advanced Configuration**
   
   For enterprise deployments, you can configure additional services:
   
   ```bash
   # Set optional environment variables for advanced features
   export PERSEUS_DB_URL="postgresql://user:pass@host:5432/perseus"  # For persistent storage
   export PERSEUS_REDIS_URL="redis://host:6379"                       # For caching
   export PERSEUS_SECRET_KEY="your-secret-key"                        # For JWT auth
   ```

3. **Verify Installation:**
   ```bash
   # Check if the platform is running
   curl http://localhost:8000/
   
   # Access the dashboard
   open http://localhost:8000/dashboard
   ```

### Remote Agent Deployment

1. **Package Agent:**
   ```bash
   ./scripts/agent/package-agent-final.sh
   ```

2. **Deploy to Target:**
   ```bash
   scp telemetry-agent.tar.gz user@target-host:/tmp/
   ssh user@target-host "cd /tmp && tar -xzf telemetry-agent.tar.gz"
   ```

3. **Configure and Start:**
   ```bash
   ssh user@target-host "cd telemetry-agent && python agent.py"
   ```

---

## ☸️ Kubernetes Deployment

Perseus includes production-ready Kubernetes manifests for high-availability deployments:

### Architecture
- **3 API replicas** - Load balanced, auto-healing
- **2 Background job processors** - Parallel task processing
- **PostgreSQL StatefulSet** - Persistent data storage
- **Automatic restarts** - Self-healing on failures

### Quick Commands
```bash
# Deploy to Kubernetes
make k8s-deploy

# Check status
make k8s-status

# View logs
make k8s-logs

# Scale deployments
make k8s-scale

# Access via port-forward
make k8s-port-forward  # Available at localhost:8001

# Database operations
make k8s-db-backup     # Backup database
make k8s-db-shell      # PostgreSQL shell
```

### Requirements
- Kubernetes cluster (Docker Desktop, Minikube, or cloud)
- kubectl configured
- 4GB RAM minimum

---

## 🔒 Security Features

### Input Validation & Sanitization
- **Path Traversal Protection**: Prevents `../` attacks and dangerous path patterns
- **Request Size Limits**: 100MB maximum request size
- **Input Sanitization**: Removes dangerous characters from component names and versions
- **URL Validation**: Validates and sanitizes file://, http://, https://, and git:// URLs

### Rate Limiting & Access Control
- **Rate Limiting**: 60 requests per minute per IP address
- **IP Blocking**: Manual IP blocking capability for security violations
- **Request Monitoring**: Tracks and logs all API requests

### Audit Logging
- **Security Violations**: Logs all security violations with client IP
- **Analysis Requests**: Tracks all analysis operations
- **File Access**: Monitors file access operations
- **SBOM Generation**: Logs SBOM generation activities

### Docker Security
- **Registry Authentication**: Supports Docker registry authentication for private images
- **Credential Management**: Secure handling of Docker credentials
- **Authentication Validation**: Validates Docker authentication before analysis

### Classification System
- **Security Classification**: Configurable security classification levels (UNCLASSIFIED, OFFICIAL, SECRET)
- **Classification Banner**: Visual classification display in dashboard
- **Version Control**: Version tracking with classification metadata
- **Export Controls**: Classification-aware data export restrictions

### Telemetry Security
- **WebSocket Security**: Secure WebSocket connections for real-time communication
- **TLS Support**: SSL/TLS encryption for agent communication (partially implemented)
- **Agent Authentication**: Basic authentication framework
- **Secure Communication**: Encrypted communication between agents and server
- **Command Authorization**: Secure remote command execution

---

## 📊 Monitoring & Metrics

### Dashboard Features
- **Real-time Metrics**: System performance monitoring
- **Analysis Statistics**: Success rates and processing times
- **Vulnerability Trends**: Security posture tracking
- **Agent Health**: Remote agent status monitoring

### Alert System
- **Performance Alerts**: CPU, memory, disk thresholds
- **Security Alerts**: Critical vulnerability notifications
- **Agent Alerts**: Offline agent detection
- **API Alerts**: Error rate and response time monitoring

---

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/performance/

# Run with coverage
python -m pytest --cov=src tests/
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning validation

---

## 🤝 Contributing

We welcome contributions to Perseus! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/ikarakas/Perseus.git
cd Perseus

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run performance tests
python -m pytest tests/performance/

# Start development server
make dev

# Or run directly
python -m uvicorn src.api.main:app --reload --port 8000

# Run debug agent
python debug-agent/debug_agent.py
```

---

## 📄 License

Perseus is licensed under the **NAEW&C Force License (NFCL) v1.0**. See [LICENSE](LICENSE.md) for details.

---

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ikarakas/Perseus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ikarakas/Perseus/discussions)

---

<div align="center">

**Perseus** - Enterprise SBOM & Vulnerability Management Platform

*Built with ❤️ for secure software supply chains*

</div>
