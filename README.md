# Route Finder App

A React Native Expo application that helps users find the fastest routes between their current location and destination using multiple transportation modes (Uber, Lyft, Lime, walking, public transit).

## Project Structure

- `frontend/` - React Native Expo app
- `backend/` - FastAPI backend for route calculations

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure Stripe (optional):
   - Update `STRIPE_PUBLISHABLE_KEY` in `screens/RoutesListScreen.tsx`

4. Start the Expo development server:
```bash
npm start
```

5. Run on iOS:
```bash
npm run ios
```

## App Flow

1. **Default Screen**: Shows a map centered on the user's current location with a search bar for entering the destination.

2. **Loading Screen**: After the user confirms a destination, shows a loading message while routes are being calculated.

3. **Routes List**: Displays all calculated routes with:
   - Distance and time estimates
   - Transportation mode
   - Cost (if applicable)
   - Interactive map showing all routes
   - Tap to select and view different routes on the map

4. **Route Selection**: When a user selects a route:
   - If the route costs money, prompts for payment via Stripe
   - After payment (or for free routes), opens the appropriate transportation app via deep linking

5. **Deep Linking**: 
   - Paid routes: Opens Uber, Lyft, or Lime apps
   - Free routes (walking/transit): Opens Apple Maps

## Features

- Real-time location tracking
- Multiple route options with different transportation modes
- Route visualization on interactive map
- Payment integration with Stripe
- iOS deep linking to transportation apps
- Modern, clean UI

## Technologies

### Frontend
- React Native with Expo
- TypeScript
- React Navigation
- React Native Maps
- Stripe React Native SDK
- Expo Location & Linking

### Backend
- FastAPI
- Python 3
- Pydantic for data validation

## Notes

- The app currently uses mock data for route calculations
- Geocoding (address to coordinates) is simplified for demo purposes
- Payment flow is set up but uses mock confirmation (integrate with your Stripe backend for production)
- Deep linking configured for iOS only

