# ngrok Setup Guide

## ✅ Setup Complete!

Your ngrok tunnel is now configured and running.

## Current Configuration

- **Backend URL:** `https://f997b6488d2f.ngrok-free.app`
- **Local Backend:** `http://localhost:8000`
- **ngrok Dashboard:** `http://localhost:4040`

## How It Works

1. **Backend runs locally** on port 8000
2. **ngrok creates a public HTTPS tunnel** to your local backend
3. **Your phone app connects** to the ngrok URL from anywhere (Wi-Fi, mobile data, etc.)
4. **No network configuration needed!**

## Starting Everything

### Option 1: Manual (Current Setup)

**Terminal 1 - Start Backend:**
```bash
cd backend
python start_server.py
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 8000
```

### Option 2: Use Helper Script

```bash
cd backend
.\start_with_ngrok.ps1
```

## Getting Your ngrok URL

After starting ngrok, get your URL:

```bash
cd backend
.\get_ngrok_url.ps1
```

Or check the ngrok web interface:
- Open: `http://localhost:4040`
- Look for the "Forwarding" URL

## Updating the App

If your ngrok URL changes (they do change on free tier after restart):

1. Run `.\get_ngrok_url.ps1` to get the new URL
2. Update `frontend/services/routeService.ts`:
   ```typescript
   const API_BASE_URL = 'https://YOUR-NEW-NGROK-URL.ngrok-free.app';
   ```
3. Restart your Expo app

## Testing

1. **Start backend:** `cd backend && python start_server.py`
2. **Start ngrok:** `ngrok http 8000` (in another terminal)
3. **Get URL:** `cd backend && .\get_ngrok_url.ps1`
4. **Update app** if URL changed
5. **Test from phone** - Works from anywhere now!

## ngrok Features

- ✅ HTTPS (secure connection)
- ✅ Works from anywhere (no local network needed)
- ✅ Works on mobile data
- ✅ Free tier available
- ✅ Web dashboard for monitoring

## Important Notes

- **Free ngrok URLs change** when you restart ngrok
- **ngrok free tier** may show a warning page (users need to click through)
- For production, consider ngrok paid plan or deploy backend to cloud

## Troubleshooting

**ngrok not connecting?**
- Make sure backend is running on port 8000
- Check `http://localhost:8000` works in browser
- Verify ngrok is running: `http://localhost:4040`

**URL not working?**
- Free ngrok URLs expire/change - get a new one with `.\get_ngrok_url.ps1`
- Check ngrok dashboard for connection status
- Make sure both backend and ngrok are running

