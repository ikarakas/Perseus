#!/bin/bash
# Test script for telemetry system

echo "=== SBOM Telemetry System Test ==="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# 1. Start the telemetry server
echo "1. Starting telemetry server..."
cd src/telemetry
python run_server.py -c ../../telemetry-server-config.yaml &
SERVER_PID=$!
sleep 3
check_status "Server started (PID: $SERVER_PID)"

# 2. Test server is listening
echo "2. Testing server connection..."
nc -zv localhost 9876
check_status "Server is listening on port 9876"

# 3. Test API endpoints
echo "3. Testing API endpoints..."
curl -s http://localhost:8000/telemetry/status | jq .
check_status "Telemetry API is accessible"

# 4. Show how to deploy agent
echo -e "\n${GREEN}=== Agent Deployment Instructions ===${NC}"
echo "To deploy the agent to your Ubuntu VM:"
echo ""
echo "1. Package the agent:"
echo "   tar -czf telemetry-agent.tar.gz telemetry-agent/"
echo ""
echo "2. Copy to VM:"
echo "   scp telemetry-agent.tar.gz user@vm-ip:/tmp/"
echo ""
echo "3. On the VM, extract and setup:"
echo "   ssh user@vm-ip"
echo "   cd /tmp"
echo "   tar -xzf telemetry-agent.tar.gz"
echo "   cd telemetry-agent"
echo "   sudo apt-get update"
echo "   sudo apt-get install -y python3-pip"
echo "   pip3 install -r requirements.txt"
echo ""
echo "4. Configure agent (edit config.yaml):"
echo "   nano config.yaml"
echo "   # Change server.host to your host machine's IP"
echo ""
echo "5. Run the agent:"
echo "   python3 agent.py"
echo ""
echo "6. Check agent status from host:"
echo "   curl http://localhost:8000/telemetry/agents"

# Cleanup
echo -e "\n${GREEN}Press Ctrl+C to stop the server${NC}"
wait $SERVER_PID