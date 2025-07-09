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
