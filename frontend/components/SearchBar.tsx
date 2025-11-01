import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  Text,
  ActivityIndicator,
  FlatList,
  Keyboard,
} from 'react-native';
import { GeocodingService, AutocompleteSuggestion } from '../services/geocodingService';
import { Location } from '../services/routeService';

interface SearchBarProps {
  onSearch: (destination: string) => void;
  onSuggestionSelect?: (suggestion: AutocompleteSuggestion) => void;
  placeholder?: string;
  isLoading?: boolean;
  locationBias?: Location;
}

export default function SearchBar({
  onSearch,
  onSuggestionSelect,
  placeholder = 'Enter destination...',
  isLoading = false,
  locationBias,
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Log render state changes
  useEffect(() => {
    console.log('[SearchBar] Render state changed:', {
      query,
      suggestionsCount: suggestions.length,
      showSuggestions,
      isLoadingSuggestions,
      shouldRenderSuggestions: showSuggestions && suggestions.length > 0,
    });
  }, [query, suggestions, showSuggestions, isLoadingSuggestions]);

  // Debounced autocomplete search
  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Don't search if query is too short
    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Set loading state
    setIsLoadingSuggestions(true);

    // Debounce the search
    debounceTimerRef.current = setTimeout(async () => {
      console.log('[SearchBar] Starting autocomplete search for query:', query.trim());
      try {
        const results = await GeocodingService.autocomplete(query, 5, locationBias);
        console.log('[SearchBar] Received autocomplete results:', results.length, 'suggestions');
        console.log('[SearchBar] Results data:', JSON.stringify(results, null, 2));
        
        setSuggestions(results);
        const shouldShow = results.length > 0;
        setShowSuggestions(shouldShow);
        
        console.log('[SearchBar] Updated state:', {
          suggestionsCount: results.length,
          showSuggestions: shouldShow,
          suggestions: results,
        });
      } catch (error) {
        console.error('[SearchBar] Autocomplete error:', error);
        setSuggestions([]);
        setShowSuggestions(false);
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 300); // 300ms debounce

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, locationBias]);

  const handleSearch = () => {
    if (query.trim()) {
      Keyboard.dismiss();
      setShowSuggestions(false);
      onSearch(query.trim());
    }
  };

  const handleSuggestionPress = (suggestion: AutocompleteSuggestion) => {
    setQuery(suggestion.display_name);
    setShowSuggestions(false);
    Keyboard.dismiss();
    
    if (onSuggestionSelect) {
      onSuggestionSelect(suggestion);
    } else {
      // Fallback: trigger search with the suggestion's display name
      onSearch(suggestion.display_name);
    }
  };

  const renderSuggestion = ({ item }: { item: AutocompleteSuggestion }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => handleSuggestionPress(item)}
    >
      <Text style={styles.suggestionText} numberOfLines={1}>
        {item.display_name}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.wrapper}>
      <View style={styles.container}>
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
          editable={!isLoading}
          onFocus={() => {
            if (suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          onBlur={() => {
            // Delay hiding suggestions to allow for suggestion press
            setTimeout(() => setShowSuggestions(false), 200);
          }}
        />
        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleSearch}
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.buttonText}>Search</Text>
          )}
        </TouchableOpacity>
      </View>
      
      {showSuggestions && suggestions.length > 0 && (
        <View style={styles.suggestionsContainer}>
          {isLoadingSuggestions ? (
            <View style={styles.suggestionItem}>
              <ActivityIndicator size="small" color="#007AFF" />
            </View>
          ) : (
            <FlatList
              data={suggestions}
              renderItem={renderSuggestion}
              keyExtractor={(item, index) => item.place_id?.toString() || index.toString()}
              keyboardShouldPersistTaps="handled"
              nestedScrollEnabled
            />
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'relative',
    zIndex: 1000,
  },
  container: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    margin: 16,
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  suggestionsContainer: {
    position: 'absolute',
    top: '100%',
    left: 16,
    right: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    marginTop: 4,
    maxHeight: 200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
    overflow: 'hidden',
  },
  suggestionItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  suggestionText: {
    fontSize: 16,
    color: '#333',
  },
});

