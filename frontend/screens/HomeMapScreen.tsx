import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import MapViewComponent from '../components/MapView';
import SearchBar from '../components/SearchBar';
import { LocationService, LocationCoordinates } from '../services/locationService';

interface HomeMapScreenProps {
  navigation: any;
}

export default function HomeMapScreen({ navigation }: HomeMapScreenProps) {
  const [currentLocation, setCurrentLocation] = useState<LocationCoordinates | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCurrentLocation();
  }, []);

  const loadCurrentLocation = async () => {
    try {
      setIsLoading(true);
      const location = await LocationService.getCurrentLocation();
      setCurrentLocation(location);
    } catch (error: any) {
      Alert.alert(
        'Location Error',
        error.message || 'Failed to get your location. Please enable location permissions.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (destinationQuery: string) => {
    if (!currentLocation) {
      Alert.alert('Error', 'Please wait for your location to be loaded.');
      return;
    }

    // For now, use a simple geocoding placeholder
    // In production, you'd use a real geocoding service
    // For demo purposes, we'll use a mock destination near the current location
    const destination: LocationCoordinates = {
      latitude: currentLocation.latitude + 0.01,
      longitude: currentLocation.longitude + 0.01,
    };

    // Navigate to loading screen with origin and destination
    navigation.navigate('Loading', {
      origin: currentLocation,
      destination,
      destinationQuery,
    });
  };

  if (isLoading || !currentLocation) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <MapViewComponent currentLocation={currentLocation} routes={[]} />
      <View style={styles.searchContainer}>
        <SearchBar onSearch={handleSearch} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchContainer: {
    position: 'absolute',
    top: 60,
    left: 0,
    right: 0,
  },
});

