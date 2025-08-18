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
import { apiService, UserItem, SearchResult, API_BASE_URL } from '../services/api';
import { Theme } from '../config/theme';
import { Logo } from '../components/Logo';

// Import the base URL constant from the centralized API service

interface Message {
  id: string;
  text?: string;
  sender: 'user' | 'memora';
  timestamp: Date;
  isDeleted?: boolean;
  itemId?: string;
  searchResult?: SearchResult;
  type?: 'search_result' | 'text' | 'processing' | 'welcome';
}

const USER_ID = '831447258';

export const ChatScreen: React.FC = () => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      sender: 'memora',
      timestamp: new Date(),
      type: 'welcome',
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
    // Prefer explicit preview fields
    if ((item as any).preview_thumbnail_path) {
      return `${API_BASE_URL}/file/${item.id}?user_id=${USER_ID}`;
    }
    if ((item as any).preview_image_url) {
      return (item as any).preview_image_url;
    }
    // Legacy fallbacks
    if (item.media_type === 'image' && item.file_path) {
      return `${API_BASE_URL}/file/${item.id}?user_id=${USER_ID}`;
    }
    if (item.media_type === 'url' && (item as any).content_data?.image) {
      return (item as any).content_data.image;
    }
    // Fallback for youtube links
    if (item.url?.includes('youtube.com') || item.url?.includes('youtu.be')) {
      const videoId = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/.exec(item.url)?.[1];
      if (videoId) return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
    }
    return null;
  };

  const WelcomeMessage = () => {
    const styles = getStyles(theme);
    return (
      <View style={[styles.messageBubble, styles.memoraMessageBubble, styles.welcomeMessage]}>
        <View style={styles.welcomeHeader}>
          <Logo size={32} color={theme.colors.primary} />
          <Text style={[styles.memoraMessageText, styles.welcomeTitle]}>Memora</Text>
        </View>
        <Text style={styles.memoraMessageText}>
          Hello! I'm your personal memory assistant. How can I help you remember or find something today?
        </Text>
      </View>
    );
  };

  const getPlaceholderIcon = (result: SearchResult): string => {
    switch (result.media_type) {
      case 'url': return '🔗';
      case 'text': return '📝';
      case 'document': return '📄';
      case 'image': return '🖼️';
      default: return '📋';
    }
  };

  const getPlaceholderColor = (result: SearchResult): string => {
    const colors = {
      url: '#4A90E2',
      text: '#7ED321', 
      document: '#F5A623',
      image: '#BD10E0',
      default: '#9013FE'
    };
    return colors[result.media_type as keyof typeof colors] || colors.default;
  };

  const SearchResultMessage = ({ result }: { result: SearchResult }) => {
    const styles = getStyles(theme);
    const previewImage = getPreviewImageUrl(result);

    return (
      <View style={[styles.messageBubble, styles.memoraMessageBubble, styles.searchResultBubble]}>
        {previewImage ? (
          <Image 
            source={{ uri: previewImage }} 
            style={styles.searchResultImage}
            onError={() => {
              console.log('Search result image failed to load:', previewImage);
            }}
          />
        ) : (
          <View style={[styles.searchResultPlaceholder, { backgroundColor: getPlaceholderColor(result) + '20' }]}>
            <Text style={[styles.searchResultPlaceholderIcon, { color: getPlaceholderColor(result) }]}>
              {getPlaceholderIcon(result)}
            </Text>
            <Text style={styles.searchResultPlaceholderText} numberOfLines={1}>
              {result.media_type === 'url' ? 'Link' : 
               result.media_type === 'text' ? 'Note' :
               result.media_type === 'document' ? 'Doc' :
               result.media_type === 'image' ? 'Image' : 'Content'}
            </Text>
          </View>
        )}
        <View style={styles.searchResultContent}>
          <Text style={[styles.memoraMessageText, styles.searchResultTitle]}>{result.title || 'Untitled Memory'}</Text>
          {result.media_type === 'text' && ((result as any).content_text || (result as any).content_data) ? (
            <Text style={styles.memoraMessageText} numberOfLines={3}>{(result as any).content_text || (result as any).content_data}</Text>
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
              ) : msg.type === 'welcome' ? (
                <WelcomeMessage />
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
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  flex: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  messagesContent: {
    paddingTop: 16,
    paddingBottom: 16,
  },
  messageWrapper: {
    marginVertical: 4,
  },
  userMessageWrapper: {
    alignItems: 'flex-end',
  },
  memoraMessageWrapper: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    marginVertical: 2,
  },
  userMessageBubble: {
    backgroundColor: theme.colors.primary,
    borderBottomRightRadius: 6,
  },
  memoraMessageBubble: {
    backgroundColor: theme.colors.surface,
    borderBottomLeftRadius: 6,
  },
  userMessageText: {
    color: theme.colors.background,
    fontSize: 16,
    lineHeight: 20,
  },
  memoraMessageText: {
    color: theme.colors.text,
    fontSize: 16,
    lineHeight: 20,
  },
  deleteButton: {
    marginTop: 8,
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: theme.colors.error,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  deleteButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  inputWrapper: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: theme.colors.background,
    borderTopWidth: 1, 
    borderTopColor: theme.colors.border,
  },
  uploadButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  uploadButtonText: {
    fontSize: 24,
    color: theme.colors.text,
    fontWeight: '300',
  },
  textInput: { 
    flex: 1, 
    minHeight: 40,
    maxHeight: 120,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: theme.colors.surface, 
    borderRadius: 20,
    fontSize: 16, 
    color: theme.colors.text, 
    textAlignVertical: 'top',
  },
  sendButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: theme.colors.primary, 
    justifyContent: 'center', 
    alignItems: 'center',
    marginLeft: 12,
  },
  sendButtonText: { 
    fontSize: 20,
    fontWeight: 'bold',
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
  searchResultPlaceholder: {
    width: '100%',
    height: 150,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
  },
  searchResultPlaceholderIcon: {
    fontSize: 40,
    marginBottom: 8,
  },
  searchResultPlaceholderText: {
    fontSize: 14,
    color: theme.colors.textTertiary,
    fontWeight: '600',
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
  },
  welcomeMessage: {
    padding: 16,
  },
  welcomeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginLeft: 12,
  },
}); 