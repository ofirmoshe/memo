import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ActivityIndicator,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  Platform,
  Text,
  KeyboardAvoidingView,
  Keyboard,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSearchContent } from '../services/api';
import { getUser } from '../services/user';
import { ContentItem } from '../types/api';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from '../components/Logo';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import ResultCard from '../components/ResultCard';
import theme from '../config/theme';

type SearchScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Search'>;

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
  const scrollViewRef = useRef<ScrollView>(null);
  const searchBarRef = useRef<View>(null);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const insets = useSafeAreaInsets();

  // Web-specific fix for search bar positioning
  useEffect(() => {
    if (Platform.OS === 'web') {
      // Add a style tag to the document head
      const styleTag = document.createElement('style');
      styleTag.innerHTML = `
        .search-bar-fixed {
          position: fixed !important;
          bottom: 0 !important;
          left: 0 !important;
          right: 0 !important;
          z-index: 9999 !important;
          background-color: white !important;
          border-top: 1px solid #E5E5EA !important;
        }
        
        .content-area {
          height: calc(100vh - 140px) !important;
          overflow: hidden !important;
          position: relative !important;
        }
        
        .results-scroll {
          height: 100% !important;
          overflow-y: scroll !important;
          -webkit-overflow-scrolling: touch !important;
          scrollbar-width: thin !important;
          scrollbar-color: #C7C7CC #F2F2F7 !important;
        }
        
        .results-scroll::-webkit-scrollbar {
          width: 8px !important;
        }
        
        .results-scroll::-webkit-scrollbar-track {
          background: #F2F2F7 !important;
          border-radius: 4px !important;
        }
        
        .results-scroll::-webkit-scrollbar-thumb {
          background-color: #C7C7CC !important;
          border-radius: 4px !important;
          border: 2px solid #F2F2F7 !important;
        }
        
        .results-scroll::-webkit-scrollbar-thumb:hover {
          background-color: #AEAEB2 !important;
        }
      `;
      document.head.appendChild(styleTag);
      
      // Function to apply the fixed class to the search bar
      const fixSearchBar = () => {
        const searchBarElement = document.getElementById('search-bar-container');
        if (searchBarElement) {
          searchBarElement.className = 'search-bar-fixed';
        }
        
        const contentArea = document.getElementById('content-area');
        if (contentArea) {
          contentArea.className = 'content-area';
        }
        
        const scrollView = document.getElementById('results-scroll');
        if (scrollView) {
          scrollView.className = 'results-scroll';
        }
      };
      
      // Apply immediately and after each render
      setTimeout(fixSearchBar, 0);
      setTimeout(fixSearchBar, 100);
      setTimeout(fixSearchBar, 500);
      
      // Add event listener for window resize to reapply styles
      window.addEventListener('resize', fixSearchBar);
      
      // Clean up
      return () => {
        document.head.removeChild(styleTag);
        window.removeEventListener('resize', fixSearchBar);
      };
    }
  }, []);

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
    }
  }, [error]);

  useEffect(() => {
    if (data?.items && searchQuery) {
      const newSection: ResultSection = {
        id: `query-${Date.now()}`,
        query: searchQuery,
        timestamp: Date.now(),
        results: data.items,
      };
      
      setResultSections(prev => [newSection, ...prev]);
      setSearchQuery('');
      
      if (scrollViewRef.current) {
        scrollViewRef.current.scrollTo({ y: 0, animated: true });
      }
      
      // Re-apply the fixed positioning for web
      if (Platform.OS === 'web') {
        const searchBarElement = document.getElementById('search-bar-container');
        if (searchBarElement) {
          searchBarElement.className = 'search-bar-fixed';
        }
        
        const scrollView = document.getElementById('results-scroll');
        if (scrollView) {
          scrollView.className = 'results-scroll';
        }
      }
    }
  }, [data, searchQuery]);

  // Web-specific fix for scrolling
  useEffect(() => {
    if (Platform.OS === 'web' && resultSections.length > 0) {
      // Direct DOM manipulation to ensure scrolling works
      const scrollView = document.getElementById('results-scroll');
      if (scrollView) {
        // Force the scrollView to be scrollable
        scrollView.style.overflowY = 'scroll';
        scrollView.style.height = '100%';
        
        // Add some test content to ensure scrolling is possible
        const contentArea = document.getElementById('content-area');
        if (contentArea) {
          contentArea.style.height = 'calc(100vh - 140px)';
          contentArea.style.overflow = 'hidden';
        }
      }
    }
  }, [resultSections]);

  // Add keyboard listeners
  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      () => {
        setKeyboardVisible(true);
      }
    );
    const keyboardDidHideListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setKeyboardVisible(false);
      }
    );

    return () => {
      keyboardDidShowListener.remove();
      keyboardDidHideListener.remove();
    };
  }, []);

  const handleSearch = () => {
    if (!input.trim()) return;
    const query = input.trim();
    setSearchQuery(query);
    setInput('');
    setIsTyping(false);
    Keyboard.dismiss();
  };

  const handleInputFocus = () => {
    setIsTyping(true);
  };

  const handleInputBlur = () => {
    setIsTyping(false);
  };

  // Navigate to tags screen
  const handleTagsPress = () => {
    navigation.navigate('Tags');
  };

  const renderResultSection = (item: ResultSection) => (
    <View key={item.id} style={styles.resultSection}>
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
    <SafeAreaView style={styles.outerContainer} edges={['top', 'right', 'left', 'bottom']}>
      {/* Header */}
      <View style={styles.toolbar}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.navigate('Home')}>
          <Icon name="home" size={28} color={theme.colors.primary} />
        </TouchableOpacity>
        <View style={styles.logoContainer}>
          <Logo size={32} color={theme.colors.primary} />
          <Text style={styles.appName}>Memora</Text>
        </View>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.iconButton} onPress={handleTagsPress}>
            <Icon name="pricetags" size={28} color={theme.colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => navigation.navigate('UrlSubmission')}>
            <Icon name="add-circle" size={32} color={theme.colors.accent} />
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Content Area */}
      <View style={styles.mainContainer}>
        <View 
          style={styles.contentArea}
          // @ts-ignore - Web only property
          id={Platform.OS === 'web' ? 'content-area' : undefined}
        >
          {resultSections.length === 0 && !isLoading ? (
            <View style={styles.emptyStateContainer}>
              <Icon name="search" size={64} color="#E5E5EA" />
              <Text style={styles.emptyStateTitle}>Search your memories</Text>
              <Text style={styles.emptyStateSubtitle}>
                Type a query below to search through your saved content
              </Text>
            </View>
          ) : (
            <ScrollView 
              ref={scrollViewRef}
              style={styles.scrollView}
              contentContainerStyle={[
                styles.resultsList,
                { paddingBottom: 80 + insets.bottom }
              ]}
              // @ts-ignore - Web only property
              id={Platform.OS === 'web' ? 'results-scroll' : undefined}
              showsVerticalScrollIndicator={true}
              persistentScrollbar={true}
            >
              {resultSections.map(section => renderResultSection(section))}
            </ScrollView>
          )}
          
          {isLoading && (
            <View style={styles.loadingOverlay}>
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.loadingText}>Searching...</Text>
              </View>
            </View>
          )}
        </View>
        
        {/* Search Bar - Fixed at bottom with proper safe area insets */}
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
          style={styles.keyboardAvoid}
        >
          <View 
            ref={searchBarRef}
            style={[
              styles.searchBarContainer,
              { paddingBottom: keyboardVisible ? 0 : insets.bottom }
            ]}
            // @ts-ignore - Web only property
            id={Platform.OS === 'web' ? 'search-bar-container' : undefined}
          >
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
          </View>
        </KeyboardAvoidingView>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  outerContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  mainContainer: {
    flex: 1,
    position: 'relative',
  },
  keyboardAvoid: {
    width: '100%',
  },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 0,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 0,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 6,
    zIndex: 10,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
  },
  contentArea: {
    flex: 1,
    position: 'relative',
    overflow: Platform.OS === 'web' ? 'hidden' : 'visible',
  },
  scrollView: {
    flex: 1,
    height: Platform.OS === 'web' ? '100%' : undefined,
    width: '100%',
    overflow: Platform.OS === 'web' ? 'scroll' : undefined,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appName: {
    fontSize: theme.font.size.xl,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginLeft: theme.spacing.md,
    letterSpacing: 1.2,
  },
  addButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22,
    backgroundColor: 'rgba(244,114,182,0.10)',
    marginLeft: theme.spacing.sm,
  },
  searchBarContainer: {
    backgroundColor: theme.colors.cardGlass,
    borderTopWidth: 0,
    width: '100%',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.md,
    backgroundColor: 'transparent',
  },
  input: {
    flex: 1,
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    fontSize: theme.font.size.md,
    marginRight: theme.spacing.md,
    color: theme.colors.text,
    borderWidth: 1.5,
    borderColor: 'transparent',
    fontWeight: '500',
  },
  inputFocused: {
    backgroundColor: theme.colors.card,
    borderWidth: 1.5,
    borderColor: theme.colors.primary,
  },
  searchButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: 24,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2,
  },
  searchButtonDisabled: {
    backgroundColor: theme.colors.border,
  },
  resultsList: {
    padding: theme.spacing.md,
  },
  resultSection: {
    marginBottom: theme.spacing.xl,
  },
  queryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
    paddingHorizontal: theme.spacing.xs,
  },
  queryText: {
    fontSize: theme.font.size.md,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginLeft: theme.spacing.sm,
    flex: 1,
  },
  timestampText: {
    fontSize: theme.font.size.xs,
    color: theme.colors.textSecondary,
  },
  resultCount: {
    fontSize: theme.font.size.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
    paddingHorizontal: theme.spacing.xs,
  },
  resultsContainer: {
    gap: theme.spacing.sm,
  },
  emptyResultsContainer: {
    padding: theme.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 16,
  },
  emptyResultsText: {
    fontSize: theme.font.size.md,
    color: theme.colors.textSecondary,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  loadingContainer: {
    padding: theme.spacing.lg,
    borderRadius: 16,
    backgroundColor: theme.colors.cardGlass,
    alignItems: 'center',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 3,
  },
  loadingText: {
    marginTop: theme.spacing.md,
    fontSize: theme.font.size.md,
    color: theme.colors.primary,
  },
  emptyStateContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  emptyStateTitle: {
    fontSize: theme.font.size.xl,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  emptyStateSubtitle: {
    fontSize: theme.font.size.md,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
    marginLeft: theme.spacing.sm,
  },
});

export default SearchScreen; 