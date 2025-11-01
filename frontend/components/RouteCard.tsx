import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Route } from '../services/routeService';

interface RouteCardProps {
  route: Route;
  isSelected: boolean;
  onPress: () => void;
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  if (mins < 60) {
    return `${mins} min`;
  }
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return remainingMins > 0 ? `${hours}h ${remainingMins}min` : `${hours}h`;
};

const formatDistance = (meters: number): string => {
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(1)} km`;
};

const getTransportIcon = (mode: string): string => {
  const icons: Record<string, string> = {
    Lime: '🛴',
    Walking: '🚶',
    'Public Transit': '🚌',
  };
  return icons[mode] || '📍';
};

export default function RouteCard({ route, isSelected, onPress }: RouteCardProps) {
  const primaryMode = route.transport_modes[0];
  
  return (
    <TouchableOpacity
      style={[styles.card, isSelected && styles.cardSelected]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.icon}>{getTransportIcon(primaryMode)}</Text>
        <View style={styles.info}>
          <Text style={styles.transportMode}>{primaryMode}</Text>
          <Text style={styles.details}>
            {formatDistance(route.total_distance_meters)} • {formatDuration(route.total_duration_seconds)}
          </Text>
        </View>
        <View style={styles.costContainer}>
          {route.cost_usd > 0 ? (
            <Text style={styles.cost}>${route.cost_usd.toFixed(2)}</Text>
          ) : (
            <Text style={styles.free}>Free</Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginVertical: 6,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F8FF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
    fontSize: 32,
    marginRight: 12,
  },
  info: {
    flex: 1,
  },
  transportMode: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  details: {
    fontSize: 14,
    color: '#666',
  },
  costContainer: {
    alignItems: 'flex-end',
  },
  cost: {
    fontSize: 18,
    fontWeight: '700',
    color: '#007AFF',
  },
  free: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
  },
});

