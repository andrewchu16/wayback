import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StripeProvider, useStripe } from '@stripe/stripe-react-native';
import MapViewComponent from '../components/MapView';
import RouteCard from '../components/RouteCard';
import { Route } from '../services/routeService';
import { LocationCoordinates } from '../services/locationService';
import { DeepLinkService, TransportMode } from '../services/deepLinkService';
import { PaymentService } from '../services/paymentService';

interface RoutesListScreenProps {
  navigation: any;
  route: {
    params: {
      routes: Route[];
      origin: LocationCoordinates;
      destination: LocationCoordinates;
    };
  };
}

function RoutesListContent({ navigation, route }: RoutesListScreenProps) {
  const { routes, origin, destination } = route.params;
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(
    routes[0]?.id || null
  );
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const stripe = useStripe();

  const handleSelectRoute = async () => {
    if (!selectedRouteId) {
      Alert.alert('Error', 'Please select a route first.');
      return;
    }

    const selectedRoute = routes.find((r) => r.id === selectedRouteId);
    if (!selectedRoute) return;

        // Check if route requires payment
        if (selectedRoute.cost_usd > 0) {
          setIsProcessingPayment(true);
          try {
            // For demo: Show payment confirmation alert
            // In production, integrate with actual Stripe payment flow
            Alert.alert(
              'Payment Required',
              `This route costs $${selectedRoute.cost_usd.toFixed(2)}. Continue?`,
              [
                { text: 'Cancel', style: 'cancel', onPress: () => setIsProcessingPayment(false) },
                {
                  text: 'Pay',
                  onPress: async () => {
                    try {
                      // TODO: Implement actual Stripe payment
                      // For now, simulate successful payment
                      const success = await PaymentService.processPayment(
                        stripe,
                        Math.round(selectedRoute.cost_usd * 100) // Convert to cents
                      );

                      if (success) {
                        await handleDeepLink(selectedRoute);
                      }
                    } catch (error: any) {
                      Alert.alert('Payment Error', error.message || 'Payment failed. Please try again.');
                      setIsProcessingPayment(false);
                    }
                  },
                },
              ]
            );
          } catch (error: any) {
            Alert.alert('Payment Error', error.message || 'Payment failed. Please try again.');
            setIsProcessingPayment(false);
          }
        } else {
          // Free route - directly open deep link
          await handleDeepLink(selectedRoute);
        }
  };

  const handleDeepLink = async (route: Route) => {
    try {
      const transportMode = route.transport_modes[0] as TransportMode;
      await DeepLinkService.openTransportApp(transportMode, origin, destination);
      
      // Show success message
      Alert.alert(
        'Route Selected',
        `Opening ${transportMode}...`,
        [{ text: 'OK', onPress: () => navigation.navigate('Home') }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to open transportation app.');
    }
  };

  const selectedRoute = routes.find((r) => r.id === selectedRouteId);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.mapContainer}>
        <MapViewComponent
          currentLocation={origin}
          destination={destination}
          routes={routes}
          selectedRouteId={selectedRouteId || undefined}
        />
      </View>

      <View style={styles.listContainer}>
        <Text style={styles.header}>Select Your Route</Text>
        <FlatList
          data={routes}
          renderItem={({ item }) => (
            <RouteCard
              route={item}
              isSelected={item.id === selectedRouteId}
              onPress={() => setSelectedRouteId(item.id)}
            />
          )}
          keyExtractor={(item) => item.id}
          style={styles.list}
        />

        <TouchableOpacity
          style={[styles.selectButton, isProcessingPayment && styles.selectButtonDisabled]}
          onPress={handleSelectRoute}
          disabled={isProcessingPayment || !selectedRouteId}
        >
          {isProcessingPayment ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.selectButtonText}>
              Select Route{selectedRoute && selectedRoute.cost_usd > 0 ? ` - $${selectedRoute.cost_usd.toFixed(2)}` : ''}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

export default function RoutesListScreen(props: RoutesListScreenProps) {
  // Stripe publishable key - replace with your actual key
  const STRIPE_PUBLISHABLE_KEY = 'pk_test_your_publishable_key_here';

  return (
    <StripeProvider publishableKey={STRIPE_PUBLISHABLE_KEY}>
      <RoutesListContent {...props} />
    </StripeProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  mapContainer: {
    height: '40%',
  },
  listContainer: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    fontSize: 24,
    fontWeight: '700',
    padding: 16,
    paddingBottom: 8,
    color: '#000',
  },
  list: {
    flex: 1,
  },
  selectButton: {
    backgroundColor: '#007AFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
  },
  selectButtonDisabled: {
    opacity: 0.6,
  },
  selectButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});

