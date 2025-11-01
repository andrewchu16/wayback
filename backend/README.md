# Route Finder Backend

FastAPI backend for calculating routes using multiple transportation modes.

## Setup

```bash
pip install -r requirements.txt
```

## Run

### Option 1: Using the helper script (Recommended)
```bash
python start_server.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Important**: Always use `--host 0.0.0.0` to allow connections from mobile devices!

The API will be available at:
- `http://localhost:8000` (from your computer)
- `http://YOUR_IP:8000` (from mobile devices on the same network)

API Documentation: `http://localhost:8000/docs`

## Troubleshooting Mobile Connection Issues

### Issue: "Connection timeout" or "Network request failed" on mobile device

1. **Verify the server is running with the correct host:**
   ```bash
   # Make sure you see "0.0.0.0" in the startup message
   python start_server.py
   ```

2. **Check Windows Firewall:**
   - Open Windows Defender Firewall
   - Click "Allow an app or feature through Windows Defender Firewall"
   - Find Python or add a new rule for port 8000
   - Or temporarily disable firewall to test (not recommended for production)

3. **Verify your computer's IP address:**
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" under your active network adapter (should be something like 192.168.0.171)

4. **Test connection from your computer first:**
   - Open browser: `http://localhost:8000`
   - Should see: `{"message":"Route Finder API"}`
   - Try: `http://192.168.0.171:8000` (replace with your IP)
   - Both should work if server is configured correctly

5. **Check if phone and computer are on the same network:**
   - Phone must be on the same Wi-Fi network as your computer
   - Mobile data won't work for local IP addresses

6. **Test with curl or browser on your phone:**
   - Open mobile browser: `http://192.168.0.171:8000`
   - Should see the JSON response

### Quick Test Command

Test if the server is accessible:
```bash
# From your computer
curl http://localhost:8000

# From your phone's browser
# Navigate to: http://YOUR_IP:8000
```

