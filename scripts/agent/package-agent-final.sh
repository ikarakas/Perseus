#!/bin/bash
# Create the telemetry agent package

# Change to project root directory
cd "$(dirname "$0")/../.." || exit 1

echo "🔧 Creating telemetry agent package..."

# Clean up any previous attempts
rm -rf telemetry-agent-final
rm -f telemetry-agent-final.tar.gz

# Create directory structure
mkdir -p telemetry-agent-final/src/telemetry
mkdir -p telemetry-agent-final/src/analyzers
mkdir -p telemetry-agent-final/src/api

echo "✅ Copying and fixing agent files..."

# Copy agent files with fixes
cp telemetry-agent/agent.py telemetry-agent-final/
cp telemetry-agent/transport.py telemetry-agent-final/
cp telemetry-agent/README.md telemetry-agent-final/
cp telemetry-agent/__init__.py telemetry-agent-final/

# Copy and fix collector.py
cp telemetry-agent/collector.py telemetry-agent-final/
sed -i.bak 's/from src.analyzers.analyzer import AnalysisResult/from src.api.models import AnalysisResult, AnalysisOptions/' telemetry-agent-final/collector.py
rm telemetry-agent-final/collector.py.bak

# Copy required modules from main project (with fixes)
cp src/telemetry/protocol.py telemetry-agent-final/src/telemetry/
cp src/analyzers/os_analyzer.py telemetry-agent-final/src/analyzers/
cp src/analyzers/base.py telemetry-agent-final/src/analyzers/
cp src/api/models.py telemetry-agent-final/src/api/

echo "✅ Creating optimized configuration..."

# Create Docker-ready config
cat > telemetry-agent-final/config.yaml << 'EOF'
# Telemetry Agent Configuration (Final Fixed Version)

# Server connection settings
server:
  host: 10.211.55.2  # Your Docker host IP
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

# Create minimal __init__.py files
echo '# Telemetry protocol module' > telemetry-agent-final/src/telemetry/__init__.py
echo '# Analyzers module' > telemetry-agent-final/src/analyzers/__init__.py
echo '# API models module' > telemetry-agent-final/src/api/__init__.py
echo '# Source module' > telemetry-agent-final/src/__init__.py

# Create complete requirements.txt
cat > telemetry-agent-final/requirements.txt << 'EOF'
pyyaml>=6.0
aiofiles>=23.0.0
pydantic>=2.0.0
EOF

echo "✅ Creating setup scripts..."

# Create universal setup script
cat > telemetry-agent-final/setup.sh << 'EOF'
#!/bin/bash
# Universal setup script for telemetry agent

echo "🚀 Setting up SBOM telemetry agent..."

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
echo "✅ Setup complete!"
echo ""
echo "Configuration:"
echo "  - Server: 10.211.55.2:9876 (Docker host)"
echo "  - Collection interval: 1 hour"
echo "  - Deep scan: disabled (for performance)"
echo ""
echo "To run the agent:"
echo "  1. source venv/bin/activate"
echo "  2. python agent.py"
echo ""
echo "Or use the run script: ./run.sh"
echo ""
echo "To stop: Press Ctrl+C (now works properly!)"
EOF

chmod +x telemetry-agent-final/setup.sh

# Create run script
cat > telemetry-agent-final/run.sh << 'EOF'
#!/bin/bash
# Run the telemetry agent

echo "🤖 Starting SBOM telemetry agent..."

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate
python agent.py "$@"
EOF

chmod +x telemetry-agent-final/run.sh

# Create debug script
cat > telemetry-agent-final/debug.sh << 'EOF'
#!/bin/bash
# Run agent with debug logging

source venv/bin/activate
python agent.py --log-level DEBUG
EOF

chmod +x telemetry-agent-final/debug.sh

# Create the tarball
tar -czf telemetry-agent-final.tar.gz telemetry-agent-final/

# Cleanup
rm -rf telemetry-agent-final/

echo ""
echo "🎉 FINAL FIXED package created: telemetry-agent-final.tar.gz"
echo ""
echo "✅ ALL FIXES INCLUDED:"
echo "  🔧 Ctrl+C now works properly (force exit)"
echo "  🕐 No more datetime deprecation warnings"
echo "  🔒 Permission errors handled gracefully"
echo "  📦 AnalysisOptions import fixed"
echo "  🐳 Pre-configured for Docker (10.211.55.2)"
echo "  📝 Complete setup and run scripts"
echo ""
echo "🚀 Deploy to VM:"
echo "  1. scp telemetry-agent-final.tar.gz parallels@10.211.55.3:/tmp/"
echo "  2. ssh parallels@10.211.55.3"
echo "  3. cd /tmp && tar -xzf telemetry-agent-final.tar.gz"
echo "  4. cd telemetry-agent-final && ./setup.sh"
echo "  5. ./run.sh"
echo ""
echo "  ✋ Ctrl+C will now work to stop the agent!"
echo ""