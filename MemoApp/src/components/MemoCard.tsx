import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { ContentItem } from '../types/api';
import { getPreviewImageUrl, getFaviconUrl, getPlaceholderImageUrl } from '../utils/previewUtils';
import { getCachedImage, cacheImage } from '../utils/imageCache';
import theme from '../config/theme';

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

type MemoCardProps = {
  item: ContentItem;
  onPress?: (item: ContentItem) => void;
  width?: number;
};

const MemoCard = ({ item, onPress, width = 160 }: MemoCardProps) => {
  const [previewUrl, setPreviewUrl] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  
  const IMAGE_SIZE = width; // Use width as both width and height for a square image
  
  // Get preview image on component mount
  useEffect(() => {
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
        month: 'short',
        day: 'numeric',
      });
    } catch (e) {
      console.error('Error formatting date:', e);
      return '';
    }
  };
  
  return (
    <TouchableOpacity 
      style={[styles.container, { width }]} 
      onPress={() => onPress?.(item)}
      activeOpacity={0.85}>
      {/* Image Preview */}
      <View style={[styles.imageContainer, { height: IMAGE_SIZE, width: '100%' }]}>
        {loading ? (
          <View style={[styles.imagePlaceholder, { backgroundColor: placeholderColor }]}>
            <ActivityIndicator size="small" color={theme.colors.card} />
          </View>
        ) : imageError || !previewUrl ? (
          <View style={[styles.imagePlaceholder, { backgroundColor: placeholderColor }]}>
            <Icon name={contentTypeIcon} size={32} color={theme.colors.card} />
          </View>
        ) : (
          <Image 
            source={{ uri: previewUrl }} 
            style={styles.image}
            onError={() => setImageError(true)}
          />
        )}
        
        {/* Content Type Badge */}
        <View style={[styles.contentTypeBadge, { backgroundColor: theme.colors.primary + 'E6' }]}>
          <Icon name={contentTypeIcon} size={16} color={theme.colors.card} />
        </View>
      </View>
      
      {/* Content Info */}
      <View style={styles.infoContainer}>
        <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
        
        {/* Platform and Date */}
        <View style={styles.metaContainer}>
          <Icon name={platformIcon} size={14} color={theme.colors.textSecondary} />
          <Text style={styles.metaText}>{item.platform || 'web'}</Text>
          {item.timestamp && (
            <>
              <View style={styles.metaDot} />
              <Text style={styles.metaText}>{formattedDate()}</Text>
            </>
          )}
        </View>
        
        {/* Tags (if present) */}
        {item.tags && item.tags.length > 0 && (
          <View style={styles.tagsContainer}>
            {item.tags.slice(0, 2).map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
            {(item.tags.length) > 2 && (
              <Text style={styles.moreTagsText}>+{(item.tags.length) - 2}</Text>
            )}
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 24,
    elevation: 8,
    borderWidth: 0.5,
    borderColor: theme.colors.border,
  },
  imageContainer: {
    width: '100%',
    height: undefined,
    aspectRatio: 1,
    position: 'relative',
    backgroundColor: theme.colors.background,
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  contentTypeBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius: 4,
    elevation: 3,
  },
  infoContainer: {
    padding: theme.spacing.lg,
  },
  title: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  metaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  metaText: {
    fontSize: theme.font.size.xs,
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.xs,
  },
  metaDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: theme.colors.textSecondary,
    marginHorizontal: theme.spacing.xs,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  tag: {
    backgroundColor: theme.colors.tag,
    borderRadius: 12,
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
  moreTagsText: {
    fontSize: theme.font.size.xs,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
});

export default MemoCard; 