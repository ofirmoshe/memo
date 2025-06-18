import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Linking,
  ActivityIndicator,
  Share,
  Platform,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import Icon from 'react-native-vector-icons/Ionicons';
import { getPreviewImageUrl, getFaviconUrl, getPlaceholderImageUrl } from '../utils/previewUtils';
import { getCachedImage, cacheImage } from '../utils/imageCache';
import theme from '../config/theme';

type ItemDetailScreenRouteProp = RouteProp<RootStackParamList, 'ItemDetail'>;
type ItemDetailScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'ItemDetail'>;

// Content type icon mappings
const CONTENT_TYPE_ICONS = {
  article: 'document-text',
  video: 'videocam',
  audio: 'musical-notes',
  social_media: 'people',
  image: 'image',
  web: 'globe',
  pdf: 'document',
  default: 'document-outline',
};

// Platform icon mappings
const PLATFORM_ICONS = {
  youtube: 'logo-youtube',
  twitter: 'logo-twitter',
  instagram: 'logo-instagram',
  facebook: 'logo-facebook',
  linkedin: 'logo-linkedin',
  spotify: 'musical-note',
  tiktok: 'musical-notes',
  medium: 'logo-medium',
  reddit: 'logo-reddit',
  web: 'globe',
  default: 'globe-outline',
};

// Image placeholder based on content type
const PLACEHOLDER_COLORS = {
  article: '#FF9500',
  video: '#FF3B30',
  audio: '#AF52DE',
  social_media: '#5856D6',
  image: '#34C759',
  web: '#007AFF',
  pdf: '#FF2D55',
  default: '#8E8E93',
};

