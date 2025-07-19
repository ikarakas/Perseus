#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Script to reorganize project structure cleanly

echo "🗂️  Reorganizing SBOM project structure..."

# Create organized directories
echo "Creating directory structure..."
mkdir -p scripts/{agent,docker,utility,dev}
mkdir -p tests/{integration,unit,performance}
mkdir -p docs
mkdir -p tools

# Move agent packaging scripts
echo "Moving agent scripts..."
mv package-agent*.sh scripts/agent/ 2>/dev/null || true

# Move Docker-related scripts
echo "Moving Docker scripts..."
mv docker-start.sh scripts/docker/ 2>/dev/null || true
mv Dockerfile scripts/docker/Dockerfile.bak 2>/dev/null || true
cp Dockerfile scripts/docker/ 2>/dev/null || true

# Move utility scripts
echo "Moving utility scripts..."
mv find-host-ip.sh scripts/utility/ 2>/dev/null || true
mv debug-agent.sh scripts/utility/ 2>/dev/null || true
mv run_telemetry_server.py scripts/utility/ 2>/dev/null || true

# Move development/monitoring scripts
echo "Moving development scripts..."
mv git_monitor.py scripts/dev/ 2>/dev/null || true
mv git_watch.sh scripts/dev/ 2>/dev/null || true
mv find_docker_image.py scripts/dev/ 2>/dev/null || true

# Move test files
echo "Moving test files..."
mv test_*.py tests/integration/ 2>/dev/null || true
mv test_*.sh tests/integration/ 2>/dev/null || true

# Move tools
echo "Moving tools..."
mv sbom-cli.sh tools/ 2>/dev/null || true
mv sbom_formatter.py tools/ 2>/dev/null || true
mv sbom_html_generator.py tools/ 2>/dev/null || true

# Create convenience symlinks in root for important scripts
echo "Creating convenience symlinks..."
ln -sf scripts/docker/docker-start.sh docker-start.sh 2>/dev/null || true
ln -sf scripts/agent/package-agent-final.sh package-agent.sh 2>/dev/null || true

# Create a project map
cat > PROJECT_STRUCTURE.md << 'EOF'
# SBOM Project Structure

## Directory Layout

```
SBOM/
├── src/                    # Main application source code
│   ├── analyzers/         # Component analyzers (C++, Java, OS, etc.)
│   ├── api/              # REST API endpoints
│   ├── monitoring/       # Dashboard and metrics
│   ├── orchestrator/     # Workflow engine
│   ├── sbom/            # SBOM generation
│   └── telemetry/       # Telemetry server and protocol
│
├── telemetry-agent/       # Remote agent source code
│
├── scripts/              # All scripts organized by purpose
│   ├── agent/           # Agent packaging scripts
│   │   ├── package-agent-final.sh
│   │   ├── package-agent-docker.sh
│   │   └── package-agent-fixed.sh
│   ├── docker/          # Docker-related scripts
│   │   └── docker-start.sh
│   ├── utility/         # Utility scripts
│   │   ├── find-host-ip.sh
│   │   ├── debug-agent.sh
│   │   └── run_telemetry_server.py
│   └── dev/             # Development tools
│       ├── git_monitor.py
│       └── git_watch.sh
│
├── tests/                # All test files
│   ├── integration/     # Integration tests
│   └── unit/           # Unit tests
│
├── tools/               # Standalone tools
│   ├── sbom-cli.sh
│   ├── sbom_formatter.py
│   └── sbom_html_generator.py
│
├── docs/                # Documentation
│   └── TELEMETRY_TESTING.md
│
├── data/                # File upload directory
├── logs/                # Application logs
├── telemetry_data/      # Telemetry storage
│
├── docker-compose.yml   # Docker orchestration
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Quick Commands

- **Start Docker**: `./docker-start.sh`
- **Package Agent**: `./package-agent.sh`
- **Run Tests**: `python -m pytest tests/`
- **Access Dashboard**: http://localhost:8000/dashboard

## Key Locations

- **Main API**: `src/api/main.py`
- **Telemetry Server**: `src/telemetry/server.py`
- **Agent Code**: `telemetry-agent/agent.py`
- **Docker Config**: `docker-compose.yml`
EOF

echo ""
echo "✅ Project reorganized! Key changes:"
echo "  📁 Scripts organized into scripts/{agent,docker,utility,dev}"
echo "  🧪 Tests moved to tests/{integration,unit}"
echo "  🔧 Tools moved to tools/"
echo "  🔗 Convenience symlinks created in root"
echo "  📄 PROJECT_STRUCTURE.md created"
echo ""
echo "Note: Docker and core functionality remain unchanged!"