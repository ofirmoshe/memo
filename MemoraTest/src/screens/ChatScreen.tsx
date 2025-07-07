import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Logo } from '../components/Logo';
import { apiService, UserItem, SearchResult } from '../services/api';
import { Theme } from '../config/theme';

// Import the base URL constant
const API_BASE_URL = 'https://memo-production-9d97.up.railway.app';

interface Message {
  id: string;
  text?: string;
  sender: 'user' | 'memora';
  timestamp: Date;
  isDeleted?: boolean;
  itemId?: string;
  searchResult?: SearchResult;
  type?: 'search_result' | 'text' | 'processing';
}

const USER_ID = '831447258';

export const ChatScreen: React.FC = () => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      text: "Hello! I'm Memora. How can I help you remember or find something today?",
      sender: 'memora',
      timestamp: new Date(),
      type: 'text',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, { ...message, id: Date.now().toString() + Math.random(), timestamp: new Date() }]);
  };
  
  const addProcessingMessage = () => {
    const processingId = 'processing-msg';
    setMessages(prev => [...prev, { id: processingId, sender: 'memora', type: 'processing', timestamp: new Date() }]);
    return () => setMessages(prev => prev.filter(m => m.id !== processingId));
  }

  const handleSendMessage = async () => {
    const messageText = inputText.trim();
    if (!messageText || isLoading) return;

    addMessage({ text: messageText, sender: 'user', type: 'text' });
    setInputText('');
    setIsLoading(true);
    const removeProcessingMessage = addProcessingMessage();

    try {
      // URL Check First
      if (/https?:\/\//.test(messageText)) {
        const [url, userContext] = extractUrlAndContext(messageText);
        if (url) {
          const result = await apiService.extractUrl(url, USER_ID, userContext || null);
          removeProcessingMessage();
          addMessage({ sender: 'memora', text: `✅ Saved: ${result.title || url}`, itemId: result.id, type: 'text' });
        }
        return;
      }
      
      // LLM Intent Detection
      const { intent, english_text, answer } = await apiService.detectIntent(messageText);
      
      if (intent === 'search') {
        const searchResults = await apiService.search(english_text, USER_ID);
        removeProcessingMessage();
        
        if (searchResults.length === 0) {
          addMessage({ sender: 'memora', text: `I couldn't find anything for "${english_text}".`, type: 'text' });
        } else {
          addMessage({ sender: 'memora', text: `Found ${searchResults.length} memories for "${english_text}":`, type: 'text' });
          searchResults.forEach(result => {
            addMessage({ sender: 'memora', searchResult: result, type: 'search_result' });
          });
        }
      } else if (intent === 'save') {
        const result = await apiService.saveText(messageText, USER_ID);
        removeProcessingMessage();
        addMessage({ sender: 'memora', text: `✅ Saved: ${result.title}`, itemId: result.id, type: 'text' });
      } else { // greeting or general
        removeProcessingMessage();
        addMessage({ sender: 'memora', text: answer || "Hello! How can I help you?", type: 'text' });
      }
    } catch (error: any) {
      removeProcessingMessage();
      console.error('Message handling error:', error);
      addMessage({ sender: 'memora', text: `❌ Sorry, an error occurred: ${error.message}`, type: 'text' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteMessage = (message: Message) => {
    if (!message.itemId) return;
    Alert.alert('Delete Memory', 'Are you sure you want to permanently delete this memory?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive',
        onPress: async () => {
          try {
            await apiService.deleteItem(message.itemId!, USER_ID);
            setMessages(prev => prev.map(m => m.id === message.id ? { ...m, isDeleted: true, text: '🗑️ Memory deleted.' } : m));
          } catch (error) {
            Alert.alert('Error', 'Could not delete the memory.');
          }
        }
      }
    ]);
  };

  const extractUrlAndContext = (text: string): [string | null, string] => {
    const urlPattern = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/;
    const match = text.match(urlPattern);
    if (!match) return [null, text];
    const url = match[0];
    const userContext = text.replace(url, '').trim();
    return [url, userContext];
  };
  
  const formatSearchResults = (results: UserItem[], query: string): string => {
    let response = `Found ${results.length} memories for "${query}":\n\n`;
    results.slice(0, 5).forEach((r, i) => {
      response += `${i + 1}. ${r.title || 'Untitled'}\n`;
      if (r.description) response += `   ${r.description.substring(0, 100)}...\n`;
      if (r.url) response += `   ${r.url}\n`;
      if(r.similarity_score) response += `   (Relevance: ${(r.similarity_score * 100).toFixed(0)}%)\n\n`;
    });
    return response;
  };

  const SearchResultMessage = ({ result }: { result: SearchResult }) => {
    const styles = getStyles(theme);
    return (
      <View style={[styles.messageBubble, styles.memoraMessageBubble, styles.searchResultBubble]}>
        <Text style={[styles.memoraMessageText, styles.searchResultTitle]}>{result.title || 'Untitled Memory'}</Text>
        {result.description && (
          <Text style={styles.memoraMessageText} numberOfLines={3}>{result.description}</Text>
        )}
        {result.url && (
          <TouchableOpacity onPress={() => Linking.openURL(result.url!)}>
            <Text style={styles.searchResultUrl}>{result.url}</Text>
          </TouchableOpacity>
        )}
        {result.similarity_score && (
          <Text style={styles.searchResultRelevance}>Relevance: {(result.similarity_score * 100).toFixed(0)}%</Text>
        )}
      </View>
    );
  }

  const styles = getStyles(theme);

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={80}>
        <View style={styles.header}>
          <Logo size={28} color={theme.colors.text} />
          <Text style={styles.headerTitle}>Memora</Text>
        </View>
        <ScrollView 
          ref={scrollViewRef} 
          style={styles.messagesContainer} 
          contentContainerStyle={styles.messagesContent}
          keyboardShouldPersistTaps="handled"
        >
          {messages.map((msg) => (
            <View key={msg.id} style={[styles.messageWrapper, msg.sender === 'user' ? styles.userMessageWrapper : styles.memoraMessageWrapper]}>
              {msg.type === 'search_result' && msg.searchResult ? (
                <SearchResultMessage result={msg.searchResult} />
              ) : msg.type === 'processing' ? (
                <ActivityIndicator style={{alignSelf: 'flex-start', margin: 10}} color={theme.colors.textTertiary} />
              ) : (
                <View style={[styles.messageBubble, msg.sender === 'user' ? styles.userMessageBubble : styles.memoraMessageBubble]}>
                  <Text style={msg.sender === 'user' ? styles.userMessageText : styles.memoraMessageText}>{msg.text}</Text>
                  {msg.sender === 'memora' && msg.itemId && !msg.isDeleted && (
                    <TouchableOpacity onPress={() => handleDeleteMessage(msg)} style={styles.deleteButton}>
                      <Text style={styles.deleteButtonText}>Delete</Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            </View>
          ))}
        </ScrollView>
        <View style={styles.inputWrapper}>
          <TextInput 
            style={styles.textInput} 
            value={inputText} 
            onChangeText={setInputText} 
            placeholder="Ask or save..." 
            placeholderTextColor={theme.colors.textTertiary} 
            editable={!isLoading} 
          />
          <TouchableOpacity 
            style={[
              styles.sendButton, 
              (!inputText.trim() || isLoading) && { backgroundColor: theme.colors.surface }
            ]} 
            onPress={handleSendMessage} 
            disabled={!inputText.trim() || isLoading}
          >
            <Text style={[styles.sendButtonText, { color: (!inputText.trim() || isLoading) ? theme.colors.textTertiary : theme.colors.background }]}>↑</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  flex: { flex: 1 },
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1, 
    borderBottomColor: theme.colors.border 
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: theme.colors.text },
  messagesContainer: { flex: 1 },
  messagesContent: { padding: 16 },
  messageWrapper: { marginVertical: 4, maxWidth: '85%' },
  userMessageWrapper: { alignSelf: 'flex-end' },
  memoraMessageWrapper: { alignSelf: 'flex-start' },
  messageBubble: { padding: 12, borderRadius: 18 },
  userMessageBubble: { backgroundColor: theme.colors.primary, borderBottomRightRadius: 4 },
  memoraMessageBubble: { backgroundColor: theme.colors.surface, borderBottomLeftRadius: 4 },
  userMessageText: { fontSize: 16, color: theme.colors.background, lineHeight: 22 },
  memoraMessageText: { fontSize: 16, color: theme.colors.text, lineHeight: 22 },
  deleteButton: { marginTop: 8, paddingVertical: 4, paddingHorizontal: 8, backgroundColor: theme.colors.background, borderRadius: 6, alignSelf: 'flex-start', borderWidth: 1, borderColor: theme.colors.border },
  deleteButtonText: { color: theme.colors.error, fontSize: 12, fontWeight: 'bold' },
  inputWrapper: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12, 
    paddingVertical: 8,
    borderTopWidth: 1, 
    borderTopColor: theme.colors.border 
  },
  textInput: { 
    flex: 1, 
    backgroundColor: theme.colors.surface, 
    borderRadius: 24, 
    paddingHorizontal: 16, 
    paddingVertical: Platform.OS === 'ios' ? 12 : 8, 
    fontSize: 16, 
    color: theme.colors.text, 
    marginRight: 8,
    maxHeight: 100,
  },
  sendButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: theme.colors.primary, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  sendButtonText: { 
    fontSize: 24, 
    fontWeight: 'bold',
    lineHeight: 28,
  },
  searchResultBubble: {
    width: '100%',
  },
  searchResultTitle: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  searchResultUrl: {
    color: theme.colors.primary,
    textDecorationLine: 'underline',
    marginTop: 4,
  },
  searchResultRelevance: {
    fontSize: 12,
    color: theme.colors.textTertiary,
    marginTop: 8,
  }
}); 