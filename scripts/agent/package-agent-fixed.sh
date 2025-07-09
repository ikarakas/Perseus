#!/bin/bash
# Package telemetry agent with all fixes

echo "Creating fixed telemetry agent package..."

# Clean up any previous attempts
rm -rf telemetry-agent-fixed
rm -f telemetry-agent-fixed.tar.gz

# Create directory structure
mkdir -p telemetry-agent-fixed/src/telemetry
mkdir -p telemetry-agent-fixed/src/analyzers
mkdir -p telemetry-agent-fixed/src/api

# Copy agent files
cp telemetry-agent/agent.py telemetry-agent-fixed/
cp telemetry-agent/transport.py telemetry-agent-fixed/
cp telemetry-agent/README.md telemetry-agent-fixed/
cp telemetry-agent/__init__.py telemetry-agent-fixed/

# Copy and fix collector.py
cp telemetry-agent/collector.py telemetry-agent-fixed/
sed -i.bak 's/from src.analyzers.analyzer import AnalysisResult/from src.api.models import AnalysisResult/' telemetry-agent-fixed/collector.py
rm telemetry-agent-fixed/collector.py.bak

# Copy config with correct host IP
cp telemetry-agent/config.yaml telemetry-agent-fixed/
sed -i.bak 's/host: localhost/host: 10.211.55.2/' telemetry-agent-fixed/config.yaml
rm telemetry-agent-fixed/config.yaml.bak

# Copy required modules from main project
cp src/telemetry/protocol.py telemetry-agent-fixed/src/telemetry/
cp src/analyzers/os_analyzer.py telemetry-agent-fixed/src/analyzers/
cp src/analyzers/base.py telemetry-agent-fixed/src/analyzers/
cp src/api/models.py telemetry-agent-fixed/src/api/

# Create minimal __init__.py files
echo '# Telemetry protocol module' > telemetry-agent-fixed/src/telemetry/__init__.py
echo '# Analyzers module' > telemetry-agent-fixed/src/analyzers/__init__.py
echo '# API models module' > telemetry-agent-fixed/src/api/__init__.py
echo '# Source module' > telemetry-agent-fixed/src/__init__.py

# Create complete requirements.txt
cat > telemetry-agent-fixed/requirements.txt << 'EOF'
pyyaml>=6.0
aiofiles>=23.0.0
pydantic>=2.0.0
EOF

# Create simple setup script
cat > telemetry-agent-fixed/setup.sh << 'EOF'
#!/bin/bash
# Setup script for telemetry agent

echo "Setting up SBOM telemetry agent..."

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
echo "The agent is configured to connect to: 10.211.55.2:9876"
EOF

chmod +x telemetry-agent-fixed/setup.sh

# Create run script for convenience
cat > telemetry-agent-fixed/run.sh << 'EOF'
#!/bin/bash
# Run the telemetry agent

source venv/bin/activate
python agent.py "$@"
EOF

chmod +x telemetry-agent-fixed/run.sh

# Create the tarball
tar -czf telemetry-agent-fixed.tar.gz telemetry-agent-fixed/

# Cleanup
rm -rf telemetry-agent-fixed/

echo "✓ Fixed package created: telemetry-agent-fixed.tar.gz"
echo ""
echo "This package includes:"
echo "  - All import fixes"
echo "  - Pre-configured host IP: 10.211.55.2"
echo "  - All required dependencies in requirements.txt"
echo "  - Setup and run scripts"
echo ""
echo "To deploy:"
echo "1. scp telemetry-agent-fixed.tar.gz parallels@vm-ip:/tmp/"
echo "2. ssh parallels@vm-ip"
echo "3. cd /tmp && tar -xzf telemetry-agent-fixed.tar.gz"
echo "4. cd telemetry-agent-fixed && ./setup.sh"
echo "5. ./run.sh"