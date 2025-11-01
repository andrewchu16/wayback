import * as Linking from 'expo-linking';

export type TransportMode = 'Lime' | 'Walking' | 'Public Transit';

export class DeepLinkService {
  static async openTransportApp(
    mode: TransportMode,
    origin: { latitude: number; longitude: number },
    destination: { latitude: number; longitude: number }
  ): Promise<void> {
    const schemes: Record<TransportMode, string> = {
      Lime: 'lime://',
      Walking: 'maps://',
      'Public Transit': 'maps://',
    };

    const scheme = schemes[mode];
    
    if (!scheme) {
      throw new Error(`Unknown transport mode: ${mode}`);
    }

    // Build deep link URL based on transport mode
    let url: string;
    
    if (mode === 'Walking' || mode === 'Public Transit') {
      // Apple Maps URL format
      url = `http://maps.apple.com/?saddr=${origin.latitude},${origin.longitude}&daddr=${destination.latitude},${destination.longitude}&dirflg=w`;
    } else {
      // Transportation apps typically use different URL formats
      // These are common formats - adjust based on actual app documentation
      url = `${scheme}?action=setPickup&pickup[latitude]=${origin.latitude}&pickup[longitude]=${origin.longitude}&dropoff[latitude]=${destination.latitude}&dropoff[longitude]=${destination.longitude}`;
    }

    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        // Fallback to Apple Maps if app not installed
        if (mode !== 'Walking' && mode !== 'Public Transit') {
          const mapsUrl = `http://maps.apple.com/?saddr=${origin.latitude},${origin.longitude}&daddr=${destination.latitude},${destination.longitude}`;
          await Linking.openURL(mapsUrl);
        } else {
          throw new Error(`Cannot open ${mode} app. Please install it first.`);
        }
      }
    } catch (error) {
      console.error('Deep link error:', error);
      throw error;
    }
  }
}

