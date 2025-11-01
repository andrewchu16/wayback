import React from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_DEFAULT } from 'react-native-maps';
import { Route } from '../services/routeService';

interface MapViewComponentProps {
  currentLocation: { latitude: number; longitude: number };
  destination?: { latitude: number; longitude: number };
  routes: Route[];
  selectedRouteId?: string;
  onMapPress?: (coordinate: { latitude: number; longitude: number }) => void;
}

export default function MapViewComponent({
  currentLocation,
  destination,
  routes,
  selectedRouteId,
  onMapPress,
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

  const handleMapPress = (event: any) => {
    // Only handle press if onMapPress callback is provided
    // Ignore presses on markers by checking if it's a coordinate press
    if (onMapPress && event.nativeEvent.coordinate) {
      onMapPress(event.nativeEvent.coordinate);
    }
  };

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_DEFAULT}
        style={styles.map}
        initialRegion={getRegion()}
        showsUserLocation
        showsMyLocationButton
        onPress={onMapPress ? handleMapPress : undefined}
      >
        <Marker
          coordinate={currentLocation}
          title="Your Location"
          pinColor="blue"
          onPress={() => {}} // Prevent marker press from triggering map press
        />
        
        {destination && (
          <Marker
            coordinate={destination}
            title="Destination"
            pinColor="red"
            onPress={() => {}} // Prevent marker press from triggering map press
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

