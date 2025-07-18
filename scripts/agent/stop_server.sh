#!/bin/bash

# Helper script to stop Python HTTP file server running on port 17277

PORT=17277
PIDFILE="/tmp/python_server_$PORT.pid"

echo "Stopping Python HTTP file server on port $PORT..."

# Method 1: Stop using PID file (if server was started with start_server.sh)
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Found server process with PID: $PID"
        kill "$PID"
        
        # Wait for process to terminate
        sleep 1
        if kill -0 "$PID" 2>/dev/null; then
            echo "Process didn't terminate gracefully, forcing kill..."
            kill -9 "$PID"
        fi
        
        rm -f "$PIDFILE"
        echo "Server stopped successfully"
    else
        echo "PID file exists but process is not running"
        rm -f "$PIDFILE"
    fi
else
    echo "No PID file found, searching for process by port..."
    
    # Method 2: Find and kill process using the port
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Found process using port $PORT with PID: $PID"
        
        # Check if it's a Python process
        if ps -p "$PID" -o comm= | grep -q python; then
            kill "$PID"
            
            # Wait for process to terminate
            sleep 1
            if kill -0 "$PID" 2>/dev/null; then
                echo "Process didn't terminate gracefully, forcing kill..."
                kill -9 "$PID"
            fi
            echo "Server stopped successfully"
        else
            echo "Process on port $PORT is not a Python process"
            echo "Process info:"
            ps -p "$PID" -o pid,ppid,comm,args
            echo "Use 'kill $PID' manually if you want to stop it"
        fi
    else
        echo "No process found using port $PORT"
    fi
fi

# Clean up log file if it exists
LOGFILE="python_server_$PORT.log"
if [ -f "$LOGFILE" ]; then
    echo "Removing log file: $LOGFILE"
    rm -f "$LOGFILE"
fi
