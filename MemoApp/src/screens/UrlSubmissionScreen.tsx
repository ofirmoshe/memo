import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSaveUrl } from '../services/api';
import { getUser } from '../services/user';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { ContentItem } from '../types/api';
import theme from '../config/theme';

const UrlSubmissionScreen = () => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedData, setExtractedData] = useState<ContentItem | null>(null);
  const [showExtractedData, setShowExtractedData] = useState(false);
  const { mutate: saveUrl } = useSaveUrl();
  const navigation = useNavigation();

  const handleSubmit = async () => {
    if (!url.trim()) {
      Alert.alert('Error', 'Please enter a URL');
      return;
    }

    const userId = await getUser();
    if (!userId) {
      Alert.alert('Error', 'Please set a user ID first');
      return;
    }

    // Show loading state
    setIsLoading(true);
    
    try {
      // Show success message immediately
      const submittedUrl = url.trim();
      setUrl('');
      setIsSuccess(true);
      setIsProcessing(true);
      setIsLoading(false);
      
      // Make the actual API call
      saveUrl(
        { user_id: userId, url: submittedUrl },
        {
          onSuccess: (data) => {
            setExtractedData(data);
            setIsProcessing(false);
          },
          onError: () => {
            Alert.alert('Error', 'Failed to process URL');
            setIsProcessing(false);
          }
        }
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to save URL');
      setIsSuccess(false);
      setExtractedData(null);
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    navigation.navigate('Home');
  };

  const handleTagsPress = () => {
    navigation.navigate('Tags');
  };

  const handleViewDetails = () => {
    setShowExtractedData(true);
  };

  const renderExtractedData = () => {
    if (!extractedData) return null;

    return (
      <View style={styles.extractedDataContainer}>
        <Text style={styles.extractedDataTitle}>Extracted Information</Text>
        
        <View style={styles.dataRow}>
          <Text style={styles.dataLabel}>Title:</Text>
          <Text style={styles.dataValue}>{extractedData.title}</Text>
        </View>
        
        {extractedData.description && (
          <View style={styles.dataRow}>
            <Text style={styles.dataLabel}>Description:</Text>
            <Text style={styles.dataValue}>{extractedData.description}</Text>
          </View>
        )}
        
        {extractedData.content_type && (
          <View style={styles.dataRow}>
            <Text style={styles.dataLabel}>Content Type:</Text>
            <Text style={styles.dataValue}>{extractedData.content_type}</Text>
          </View>
        )}
        
        {extractedData.platform && (
          <View style={styles.dataRow}>
            <Text style={styles.dataLabel}>Platform:</Text>
            <Text style={styles.dataValue}>{extractedData.platform}</Text>
          </View>
        )}
        
        {extractedData.tags && extractedData.tags.length > 0 && (
          <View style={styles.dataRow}>
            <Text style={styles.dataLabel}>Tags:</Text>
            <View style={styles.tagsContainer}>
              {extractedData.tags.map((tag, index) => (
                <View key={index} style={styles.tagPill}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'right', 'left', 'bottom']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Icon name="arrow-back" size={28} color={theme.colors.primary} />
        </TouchableOpacity>
        <Text style={styles.title}>Save a URL</Text>
        <TouchableOpacity onPress={handleTagsPress} style={styles.tagsButton}>
          <Icon name="pricetags" size={28} color={theme.colors.primary} />
        </TouchableOpacity>
      </View>
      
      <KeyboardAvoidingView 
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView style={styles.scrollContainer} contentContainerStyle={styles.scrollContent}>
          {!isSuccess ? (
            <View style={styles.formContainer}>
              <TextInput
                style={styles.input}
                placeholder="Enter URL here"
                value={url}
                onChangeText={setUrl}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
              />
              <TouchableOpacity
                style={styles.button}
                onPress={handleSubmit}
                disabled={isLoading}>
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.buttonText}>Save URL</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : showExtractedData ? (
            <View style={styles.formContainer}>
              {renderExtractedData()}
            </View>
          ) : (
            <View style={styles.successContainer}>
              <Icon name="checkmark-circle" size={64} color="#4CD964" />
              <Text style={styles.successText}>URL successfully submitted!</Text>
              
              {isProcessing ? (
                <View style={styles.processingContainer}>
                  <ActivityIndicator color="#007AFF" style={styles.processingIndicator} />
                  <Text style={styles.processingText}>Processing your URL...</Text>
                </View>
              ) : extractedData ? (
                <View style={styles.actionButtonsContainer}>
                  <TouchableOpacity
                    style={[styles.button, styles.viewDetailsButton]}
                    onPress={handleViewDetails}>
                    <Text style={styles.buttonText}>View Details</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
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
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  backButton: {
    padding: theme.spacing.xs,
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
  },
  tagsButton: {
    padding: theme.spacing.xs,
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
  },
  placeholder: {
    width: 44,
  },
  title: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.primary,
    textAlign: 'center',
    flex: 1,
  },
  formContainer: {
    flex: 1,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 24,
    margin: theme.spacing.lg,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 24,
    elevation: 8,
  },
  successContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 24,
    margin: theme.spacing.lg,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 24,
    elevation: 8,
  },
  successText: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.xl,
    textAlign: 'center',
    color: theme.colors.success,
  },
  processingContainer: {
    alignItems: 'center',
    marginTop: theme.spacing.lg,
  },
  processingIndicator: {
    marginBottom: theme.spacing.md,
  },
  processingText: {
    fontSize: theme.font.size.md,
    color: theme.colors.primary,
  },
  actionButtonsContainer: {
    width: '100%',
    maxWidth: 300,
  },
  input: {
    borderWidth: 1.5,
    borderColor: theme.colors.border,
    borderRadius: 14,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.lg,
    fontSize: theme.font.size.md,
    backgroundColor: theme.colors.card,
    color: theme.colors.text,
    fontWeight: '500',
  },
  button: {
    backgroundColor: theme.colors.primary,
    padding: theme.spacing.md,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2,
  },
  buttonText: {
    color: theme.colors.card,
    fontSize: theme.font.size.md,
    fontWeight: 'bold',
  },
  viewDetailsButton: {
    marginTop: theme.spacing.md,
  },
  extractedDataContainer: {
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.background,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: theme.colors.border,
    marginBottom: theme.spacing.lg,
  },
  extractedDataTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    marginBottom: theme.spacing.lg,
    color: theme.colors.primary,
  },
  dataRow: {
    marginBottom: theme.spacing.md,
  },
  dataLabel: {
    fontSize: theme.font.size.sm,
    fontWeight: 'bold',
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  dataValue: {
    fontSize: theme.font.size.md,
    color: theme.colors.text,
    lineHeight: 22,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: theme.spacing.xs,
  },
  tagPill: {
    backgroundColor: theme.colors.tag,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: 16,
    marginRight: theme.spacing.xs,
    marginBottom: theme.spacing.xs,
  },
  tagText: {
    color: theme.colors.tagText,
    fontSize: theme.font.size.xs,
    fontWeight: '500',
  },
});

export default UrlSubmissionScreen; 