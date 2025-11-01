import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { RouteService, Route } from '../services/routeService';
import { LocationCoordinates } from '../services/locationService';

interface LoadingScreenProps {
  navigation: any;
  route: {
    params: {
      origin: LocationCoordinates;
      destination: LocationCoordinates;
      destinationQuery: string;
    };
  };
}

export default function LoadingScreen({ navigation, route }: LoadingScreenProps) {
  const { origin, destination } = route.params;
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    calculateRoutes();
  }, []);

  const calculateRoutes = async () => {
    try {
      const routes = await RouteService.calculateRoutes(origin, destination);
      navigation.replace('RoutesList', {
        routes,
        origin,
        destination,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to calculate routes');
      // Navigate back after a delay if error
      setTimeout(() => {
        navigation.goBack();
      }, 2000);
    }
  };

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#007AFF" />
      <Text style={styles.loadingText}>Calculating your routes...</Text>
      <Text style={styles.subtitle}>Finding the best options for you</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
  },
  loadingText: {
    marginTop: 20,
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
  },
  subtitle: {
    marginTop: 8,
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
  },
});

