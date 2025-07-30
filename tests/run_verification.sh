#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Run automated verification tests for Perseus

echo "Perseus Automated Verification System"
echo "===================================="
echo ""

# Check if Perseus is running
echo "Checking if Perseus API is running..."
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "ERROR: Perseus API is not running on http://localhost:8000"
    echo "Please start Perseus first with: docker-compose up -d"
    exit 1
fi
echo "✓ Perseus API is running"
echo ""

# Run the verification
echo "Starting automated verification..."
echo "This will simulate few concurrent users performing various analyses"
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Run the verification script
python3 ./automated_verification.py

echo ""
echo "Verification complete! Check the generated report in tests/verification_report_*.json"