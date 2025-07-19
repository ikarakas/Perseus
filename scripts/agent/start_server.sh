#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0

# Helper script to start Python HTTP file server in background
# Serves files from the current directory on port 17277

PORT=17277
HOST="0.0.0.0"
PIDFILE="/tmp/python_server_$PORT.pid"
LOGFILE="python_server_$PORT.log"

# Check if server is already running
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Server is already running on port $PORT (PID: $(cat "$PIDFILE"))"
    echo "Use ./stop_server.sh to stop it first"
    exit 1
fi

echo "Starting Python HTTP file server in background..."
echo "Serving files from: $(pwd)"
echo "Server will be available at: http://localhost:$PORT"
echo "Use ./stop_server.sh to stop the server"
echo ""

# Check if Python 3 is available, fallback to Python 2 if needed
if command -v python3 &> /dev/null; then
    echo "Using Python 3..."
    nohup python3 -m http.server $PORT --bind $HOST > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
elif command -v python &> /dev/null; then
    echo "Using Python 2..."
    nohup python -m SimpleHTTPServer $PORT > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
else
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

echo "Server started with PID: $(cat "$PIDFILE")"
echo "Server logs: $LOGFILE"