const ItemDetailScreen = () => {
  const navigation = useNavigation<ItemDetailScreenNavigationProp>();
  const route = useRoute<ItemDetailScreenRouteProp>();
  const { item } = route.params;
  const insets = useSafeAreaInsets();
  
  const [previewUrl, setPreviewUrl] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  
  // Load preview image
  React.useEffect(() => {
    const loadPreviewImage = async () => {
      try {
        setLoading(true);
        setImageError(false);
        
        // Check if we have this image URL in cache
        const cachedUrl = getCachedImage(item.url);
        if (cachedUrl) {
          setPreviewUrl(cachedUrl);
          setLoading(false);
          return;
        }
        
        // Try to get a content-specific preview
        let url = getPreviewImageUrl(item.url, item.content_type);
        
        // If that fails, try to get a favicon as a fallback
        if (!url) {
          url = getFaviconUrl(item.url);
        }
        
        // If all else fails, generate a placeholder based on title
        if (!url) {
          url = getPlaceholderImageUrl(item.title, item.content_type);
        }
        
        // Store in cache for future use
        if (url) {
          cacheImage(item.url, url);
        }
        
        setPreviewUrl(url);
      } catch (error) {
        console.error('Error loading preview image:', error);
        setImageError(true);
      } finally {
        setLoading(false);
      }
    };
    
    loadPreviewImage();
  }, [item.url, item.content_type, item.title]);
  
  // Get appropriate content type icon
  const contentTypeIcon = CONTENT_TYPE_ICONS[item.content_type?.toLowerCase() as keyof typeof CONTENT_TYPE_ICONS] || CONTENT_TYPE_ICONS.default;
  
  // Get appropriate platform icon
  const platformIcon = item.platform 
    ? (PLATFORM_ICONS[item.platform.toLowerCase() as keyof typeof PLATFORM_ICONS] || PLATFORM_ICONS.default)
    : PLATFORM_ICONS.default;
    
  // Get placeholder color based on content type
  const placeholderColor = PLACEHOLDER_COLORS[item.content_type?.toLowerCase() as keyof typeof PLACEHOLDER_COLORS] || PLACEHOLDER_COLORS.default;
  
  // Format the date
  const formattedDate = () => {
    if (!item.timestamp) {
      return '';
    }
    
    try {
      return new Date(item.timestamp).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch (e) {
      console.error('Error formatting date:', e);
      return '';
    }
  };
  
  // Handle back button press
  const handleBackPress = () => {
    navigation.goBack();
  };
  
  // Handle opening the URL
  const handleOpenUrl = async () => {
    try {
      const supported = await Linking.canOpenURL(item.url);
      
      if (supported) {
        await Linking.openURL(item.url);
      } else {
        console.error("Don't know how to open URL:", item.url);
      }
    } catch (error) {
      console.error('Error opening URL:', error);
    }
  };
  
  // Handle sharing the content
  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out this ${item.content_type || 'content'}: ${item.title}\n${item.url}`,
        url: item.url,
        title: item.title,
      });
    } catch (error) {
      console.error('Error sharing content:', error);
    }
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['top', 'right', 'left', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBackPress}>
          <Icon name="chevron-back" size={28} color={theme.colors.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {item.content_type ? item.content_type.charAt(0).toUpperCase() + item.content_type.slice(1) : 'Content'}
        </Text>
        <View style={styles.headerRight}>
          <TouchableOpacity style={styles.headerButton} onPress={handleShare}>
            <Icon name="share-outline" size={24} color={theme.colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={handleOpenUrl}>
            <Icon name="open-outline" size={24} color={theme.colors.accent} />
          </TouchableOpacity>
        </View>
      </View>
      
      <View style={styles.contentContainer}>
        <ScrollView style={styles.scrollView}>
          {/* Preview Image */}
          <View style={styles.imageContainer}>
            {loading ? (
              <View style={[styles.imagePlaceholder, { backgroundColor: placeholderColor }]}>
                <ActivityIndicator size="large" color="#FFFFFF" />
              </View>
            ) : imageError || !previewUrl ? (
              <View style={[styles.imagePlaceholder, { backgroundColor: placeholderColor }]}>
                <Icon name={contentTypeIcon} size={64} color="#FFFFFF" />
              </View>
            ) : (
              <Image 
                source={{ uri: previewUrl }} 
                style={styles.image}
                resizeMode="cover"
                onError={() => setImageError(true)}
              />
            )}
            
            {/* Content Type Badge */}
            <View style={[styles.contentTypeBadge, { backgroundColor: placeholderColor + 'E6' }]}>
              <Icon name={contentTypeIcon} size={20} color="#FFFFFF" />
              <Text style={styles.contentTypeText}>
                {item.content_type || 'Content'}
              </Text>
            </View>
          </View>
          
          {/* Content Info */}
          <View style={styles.infoContainer}>
            <Text style={styles.title}>{item.title}</Text>
            
            {/* Platform and Date */}
            <View style={styles.metaContainer}>
              <Icon name={platformIcon} size={16} color="#8E8E93" />
              <Text style={styles.metaText}>{item.platform || 'web'}</Text>
              {item.timestamp && (
                <>
                  <View style={styles.metaDot} />
                  <Text style={styles.metaText}>{formattedDate()}</Text>
                </>
              )}
            </View>
            
            {/* Description */}
            {item.description && (
              <View style={styles.descriptionContainer}>
                <Text style={styles.sectionTitle}>Description</Text>
                <Text style={styles.description}>{item.description}</Text>
              </View>
            )}
            
            {/* Tags */}
            {item.tags && item.tags.length > 0 && (
              <View style={styles.tagsSection}>
                <Text style={styles.sectionTitle}>Tags</Text>
                <View style={styles.tagsContainer}>
                  {item.tags.map((tag, index) => (
                    <View key={index} style={styles.tag}>
                      <Text style={styles.tagText}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            {/* URL */}
            <View style={styles.urlSection}>
              <Text style={styles.sectionTitle}>Source</Text>
              <TouchableOpacity onPress={handleOpenUrl}>
                <Text style={styles.url} numberOfLines={2}>{item.url}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
        
        {/* Bottom Action Bar */}
        <View style={styles.actionBar}>
          <TouchableOpacity style={styles.actionButton} onPress={handleOpenUrl}>
            <Icon name="open-outline" size={20} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Open</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
            <Icon name="share-social-outline" size={20} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Share</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  contentContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
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
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
  },
  headerTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.primary,
    flex: 1,
    textAlign: 'center',
  },
  headerRight: {
    flexDirection: 'row',
  },
  headerButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22,
    backgroundColor: 'rgba(244,114,182,0.10)',
    marginLeft: theme.spacing.sm,
  },
  scrollView: {
    flex: 1,
  },
  imageContainer: {
    width: '100%',
    height: 250,
    position: 'relative',
    backgroundColor: theme.colors.cardGlass,
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 24,
    elevation: 8,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
  },
  contentTypeBadge: {
    position: 'absolute',
    bottom: 24,
    left: 24,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 18,
    backgroundColor: theme.colors.primary + 'E6',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius: 4,
    elevation: 3,
  },
  contentTypeText: {
    color: theme.colors.card,
    fontSize: theme.font.size.sm,
    fontWeight: 'bold',
    marginLeft: theme.spacing.sm,
    textTransform: 'capitalize',
  },
  infoContainer: {
    padding: theme.spacing.lg,
  },
  title: {
    fontSize: theme.font.size.xl,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  metaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  metaText: {
    fontSize: theme.font.size.sm,
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.xs,
  },
  metaDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.colors.textSecondary,
    marginHorizontal: theme.spacing.sm,
  },
  descriptionContainer: {
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  description: {
    fontSize: theme.font.size.md,
    lineHeight: 24,
    color: theme.colors.text,
  },
  tagsSection: {
    marginBottom: theme.spacing.md,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    backgroundColor: theme.colors.tag,
    borderRadius: 14,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    marginRight: theme.spacing.xs,
    marginBottom: theme.spacing.xs,
  },
  tagText: {
    fontSize: theme.font.size.xs,
    color: theme.colors.tagText,
    fontWeight: '500',
  },
  urlSection: {
    marginBottom: theme.spacing.md,
  },
  url: {
    fontSize: theme.font.size.sm,
    color: theme.colors.accent,
    textDecorationLine: 'underline',
    fontWeight: '500',
  },
  actionBar: {
    flexDirection: 'row',
    backgroundColor: theme.colors.cardGlass,
    borderTopWidth: 0,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 4,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: 18,
    marginHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2,
  },
  actionButtonText: {
    color: theme.colors.card,
    fontSize: theme.font.size.sm,
    fontWeight: 'bold',
    marginLeft: theme.spacing.xs,
    letterSpacing: 0.5,
  },
});

export default ItemDetailScreen; 