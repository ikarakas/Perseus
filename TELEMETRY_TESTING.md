# Testing Telemetry System with Ubuntu VM

## Quick Start

### 1. On Your Host Machine (Mac)

First, start the telemetry server and main API:

```bash
# Terminal 1: Start the main SBOM API
cd /Users/ikarakas/Development/Python/SBOM
python -m src.api.main

# Terminal 2: Start the telemetry server
cd /Users/ikarakas/Development/Python/SBOM
python src/telemetry/run_server.py
```

Find your host machine's IP address (that the VM can reach):
```bash
# On Mac
ifconfig | grep "inet " | grep -v 127.0.0.1
# Look for your network interface IP (e.g., 192.168.1.100)
```

### 2. Package the Agent

```bash
./package-agent.sh
```

This creates `telemetry-agent-deploy.tar.gz`.

### 3. Deploy to Ubuntu VM

```bash
# Copy package to VM
scp telemetry-agent-deploy.tar.gz ubuntu@<VM-IP>:/tmp/

# SSH into VM
ssh ubuntu@<VM-IP>

# Extract and setup
cd /tmp
tar -xzf telemetry-agent-deploy.tar.gz
cd telemetry-agent-package
./setup.sh
```

### 4. Configure Agent on VM

```bash
# Edit config to point to your host
nano config.yaml
# Change: host: YOUR_SERVER_IP_HERE
# To:     host: 192.168.1.100  (your host's IP)

# Activate virtual environment
source venv/bin/activate
```

### 5. Run the Agent

```bash
# Test run with debug logging
python agent.py --log-level DEBUG

# Or run normally
python agent.py
```

### 6. Monitor from Host

Check agent status:
```bash
# List all agents
curl http://localhost:8000/telemetry/agents | jq .

# Get specific agent info
curl http://localhost:8000/telemetry/agents/<AGENT-ID> | jq .

# Get latest BOM data
curl http://localhost:8000/telemetry/agents/<AGENT-ID>/bom/latest | jq .
```

## Troubleshooting

### Connection Issues

1. **Check firewall on host**:
   ```bash
   # Mac: Allow incoming connections on port 9876
   sudo pfctl -d  # Temporarily disable firewall for testing
   ```

2. **Test connectivity from VM**:
   ```bash
   # On VM
   nc -zv <HOST-IP> 9876
   curl http://<HOST-IP>:8000/
   ```

3. **Check server logs**:
   ```bash
   # On host
   tail -f telemetry-server.log
   ```

### Agent Issues

1. **Check agent logs**:
   ```bash
   # On VM
   tail -f telemetry-agent.log
   ```

2. **Run agent in foreground with debug**:
   ```bash
   python agent.py --log-level DEBUG
   ```

3. **Test OS analyzer directly**:
   ```bash
   python -c "from collector import BOMCollector; import asyncio; c = BOMCollector(); print(asyncio.run(c.collect_bom()))"
   ```

## Running Agent as Service (Optional)

On the VM, create systemd service:

```bash
sudo nano /etc/systemd/system/sbom-agent.service
```

```ini
[Unit]
Description=SBOM Telemetry Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/tmp/telemetry-agent-package
Environment="PATH=/tmp/telemetry-agent-package/venv/bin"
ExecStart=/tmp/telemetry-agent-package/venv/bin/python /tmp/telemetry-agent-package/agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sbom-agent
sudo systemctl start sbom-agent
sudo systemctl status sbom-agent
```

## Expected Results

After successful setup, you should see:

1. Agent connects to server (check server logs)
2. Agent appears in API: `GET /telemetry/agents`
3. BOM data collected every hour (or per config)
4. Heartbeats every 60 seconds

## Security Notes

For production:
1. Use TLS encryption (configure in both server and agent configs)
2. Implement proper authentication
3. Use firewall rules instead of open ports
4. Run agent with minimal privileges