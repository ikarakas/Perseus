# SBOM Project Structure

## Directory Layout

```
SBOM/
├── src/                    # Main application source code
│   ├── analyzers/         # Component analyzers (C++, Java, OS, Docker)
│   ├── api/              # REST API endpoints
│   ├── common/           # Shared utilities and storage
│   ├── monitoring/       # Dashboard and metrics
│   ├── orchestrator/     # Workflow engine
│   ├── sbom/            # SBOM generation (SPDX, CycloneDX, SWID)
│   ├── security/        # Security middleware and validation
│   ├── telemetry/       # Telemetry server and protocol
│   └── vulnerability/   # Vulnerability scanning (Grype, OSV)
│
├── examples/             # Example code and test applications
│   ├── docker-go-app/   # Sample Go application for Docker SBOM testing
│   └── java-nato-library/ # Sample Java library for source analysis
│
├── scripts/              # All scripts organized by purpose
│   ├── agent/           # Agent packaging scripts
│   ├── dev/             # Development tools
│   ├── docker/          # Docker-related scripts
│   └── utility/         # Utility scripts
│
├── tests/                # All test files
│   ├── integration/     # Integration tests
│   ├── performance/     # Performance tests
│   └── unit/           # Unit tests
│
├── tools/               # Standalone tools
│   ├── sbom-cli.sh     # Main CLI interface
│   ├── sbom_formatter.py
│   ├── sbom_html_generator.py
│   └── update-vuln-db.sh
│
├── telemetry-agent/     # Remote agent source code
├── debug-agent/         # Debug agent for troubleshooting
│
├── data/                # File upload directory (gitignored)
├── logs/                # Application logs (gitignored)
├── telemetry_data/      # Telemetry storage (gitignored)
│
├── docker-compose.yml   # Full Docker orchestration
├── docker-compose-simple.yml # Simplified Docker setup
├── Dockerfile          # Container definition
├── Makefile            # Build and deployment commands
├── requirements.txt    # Python dependencies
├── pytest.ini          # Test configuration
└── README.md          # Project documentation
```

## Quick Commands

- **Start Platform (Simple)**: `docker-compose -f docker-compose-simple.yml up -d`
- **Start Platform (Full)**: `docker-compose up -d`
- **Use Makefile**: `make start`, `make test`, `make clean`
- **CLI Tool**: `./sbom-cli.sh [command]`
- **Run Tests**: `python -m pytest tests/`
- **Access Dashboard**: http://localhost:8080/dashboard

## Key Locations

- **Main API**: `src/api/main.py`
- **CLI Tool**: `tools/sbom-cli.sh` (symlinked to root)
- **Dashboard**: `src/monitoring/dashboard.py`
- **Docker Configs**: `docker-compose-simple.yml` (recommended)
- **Test Suite**: `tests/` directory
