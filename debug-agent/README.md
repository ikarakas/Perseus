# Telemetry Agent for SBOM Collection

This agent runs on remote machines to collect OS-level BOM data and send it to the SBOM telemetry server.

## Features

- Automatic OS BOM collection (kernel, packages, libraries)
- Push-based architecture (agent initiates connection)
- Heartbeat mechanism for monitoring
- Automatic reconnection on network failures
- Configurable collection intervals

## Installation

1. Copy the telemetry-agent directory to the target machine
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.yaml` to configure:

- **Server connection**: Host and port of the telemetry server
- **Collection settings**: How often to collect BOM data
- **Agent settings**: Agent ID and heartbeat interval

## Running the Agent

```bash
# Run with default config
python agent.py

# Run with custom config
python agent.py -c /path/to/config.yaml

# Run with debug logging
python agent.py --log-level DEBUG
```

## Systemd Service (Linux)

Create `/etc/systemd/system/sbom-telemetry-agent.service`:

```ini
[Unit]
Description=SBOM Telemetry Agent
After=network.target

[Service]
Type=simple
User=sbom
WorkingDirectory=/opt/sbom-telemetry-agent
ExecStart=/usr/bin/python3 /opt/sbom-telemetry-agent/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable sbom-telemetry-agent
sudo systemctl start sbom-telemetry-agent
```

## Security

- Use TLS for encrypted communication (configure in `config.yaml`)
- Agent authentication via tokens or certificates
- Run with minimal privileges

## Monitoring

Check agent logs:
```bash
tail -f telemetry-agent.log
```

View agent status via the SBOM API:
```bash
curl http://sbom-server:8000/telemetry/agents/{agent-id}
```