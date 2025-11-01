#!/usr/bin/env python3
"""
Helper script to start the FastAPI server with proper configuration
for mobile device access.
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Route Finder API server...")
    print("Server will be accessible at:")
    print("  - http://localhost:8000 (local)")
    print("  - http://192.168.0.171:8000 (from mobile devices on same network)")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Bind to all interfaces so mobile devices can connect
        port=8000,
        reload=True,  # Auto-reload on code changes
    )

