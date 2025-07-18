# Perseus: Enterprise SBOM & Vulnerability Management Platform

<div align="center">

![Perseus Platform](https://img.shields.io/badge/Perseus-v1.3.0-blue?style=for-the-badge&logo=shield)
![License](https://img.shields.io/badge/License-NFCL%20v1.0-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

**Comprehensive Software Bill of Materials (SBOM) generation and vulnerability management platform for enterprise environments**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [API Reference](#api-reference) • [Deployment](#deployment)

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
- **🔐 Enterprise Security**: Sandboxed execution, authentication, and audit logging

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

---

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone and start Perseus:**
   ```bash
   git clone https://github.com/ikarakas/Perseus.git
   cd Perseus
   docker-compose -f docker-compose-simple.yml up -d
   ```

2. **Access the dashboard:**
   ```bash
   open http://localhost:8080/dashboard
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
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
   ```

---

## 🔧 Features

### SBOM Generation

**Multi-Format Support:**
- **SPDX 2.3**: Industry-standard Software Package Data Exchange
- **CycloneDX 1.5**: OWASP standard for vulnerability reporting
- **SWID**: Software Identification tags

**Analysis Capabilities:**
- **Source Code**: C/C++, Java, Go, Python, Node.js
- **Binary Analysis**: Executables, JAR files, shared libraries
- **Docker Images**: Complete container dependency mapping
- **OS Packages**: System-level package detection (APK, DEB, RPM)

### Vulnerability Management

**Integrated Scanners:**
- **Grype**: Offline vulnerability scanning with local database
- **OSV**: Online vulnerability database with real-time updates
- **Custom Rules**: Configurable vulnerability detection rules

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
│   │   └── scanner.py          # Main scanner orchestrator
│   ├── api/                    # REST API endpoints
│   ├── monitoring/             # Dashboard and metrics
│   ├── telemetry/              # Remote agent protocol
│   └── security/               # Authentication & middleware
│
├── telemetry-agent/            # Remote agent implementation
├── tools/                      # Command-line tools
│   └── sbom-cli.sh            # Main CLI interface
├── scripts/                    # Deployment and utility scripts
├── tests/                      # Comprehensive test suite
├── data/                       # Analysis results (gitignored)
├── logs/                       # Application logs (gitignored)
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

```bash
# Scan for vulnerabilities
./sbom-cli.sh scan-vulnerabilities <analysis-id>

# Get vulnerability report
./sbom-cli.sh get-vulnerabilities <scan-id>

# Generate security report
./sbom-cli.sh generate-security-report <analysis-id>
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

---

## 🔌 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze/source` | POST | Analyze source code |
| `/analyze/docker` | POST | Analyze Docker images |
| `/analyze/os` | POST | Analyze OS packages |
| `/vulnerabilities/scan` | POST | Scan for vulnerabilities |
| `/sbom/generate` | POST | Generate SBOM |
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

1. **Environment Setup:**
   ```bash
   # Set environment variables
   export PERSEUS_DB_URL="postgresql://user:pass@host:5432/perseus"
   export PERSEUS_REDIS_URL="redis://host:6379"
   export PERSEUS_SECRET_KEY="your-secret-key"
   ```

2. **Database Setup:**
   ```bash
   # Initialize database
   python -m src.common.storage init
   ```

3. **Start Services:**
   ```bash
   # Start with Docker Compose
   docker-compose up -d
   
   # Or start individual services
   docker-compose -f docker-compose-simple.yml up -d
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

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure API authentication
- **Role-based Access**: Granular permission control
- **API Rate Limiting**: Protection against abuse

### Data Protection
- **Encryption at Rest**: Sensitive data encryption
- **TLS Communication**: Encrypted agent communication
- **Audit Logging**: Complete operation tracking

### Sandboxed Execution
- **Container Isolation**: Secure analysis environments
- **Resource Limits**: CPU and memory constraints
- **Network Restrictions**: Controlled network access

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

# Start development server
python -m uvicorn src.api.main:app --reload
```

---

## 📄 License

Perseus is licensed under the **NAEW&C Force License (NFCL) v1.0**. See [LICENSE](LICENSE) for details.

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
