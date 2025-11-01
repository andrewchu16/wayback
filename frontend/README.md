# Route Finder - React Native Expo App

A React Native Expo app that helps users find the fastest routes using multiple transportation modes (Uber, Lyft, Lime, walking, public transit).

## Features

- Real-time location tracking
- Multiple route options with different transportation modes
- Route visualization on map
- Payment integration with Stripe (for paid routes)
- Deep linking to transportation apps (Uber, Lyft, Lime, Apple Maps)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure Stripe (optional, for payment functionality):
   - Update `STRIPE_PUBLISHABLE_KEY` in `screens/RoutesListScreen.tsx` with your Stripe publishable key

3. Configure backend URL:
   - Update `API_BASE_URL` in `services/routeService.ts` if your backend is not running on `http://localhost:8000`

4. Start the Expo development server:
```bash
npm start
```

5. Run on iOS:
```bash
npm run ios
```

## Project Structure

- `App.tsx` - Main app entry with navigation setup
- `screens/` - Screen components
  - `HomeMapScreen.tsx` - Default map with location and destination search
  - `LoadingScreen.tsx` - Route calculation loading state
  - `RoutesListScreen.tsx` - Display calculated routes with list and map
- `components/` - Reusable components
  - `MapView.tsx` - Map display with route visualization
  - `SearchBar.tsx` - Destination search input
  - `RouteCard.tsx` - Individual route display card
- `services/` - Business logic
  - `locationService.ts` - Get current location
  - `routeService.ts` - API calls for route calculation
  - `paymentService.ts` - Stripe payment integration
  - `deepLinkService.ts` - iOS deep linking to transportation apps

## Backend Integration

This app connects to a FastAPI backend (see `../backend/`). Make sure the backend is running before using the app.

## Notes

- The app requires location permissions
- Deep linking works on iOS devices
- Payment integration requires proper Stripe setup (currently uses mock for demo)

