#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Run the telemetry agent

echo "🤖 Starting SBOM telemetry agent..."

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate
python agent.py "$@"
