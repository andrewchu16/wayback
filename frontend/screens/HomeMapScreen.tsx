import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import MapViewComponent from '../components/MapView';
import SearchBar from '../components/SearchBar';
import { LocationService, LocationCoordinates } from '../services/locationService';
import { GeocodingService } from '../services/geocodingService';
import { AutocompleteSuggestion } from '../services/geocodingService';

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

  const handleSuggestionSelect = async (suggestion: AutocompleteSuggestion) => {
    if (!currentLocation) {
      Alert.alert('Error', 'Please wait for your location to be loaded.');
      return;
    }

    // Use the suggestion's coordinates directly
    const destination: LocationCoordinates = {
      latitude: suggestion.lat,
      longitude: suggestion.lng,
    };

    // Navigate to loading screen with origin and destination
    navigation.navigate('Loading', {
      origin: currentLocation,
      destination,
      destinationQuery: suggestion.display_name,
    });
  };

  const handleSearch = async (destinationQuery: string) => {
    if (!currentLocation) {
      Alert.alert('Error', 'Please wait for your location to be loaded.');
      return;
    }

    // Geocode the query string
    try {
      const location = await GeocodingService.geocode(destinationQuery, currentLocation);
      
      if (!location) {
        Alert.alert(
          'Location Not Found',
          `Could not find a location for "${destinationQuery}". Please try a different search term.`
        );
        return;
      }

      const destination: LocationCoordinates = {
        latitude: location.latitude,
        longitude: location.longitude,
      };

      // Navigate to loading screen with origin and destination
      navigation.navigate('Loading', {
        origin: currentLocation,
        destination,
        destinationQuery,
      });
    } catch (error: any) {
      Alert.alert(
        'Geocoding Error',
        error.message || 'Failed to find the destination. Please try again.'
      );
    }
  };

  const handleMapPress = async (coordinate: LocationCoordinates) => {
    if (!currentLocation) {
      Alert.alert('Error', 'Please wait for your location to be loaded.');
      return;
    }

    // Reverse geocode the tapped location to get its name
    try {
      const suggestion = await GeocodingService.reverseGeocode(coordinate);
      
      if (!suggestion) {
        // If reverse geocoding fails, still allow selection with coordinates as fallback
        const destinationQuery = `${coordinate.latitude.toFixed(6)}, ${coordinate.longitude.toFixed(6)}`;
        navigation.navigate('Loading', {
          origin: currentLocation,
          destination: coordinate,
          destinationQuery,
        });
        return;
      }

      // Use the reverse geocoded suggestion as destination
      const destination: LocationCoordinates = {
        latitude: suggestion.lat,
        longitude: suggestion.lng,
      };

      // Navigate to loading screen with origin and destination
      navigation.navigate('Loading', {
        origin: currentLocation,
        destination,
        destinationQuery: suggestion.display_name,
      });
    } catch (error: any) {
      Alert.alert(
        'Reverse Geocoding Error',
        error.message || 'Failed to get location name. Please try again.'
      );
    }
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
      <MapViewComponent 
        currentLocation={currentLocation} 
        routes={[]} 
        onMapPress={handleMapPress}
      />
      <View style={styles.searchContainer}>
        <SearchBar 
          onSearch={handleSearch}
          onSuggestionSelect={handleSuggestionSelect}
          locationBias={currentLocation}
        />
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

