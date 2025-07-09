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
