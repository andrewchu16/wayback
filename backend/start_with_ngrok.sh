#!/bin/bash
# Bash script to start backend with ngrok tunnel

echo "Starting Route Finder Backend with ngrok..."
echo "=========================================="

# Check if backend server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Backend server is already running on port 8000"
    echo "Starting ngrok tunnel..."
else
    echo "Starting backend server..."
    
    # Start backend in background
    python start_server.py &
    BACKEND_PID=$!
    
    echo "Waiting for server to start..."
    sleep 3
    
    echo "Backend server started (PID: $BACKEND_PID)"
    echo "Starting ngrok tunnel..."
fi

# Start ngrok
ngrok http 8000

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "ngrok tunnel is starting..."
echo "Check the ngrok terminal or web interface for your URL"
echo ""
echo "Next steps:"
echo "1. Copy the 'Forwarding' URL from ngrok (e.g., https://abc123.ngrok.io)"
echo "2. Update frontend/services/routeService.ts with that URL"
echo "3. Make sure to use HTTPS (not HTTP)"

