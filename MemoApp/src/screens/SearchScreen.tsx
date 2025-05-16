import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Text,
} from 'react-native';
import { useSearchContent } from '../services/api';
import { getUser } from '../services/user';
import { ConnectionTest } from '../components/ConnectionTest';
import { ContentItem } from '../types/api';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from '../components/Logo';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import ResultCard from '../components/ResultCard';

type SearchScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Search'>;

type QueryItem = {
  id: string;
  text: string;
  timestamp: number;
};

type ResultSection = {
  id: string;
  query: string;
  timestamp: number;
  results: ContentItem[];
};

const SearchScreen = () => {
  const navigation = useNavigation<SearchScreenNavigationProp>();
  const [input, setInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [resultSections, setResultSections] = useState<ResultSection[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    const loadUserId = async () => {
      const id = await getUser();
      setUserId(id);
    };
    loadUserId();
  }, []);

  const { data, isLoading, error } = useSearchContent(
    { user_id: userId || '', query: searchQuery },
    { enabled: Boolean(userId) && searchQuery.length > 0 }
  );

  useEffect(() => {
    if (error) {
      console.error('Search error:', error);
      // Show error in UI if needed
    }
  }, [error]);

  useEffect(() => {
    if (data?.items && searchQuery) {
      // Add new result section
      const newSection: ResultSection = {
        id: `query-${Date.now()}`,
        query: searchQuery,
        timestamp: Date.now(),
        results: data.items,
      };
      
      setResultSections(prev => [newSection, ...prev]);
      
      // Clear current search query after results are loaded
      setSearchQuery('');
      
      // Scroll to top to show new results
      if (flatListRef.current) {
        flatListRef.current.scrollToOffset({ offset: 0, animated: true });
      }
    }
  }, [data, searchQuery]);

  const handleSearch = () => {
    if (!input.trim()) return;

    const query = input.trim();
    setSearchQuery(query);
    setInput('');
    setIsTyping(false);
  };

  const handleInputFocus = () => {
    setIsTyping(true);
  };

  const handleInputBlur = () => {
    setIsTyping(false);
  };

  const renderResultSection = ({ item }: { item: ResultSection }) => (
    <View style={styles.resultSection}>
      <View style={styles.queryContainer}>
        <Icon name="search-outline" size={16} color="#007AFF" />
        <Text style={styles.queryText}>{item.query}</Text>
        <Text style={styles.timestampText}>
          {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>
      
      <Text style={styles.resultCount}>
        {item.results.length} {item.results.length === 1 ? 'result' : 'results'} found
      </Text>
      
      {item.results.length === 0 ? (
        <View style={styles.emptyResultsContainer}>
          <Text style={styles.emptyResultsText}>No matching content found</Text>
        </View>
      ) : (
        <View style={styles.resultsContainer}>
          {item.results.map((result) => (
            <ResultCard key={result.id} item={result} />
          ))}
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.toolbar}>
          <View style={styles.logoContainer}>
            <Logo size={28} />
            <Text style={styles.appName}>memo</Text>
          </View>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => navigation.navigate('UrlSubmission')}>
            <Icon name="add-circle" size={28} color="#007AFF" />
          </TouchableOpacity>
        </View>
        
        {/* <ConnectionTest /> */}

        {resultSections.length === 0 && !isLoading ? (
          <View style={styles.emptyStateContainer}>
            <Icon name="search" size={64} color="#E5E5EA" />
            <Text style={styles.emptyStateTitle}>Search your memories</Text>
            <Text style={styles.emptyStateSubtitle}>
              Type a query below to search through your saved content
            </Text>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={resultSections}
            keyExtractor={(item) => item.id}
            renderItem={renderResultSection}
            contentContainerStyle={styles.resultsList}
          />
        )}
        
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.loadingText}>Searching...</Text>
            </View>
          </View>
        )}
      </SafeAreaView>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}>
        <View style={styles.searchContainer}>
          <TextInput
            style={[
              styles.input,
              isTyping && styles.inputFocused,
            ]}
            value={input}
            onChangeText={setInput}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            placeholder="Search your saved content..."
            placeholderTextColor="#8E8E93"
            returnKeyType="search"
            onSubmitEditing={handleSearch}
          />
          <TouchableOpacity 
            style={[
              styles.searchButton,
              !input.trim() && styles.searchButtonDisabled
            ]} 
            onPress={handleSearch}
            disabled={!input.trim()}>
            <Icon name="search" size={24} color={input.trim() ? "#007AFF" : "#C7C7CC"} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000000',
    marginLeft: 8,
  },
  addButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    backgroundColor: '#FFFFFF',
  },
  input: {
    flex: 1,
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    marginRight: 12,
  },
  inputFocused: {
    backgroundColor: '#E5E5EA',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  searchButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 24,
  },
  searchButtonDisabled: {
    backgroundColor: '#F2F2F7',
  },
  resultsList: {
    padding: 12,
    paddingBottom: 80,
  },
  resultSection: {
    marginBottom: 24,
  },
  queryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  queryText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 8,
    flex: 1,
  },
  timestampText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  resultCount: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  resultsContainer: {
    gap: 8,
  },
  emptyResultsContainer: {
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
  },
  emptyResultsText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  loadingContainer: {
    padding: 20,
    borderRadius: 12,
    backgroundColor: 'white',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#007AFF',
  },
  emptyStateContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#000000',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

export default SearchScreen; 