#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Package telemetry agent for Docker deployment

echo "Creating Docker-ready telemetry agent package..."

# Clean up any previous attempts
rm -rf telemetry-agent-docker
rm -f telemetry-agent-docker.tar.gz

# Create directory structure
mkdir -p telemetry-agent-docker/src/telemetry
mkdir -p telemetry-agent-docker/src/analyzers
mkdir -p telemetry-agent-docker/src/api

# Copy agent files
cp telemetry-agent/agent.py telemetry-agent-docker/
cp telemetry-agent/transport.py telemetry-agent-docker/
cp telemetry-agent/README.md telemetry-agent-docker/
cp telemetry-agent/__init__.py telemetry-agent-docker/

# Copy and fix collector.py
cp telemetry-agent/collector.py telemetry-agent-docker/
sed -i.bak 's/from src.analyzers.analyzer import AnalysisResult/from src.api.models import AnalysisResult/' telemetry-agent-docker/collector.py
rm telemetry-agent-docker/collector.py.bak

# Create Docker-specific config
cat > telemetry-agent-docker/config.yaml << 'EOF'
# Telemetry Agent Configuration for Docker

# Server connection settings
server:
  # Use your Docker host IP - find with: docker network inspect bridge
  # For Mac/Windows Docker Desktop, use host.docker.internal
  # For Linux, use your actual IP address
  host: host.docker.internal  # Change this to your Docker host IP
  port: 9876

# Agent settings
agent:
  # Unique agent ID (leave empty to auto-generate)
  # id: "my-server-01"
  
  # Heartbeat interval in seconds
  heartbeat_interval: 60

# Collection settings
collection:
  # How often to collect BOM data (in seconds)
  interval: 3600  # 1 hour
  
  # Whether to perform deep scan (all packages)
  deep_scan: false
  
  # Collection timeout (in seconds)
  timeout: 300

# Logging settings
logging:
  level: INFO
  file: telemetry-agent.log
EOF

# Copy required modules from main project
cp src/telemetry/protocol.py telemetry-agent-docker/src/telemetry/
cp src/analyzers/os_analyzer.py telemetry-agent-docker/src/analyzers/
cp src/analyzers/base.py telemetry-agent-docker/src/analyzers/
cp src/api/models.py telemetry-agent-docker/src/api/

# Create minimal __init__.py files
echo '# Telemetry protocol module' > telemetry-agent-docker/src/telemetry/__init__.py
echo '# Analyzers module' > telemetry-agent-docker/src/analyzers/__init__.py
echo '# API models module' > telemetry-agent-docker/src/api/__init__.py
echo '# Source module' > telemetry-agent-docker/src/__init__.py

# Create complete requirements.txt
cat > telemetry-agent-docker/requirements.txt << 'EOF'
pyyaml>=6.0
aiofiles>=23.0.0
pydantic>=2.0.0
EOF

# Create Docker-specific setup script
cat > telemetry-agent-docker/setup-docker.sh << 'EOF'
#!/bin/bash
# Setup script for telemetry agent on Docker host

echo "Setting up SBOM telemetry agent for Docker environment..."

# Find Docker host IP
echo "Detecting Docker host IP..."
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "msys" ]]; then
    echo "Detected Mac/Windows - using host.docker.internal"
    DOCKER_HOST_IP="host.docker.internal"
elif command -v docker &> /dev/null; then
    DOCKER_HOST_IP=$(docker network inspect bridge | grep "Gateway" | awk '{print $2}' | tr -d '",' | head -1)
    if [ -z "$DOCKER_HOST_IP" ]; then
        echo "Could not detect Docker host IP automatically."
        echo "Please find your Docker host IP and update config.yaml manually."
        echo "Common methods:"
        echo "  - Linux: ip route | grep docker0 | awk '{print \$9}'"
        echo "  - Check: docker network inspect bridge"
        exit 1
    fi
    echo "Detected Docker host IP: $DOCKER_HOST_IP"
else
    echo "Docker not found. Please install Docker first."
    exit 1
fi

# Update config with detected IP
sed -i.bak "s/host: host.docker.internal/host: $DOCKER_HOST_IP/" config.yaml
rm config.yaml.bak

echo "✓ Config updated with Docker host IP: $DOCKER_HOST_IP"

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the agent:"
echo "1. source venv/bin/activate"
echo "2. python agent.py"
echo ""
echo "The agent is configured to connect to: $DOCKER_HOST_IP:9876"
EOF

chmod +x telemetry-agent-docker/setup-docker.sh

# Create run script for convenience
cat > telemetry-agent-docker/run.sh << 'EOF'
#!/bin/bash
# Run the telemetry agent

source venv/bin/activate
python agent.py "$@"
EOF

chmod +x telemetry-agent-docker/run.sh

# Create the tarball
tar -czf telemetry-agent-docker.tar.gz telemetry-agent-docker/

# Cleanup
rm -rf telemetry-agent-docker/

echo "✓ Docker-ready package created: telemetry-agent-docker.tar.gz"
echo ""
echo "This package includes:"
echo "  - Docker host networking configuration"
echo "  - Automatic Docker host IP detection"
echo "  - All required dependencies and fixes"
echo ""
echo "To deploy to VM when Docker is running:"
echo "1. Start Docker: docker-compose up -d"
echo "2. scp telemetry-agent-docker.tar.gz parallels@vm-ip:~/Downloads/"
echo "3. ssh parallels@vm-ip"
echo "4. cd ~/Downloads && tar -xzf telemetry-agent-docker.tar.gz"
echo "5. cd telemetry-agent-docker && ./setup-docker.sh"
echo "6. ./run.sh"
