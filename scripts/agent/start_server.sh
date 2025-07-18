#!/bin/bash

# Helper script to start Python HTTP file server
# Serves files from the current directory on port 17277

PORT=17277
HOST="0.0.0.0"

echo "Starting Python HTTP file server..."
echo "Serving files from: $(pwd)"
echo "Server will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Check if Python 3 is available, fallback to Python 2 if needed
if command -v python3 &> /dev/null; then
    echo "Using Python 3..."
    python3 -m http.server $PORT --bind $HOST
elif command -v python &> /dev/null; then
    echo "Using Python 2..."
    python -m SimpleHTTPServer $PORT
else
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi
