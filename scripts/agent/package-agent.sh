#!/bin/bash
# Package telemetry agent for deployment

echo "Packaging telemetry agent..."

# Create a standalone package with minimal dependencies
mkdir -p telemetry-agent-package/src/telemetry
mkdir -p telemetry-agent-package/src/analyzers
mkdir -p telemetry-agent-package/src/api

# Copy agent files
cp -r telemetry-agent/* telemetry-agent-package/

# Copy required modules from main project
cp src/telemetry/protocol.py telemetry-agent-package/src/telemetry/
# Create minimal __init__.py for telemetry module
echo '# Telemetry protocol module' > telemetry-agent-package/src/telemetry/__init__.py
cp src/analyzers/os_analyzer.py telemetry-agent-package/src/analyzers/
cp src/analyzers/base.py telemetry-agent-package/src/analyzers/
cp src/analyzers/__init__.py telemetry-agent-package/src/analyzers/
cp src/api/models.py telemetry-agent-package/src/api/
cp src/api/__init__.py telemetry-agent-package/src/api/
touch telemetry-agent-package/src/__init__.py

# Create setup script for the VM
cat > telemetry-agent-package/setup.sh << 'EOF'
#!/bin/bash
# Setup script for telemetry agent

echo "Setting up SBOM telemetry agent..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To configure the agent:"
echo "1. Edit config.yaml and set server.host to your SBOM server IP"
echo "2. Run: source venv/bin/activate && python agent.py"
EOF

chmod +x telemetry-agent-package/setup.sh

# Update config to have placeholder for server host
sed -i.bak 's/host: localhost/host: YOUR_SERVER_IP_HERE/' telemetry-agent-package/config.yaml

# Create tarball
tar -czf telemetry-agent-deploy.tar.gz telemetry-agent-package/

# Cleanup
rm -rf telemetry-agent-package/

echo "Package created: telemetry-agent-deploy.tar.gz"
echo ""
echo "To deploy:"
echo "1. scp telemetry-agent-deploy.tar.gz user@vm-ip:/tmp/"
echo "2. ssh user@vm-ip"
echo "3. cd /tmp && tar -xzf telemetry-agent-deploy.tar.gz"
echo "4. cd telemetry-agent-package && ./setup.sh"