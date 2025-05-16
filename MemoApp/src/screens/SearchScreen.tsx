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
import MessageBubble from '../components/MessageBubble';
import { ConnectionTest } from '../components/ConnectionTest';
import { ContentItem } from '../types/api';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from '../components/Logo';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';

type SearchScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Search'>;

type Message = {
  id: string;
  content: string | ContentItem;
  isUser: boolean;
};

const SearchScreen = () => {
  const navigation = useNavigation<SearchScreenNavigationProp>();
  const [input, setInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
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
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: `Error: ${error instanceof Error ? error.message : 'Failed to search'}`,
        isUser: false,
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  }, [error]);

  useEffect(() => {
    if (data?.items) {
      const newMessages = data.items.map((item, index) => ({
        id: `result-${item.id}-${index}`,
        content: item,
        isUser: false,
      }));
      setMessages((prev) => [...prev, ...newMessages]);
    }
  }, [data]);

  const handleSearch = () => {
    if (!input.trim()) return;

    const query = input.trim();
    setSearchQuery(query);
    
    const newMessage: Message = {
      id: `query-${Date.now()}`,
      content: query,
      isUser: true,
    };

    setMessages((prev) => [...prev, newMessage]);
  };

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
        
        <ConnectionTest />

        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <MessageBubble message={item.content} isUser={item.isUser} />
          )}
          contentContainerStyle={styles.messagesList}
        />
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#007AFF" />
          </View>
        )}
      </SafeAreaView>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}>
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Search your saved content..."
            placeholderTextColor="#8E8E93"
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
            <Icon name="search" size={24} color="#007AFF" />
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
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginRight: 8,
  },
  searchButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  messagesList: {
    padding: 16,
    paddingBottom: 80, // Add padding for the search container
  },
  loadingContainer: {
    padding: 8,
    alignItems: 'center',
  },
});

export default SearchScreen; 