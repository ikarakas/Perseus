#!/bin/bash
# Deploy telemetry agent to multiple remote machines

echo "🚀 Multi-Agent Deployment Script"
echo "=================================="

# Configuration
SERVER_IP="YOUR_SERVER_IP"  # Replace with your server's IP
AGENT_PACKAGE="telemetry-agent-final.tar.gz"
REMOTE_USER="parallels"  # Or your remote user
REMOTE_PATH="/tmp"

# List of remote machines (customize these)
REMOTE_MACHINES=(
    "10.211.55.3"    # VM 1
    "10.211.55.4"    # VM 2 (add more as needed)
    # "192.168.1.100"  # Example additional machine
)

# Function to deploy to a single machine
deploy_to_machine() {
    local machine_ip=$1
    echo ""
    echo "🔧 Deploying to $machine_ip..."
    
    # Copy the agent package
    echo "  📦 Copying package..."
    scp $AGENT_PACKAGE $REMOTE_USER@$machine_ip:$REMOTE_PATH/
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Package copied successfully"
        
        # SSH and setup
        echo "  🛠️  Setting up agent..."
        ssh $REMOTE_USER@$machine_ip << EOF
cd $REMOTE_PATH
tar -xzf $AGENT_PACKAGE
cd telemetry-agent-final
./setup.sh
EOF
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Agent setup completed on $machine_ip"
            echo "  🤖 To start the agent, run: ssh $REMOTE_USER@$machine_ip 'cd $REMOTE_PATH/telemetry-agent-final && ./run.sh'"
        else
            echo "  ❌ Agent setup failed on $machine_ip"
        fi
    else
        echo "  ❌ Failed to copy package to $machine_ip"
    fi
}

# Main deployment logic
echo "Server IP: $SERVER_IP"
echo "Agent Package: $AGENT_PACKAGE"
echo "Remote User: $REMOTE_USER"
echo "Machines to deploy: ${REMOTE_MACHINES[@]}"
echo ""

# Check if package exists
if [ ! -f "$AGENT_PACKAGE" ]; then
    echo "❌ Agent package not found: $AGENT_PACKAGE"
    echo "Run: ./scripts/agent/package-agent-final.sh"
    exit 1
fi

# Update server IP in the package
echo "📝 Updating server IP configuration..."
mkdir -p temp_extract
cd temp_extract
tar -xzf ../$AGENT_PACKAGE
sed -i.bak "s/10.211.55.2/$SERVER_IP/g" telemetry-agent-final/config.yaml
rm telemetry-agent-final/config.yaml.bak
tar -czf ../$AGENT_PACKAGE telemetry-agent-final/
cd ..
rm -rf temp_extract

# Deploy to each machine
for machine in "${REMOTE_MACHINES[@]}"; do
    deploy_to_machine $machine
done

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Start agents on each machine:"
for machine in "${REMOTE_MACHINES[@]}"; do
    echo "   ssh $REMOTE_USER@$machine 'cd $REMOTE_PATH/telemetry-agent-final && ./run.sh &'"
done
echo ""
echo "2. Check agent status on your dashboard at: http://localhost:8000"
echo ""
echo "3. To stop an agent: ssh to the machine and press Ctrl+C"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check agent logs: tail -f $REMOTE_PATH/telemetry-agent-final/telemetry-agent.log"
echo "- Test connectivity: telnet $SERVER_IP 9876"
echo "- Check server logs for connection attempts"