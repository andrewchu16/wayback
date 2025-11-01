import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import HomeMapScreen from './screens/HomeMapScreen';
import LoadingScreen from './screens/LoadingScreen';
import RoutesListScreen from './screens/RoutesListScreen';

export type RootStackParamList = {
  Home: undefined;
  Loading: {
    origin: { latitude: number; longitude: number };
    destination: { latitude: number; longitude: number };
    destinationQuery: string;
  };
  RoutesList: {
    routes: any[];
    origin: { latitude: number; longitude: number };
    destination: { latitude: number; longitude: number };
  };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen name="Home" component={HomeMapScreen} />
        <Stack.Screen name="Loading" component={LoadingScreen} />
        <Stack.Screen name="RoutesList" component={RoutesListScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
