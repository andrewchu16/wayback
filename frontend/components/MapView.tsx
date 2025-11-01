import React from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_DEFAULT } from 'react-native-maps';
import { Route } from '../services/routeService';

interface MapViewComponentProps {
  currentLocation: { latitude: number; longitude: number };
  destination?: { latitude: number; longitude: number };
  routes: Route[];
  selectedRouteId?: string;
}

export default function MapViewComponent({
  currentLocation,
  destination,
  routes,
  selectedRouteId,
}: MapViewComponentProps) {
  const parsePolyline = (polyline: string): Array<{ latitude: number; longitude: number }> => {
    // Simple polyline parser - format: "lat1,lon1|lat2,lon2|..."
    return polyline.split('|').map((point) => {
      const [lat, lon] = point.split(',').map(Number);
      return { latitude: lat, longitude: lon };
    });
  };

  const getRegion = () => {
    if (destination) {
      const lat = (currentLocation.latitude + destination.latitude) / 2;
      const lon = (currentLocation.longitude + destination.longitude) / 2;
      const latDelta = Math.abs(currentLocation.latitude - destination.latitude) * 1.5;
      const lonDelta = Math.abs(currentLocation.longitude - destination.longitude) * 1.5;
      
      return {
        latitude: lat,
        longitude: lon,
        latitudeDelta: Math.max(latDelta, 0.01),
        longitudeDelta: Math.max(lonDelta, 0.01),
      };
    }
    
    return {
      latitude: currentLocation.latitude,
      longitude: currentLocation.longitude,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01,
    };
  };

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_DEFAULT}
        style={styles.map}
        initialRegion={getRegion()}
        showsUserLocation
        showsMyLocationButton
      >
        <Marker
          coordinate={currentLocation}
          title="Your Location"
          pinColor="blue"
        />
        
        {destination && (
          <Marker
            coordinate={destination}
            title="Destination"
            pinColor="red"
          />
        )}

        {routes.map((route) => {
          const coordinates = parsePolyline(route.polyline);
          const isSelected = route.id === selectedRouteId;
          
          return (
            <Polyline
              key={route.id}
              coordinates={coordinates}
              strokeColor={isSelected ? '#007AFF' : '#999'}
              strokeWidth={isSelected ? 4 : 2}
              lineDashPattern={isSelected ? undefined : [5, 5]}
            />
          );
        })}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
});

