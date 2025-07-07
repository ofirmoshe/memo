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
  Image,
  ActionSheetIOS,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import { useTheme } from '../contexts/ThemeContext';
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

    // A helper to format the success message
    const formatSuccessMessage = (item: UserItem) => {
      const title = `✅ Saved: ${item.title || 'Untitled'}`;
      const description = item.description ? `\n\n📝 ${item.description.substring(0, 100)}...` : '';
      const tags = item.tags && item.tags.length > 0 ? `\n🏷️ Tags: ${item.tags.join(', ')}` : '';
      return `${title}${description}${tags}`;
    }

    try {
      // URL Check First
      if (/https?:\/\//.test(messageText)) {
        const [url, userContext] = extractUrlAndContext(messageText);
        if (url) {
          const result = await apiService.extractUrl(url, USER_ID, userContext || null);
          removeProcessingMessage();
          const successText = formatSuccessMessage(result);
          addMessage({ sender: 'memora', text: successText, itemId: result.id, type: 'text' });
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
        const successText = formatSuccessMessage(result);
        addMessage({ sender: 'memora', text: successText, itemId: result.id, type: 'text' });
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

  const getAssetName = (asset: ImagePicker.ImagePickerAsset | DocumentPicker.DocumentPickerAsset): string => {
    if ('fileName' in asset && asset.fileName) {
      return asset.fileName;
    }
    if ('name' in asset && asset.name) {
      return asset.name;
    }
    return 'upload.tmp'
  }

  const handleUploadPress = () => {
    ActionSheetIOS.showActionSheetWithOptions(
      {
        options: ['Cancel', 'Choose from Library', 'Choose Document'],
        cancelButtonIndex: 0,
      },
      (buttonIndex) => {
        if (buttonIndex === 1) {
          handleUpload('image');
        } else if (buttonIndex === 2) {
          handleUpload('document');
        }
      }
    );
  }

  const handleUpload = async (type: 'image' | 'document') => {
    let result: ImagePicker.ImagePickerResult | DocumentPicker.DocumentPickerResult | null = null;
    
    if (type === 'image') {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permissionResult.granted) {
        Alert.alert("Permission needed", "You need to allow access to your photos to upload images.");
        return;
      }
      result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
      });
    } else {
      result = await DocumentPicker.getDocumentAsync();
    }
    
    if (result.canceled || !result.assets) {
      return;
    }

    const asset = result.assets[0];
    const fileName = getAssetName(asset);

    const formData = new FormData();
    formData.append('user_id', USER_ID);
    // The 'file' key must match the backend FastAPI endpoint parameter name
    formData.append('file', {
      uri: asset.uri,
      name: fileName,
      type: asset.mimeType || 'application/octet-stream',
    } as any);

    setIsLoading(true);
    addMessage({ text: `Uploading ${fileName}...`, sender: 'memora', type: 'text' });
    
    // A helper to format the success message
    const formatSuccessMessage = (item: UserItem) => {
      const title = `✅ Saved: ${item.title || 'Untitled'}`;
      const description = item.description ? `\n\n📝 ${item.description.substring(0, 100)}...` : '';
      const tags = item.tags && item.tags.length > 0 ? `\n🏷️ Tags: ${item.tags.join(', ')}` : '';
      return `${title}${description}${tags}`;
    }
    
    try {
      const uploadResult = await apiService.uploadFile(formData, USER_ID);
      setMessages(prev => prev.slice(0, prev.length -1)); // remove uploading message
      const successText = formatSuccessMessage(uploadResult);
      addMessage({ sender: 'memora', text: successText, itemId: uploadResult.id, type: 'text' });
    } catch (error: any) {
      setMessages(prev => prev.slice(0, prev.length -1)); // remove uploading message
      Alert.alert('Upload Failed', error.message || 'Could not upload the file.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteMemory = async (itemId: string) => {
    Alert.alert('Delete Memory', 'Are you sure you want to permanently delete this memory?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive',
        onPress: async () => {
          try {
            await apiService.deleteItem(itemId, USER_ID);
            setMessages(prev => 
              prev.map(m => {
                if (m.itemId === itemId || m.searchResult?.id === itemId) {
                  return { ...m, isDeleted: true, text: '🗑️ Memory deleted.', type: 'text' };
                }
                return m;
              })
            );
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

  const getPreviewImageUrl = (item: SearchResult | UserItem): string | null => {
    // For uploaded images, construct the direct file URL
    if (item.media_type === 'image' && item.file_path) {
      return `${API_BASE_URL}/file/${item.id}?user_id=${USER_ID}`;
    }
    // For extracted URLs, use the image from content_data
    if (item.media_type === 'url' && item.content_data?.image) {
      return item.content_data.image;
    }
    // Fallback for youtube links
    if (item.url?.includes('youtube.com') || item.url?.includes('youtu.be')) {
      const videoId = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/.exec(item.url)?.[1];
      if (videoId) return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
    }
    return null;
  };

  const SearchResultMessage = ({ result }: { result: SearchResult }) => {
    const styles = getStyles(theme);
    const previewImage = getPreviewImageUrl(result);

    return (
      <View style={[styles.messageBubble, styles.memoraMessageBubble, styles.searchResultBubble]}>
        {previewImage && <Image source={{ uri: previewImage }} style={styles.searchResultImage} />}
        <View style={styles.searchResultContent}>
          <Text style={[styles.memoraMessageText, styles.searchResultTitle]}>{result.title || 'Untitled Memory'}</Text>
          {result.media_type === 'text' && result.content_data ? (
            <Text style={styles.memoraMessageText}>{result.content_data}</Text>
          ) : result.description && (
            <Text style={styles.memoraMessageText} numberOfLines={3}>{result.description}</Text>
          )}
          {result.url && (
            <TouchableOpacity onPress={() => Linking.openURL(result.url!)}>
              <Text style={styles.searchResultUrl} numberOfLines={1}>{result.url}</Text>
            </TouchableOpacity>
          )}
          <View style={styles.searchResultFooter}>
            {result.similarity_score && (
              <Text style={styles.searchResultRelevance}>Relevance: {(result.similarity_score * 100).toFixed(0)}%</Text>
            )}
            <TouchableOpacity onPress={() => handleDeleteMemory(result.id)} style={styles.deleteButton}>
              <Text style={styles.deleteButtonText}>Delete</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  const styles = getStyles(theme);

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.flex} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.header}>
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
                    <TouchableOpacity onPress={() => handleDeleteMemory(msg.itemId!)} style={styles.deleteButton}>
                      <Text style={styles.deleteButtonText}>Delete</Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            </View>
          ))}
        </ScrollView>
        <View style={styles.inputWrapper}>
          <TouchableOpacity style={styles.uploadButton} onPress={handleUploadPress}>
            <Text style={styles.uploadButtonText}>+</Text>
          </TouchableOpacity>
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
  uploadButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  uploadButtonText: {
    color: theme.colors.text,
    fontSize: 24,
    fontWeight: 'bold',
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
    padding: 0,
    overflow: 'hidden',
  },
  searchResultImage: {
    width: '100%',
    height: 150,
    backgroundColor: theme.colors.border,
  },
  searchResultContent: {
    padding: 12,
  },
  searchResultTitle: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  searchResultUrl: {
    color: theme.colors.textTertiary,
    textDecorationLine: 'underline',
    marginTop: 4,
    fontSize: 12,
  },
  searchResultFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  searchResultRelevance: {
    fontSize: 12,
    color: theme.colors.textTertiary,
  }
}); 