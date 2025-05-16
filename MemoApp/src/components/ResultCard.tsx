import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking,
  Image,
  Animated,
  Share,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { ContentItem } from '../types/api';

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
const PLACEHOLDER_IMAGES = {
  article: { color: '#FF9500' },
  video: { color: '#FF3B30' },
  audio: { color: '#AF52DE' },
  social_media: { color: '#5856D6' },
  default: { color: '#007AFF' },
};

type ResultCardProps = {
  item: ContentItem;
  onPress?: (item: ContentItem) => void;
};

const ResultCard = ({ item, onPress }: ResultCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const animatedHeight = useState(new Animated.Value(0))[0];
  
  // Handle opening the URL
  const handleOpenUrl = async () => {
    try {
      const supported = await Linking.canOpenURL(item.url);
      if (supported) {
        await Linking.openURL(item.url);
      } else {
        console.error("Can't open URL: " + item.url);
      }
    } catch (error) {
      console.error(error);
    }
  };

  // Handle sharing the content
  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out this content: ${item.title} - ${item.url}`,
        url: item.url,
      });
    } catch (error) {
      console.error(error);
    }
  };

  // Toggle expanded state with animation
  const toggleExpand = () => {
    const toValue = expanded ? 0 : 1;
    setExpanded(!expanded);
    
    Animated.timing(animatedHeight, {
      toValue,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  // Calculate relevance score indicator (from optional similarity_score)
  const relevanceScore = item.similarity_score ? Math.min(Math.round(item.similarity_score * 100), 100) : null;
  
  // Get appropriate content type icon
  const contentTypeIcon = CONTENT_TYPE_ICONS[item.content_type?.toLowerCase() as keyof typeof CONTENT_TYPE_ICONS] || CONTENT_TYPE_ICONS.default;
  
  // Get appropriate platform icon
  const platformIcon = item.platform 
    ? (PLATFORM_ICONS[item.platform.toLowerCase() as keyof typeof PLATFORM_ICONS] || PLATFORM_ICONS.default)
    : PLATFORM_ICONS.default;
    
  // Get placeholder image based on content type
  const placeholderColor = PLACEHOLDER_IMAGES[item.content_type?.toLowerCase() as keyof typeof PLACEHOLDER_IMAGES]?.color || PLACEHOLDER_IMAGES.default.color;
  
  // Format the date
  const formattedDate = () => {
    if (!item.timestamp) {
      return 'No date';
    }
    
    try {
      return new Date(item.timestamp).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch (e) {
      console.error('Error formatting date:', e);
      return 'Invalid date';
    }
  };

  // Calculate expanded content height based on animation value
  const expandedHeight = animatedHeight.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 120],
  });

  return (
    <Animated.View style={styles.container}>
      <TouchableOpacity 
        style={styles.cardContent}
        onPress={() => onPress?.(item)}
        activeOpacity={0.8}
      >
        <View style={styles.imageContainer}>
          <View style={[styles.imagePlaceholder, { backgroundColor: placeholderColor }]}>
            <Icon name={contentTypeIcon} size={32} color="#FFFFFF" />
          </View>
          <View style={styles.contentTypeIconContainer}>
            <Icon name={contentTypeIcon} size={16} color="#FFFFFF" />
          </View>
        </View>
        
        <View style={styles.infoContainer}>
          <View style={styles.headerContainer}>
            <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
            
            {relevanceScore !== null && (
              <View style={[
                styles.relevanceIndicator, 
                { backgroundColor: relevanceScore > 70 ? '#34C759' : relevanceScore > 40 ? '#FF9500' : '#FF3B30' }
              ]}>
                <Text style={styles.relevanceText}>{relevanceScore}%</Text>
              </View>
            )}
          </View>
          
          <View style={styles.metadataContainer}>
            <Icon name={platformIcon} size={14} color="#8E8E93" />
            <Text style={styles.platformText}>{item.platform || 'web'}</Text>
            <View style={styles.dateDot} />
            <Text style={styles.dateText}>{formattedDate()}</Text>
          </View>
          
          <View style={styles.urlContainer}>
            <Text style={styles.urlText} numberOfLines={1}>{item.url}</Text>
          </View>
          
          <View style={styles.actionBar}>
            <TouchableOpacity style={styles.actionButton} onPress={handleOpenUrl}>
              <Icon name="open-outline" size={16} color="#007AFF" />
              <Text style={styles.actionText}>Open</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
              <Icon name="share-outline" size={16} color="#007AFF" />
              <Text style={styles.actionText}>Share</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton} onPress={toggleExpand}>
              <Icon name={expanded ? "chevron-up" : "chevron-down"} size={16} color="#007AFF" />
              <Text style={styles.actionText}>{expanded ? "Less" : "More"}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
      
      <Animated.View style={[styles.expandedContent, { height: expandedHeight }]}>
        {item.description && (
          <View style={styles.descriptionContainer}>
            <Text style={styles.descriptionTitle}>Description</Text>
            <Text style={styles.descriptionText}>{item.description}</Text>
          </View>
        )}
        
        {item.tags && item.tags.length > 0 && (
          <View style={styles.tagsContainer}>
            <Text style={styles.tagsTitle}>Tags</Text>
            <View style={styles.tagsList}>
              {item.tags.map((tag, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </Animated.View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    marginHorizontal: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardContent: {
    flexDirection: 'row',
    padding: 12,
  },
  imageContainer: {
    width: 80,
    height: 80,
    borderRadius: 8,
    overflow: 'hidden',
    marginRight: 12,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentTypeIconContainer: {
    position: 'absolute',
    top: 4,
    left: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 4,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoContainer: {
    flex: 1,
    justifyContent: 'space-between',
  },
  headerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    flex: 1,
    marginRight: 8,
  },
  relevanceIndicator: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 36,
  },
  relevanceText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  metadataContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  platformText: {
    fontSize: 12,
    color: '#8E8E93',
    marginLeft: 4,
  },
  dateDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#8E8E93',
    marginHorizontal: 6,
  },
  dateText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  urlContainer: {
    marginBottom: 8,
  },
  urlText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  actionBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 4,
  },
  actionText: {
    fontSize: 12,
    color: '#007AFF',
    marginLeft: 4,
  },
  expandedContent: {
    overflow: 'hidden',
    paddingHorizontal: 12,
  },
  descriptionContainer: {
    marginBottom: 8,
  },
  descriptionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  descriptionText: {
    fontSize: 14,
    color: '#3C3C43',
    lineHeight: 20,
  },
  tagsContainer: {
    marginBottom: 12,
  },
  tagsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  tagsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginRight: 6,
    marginBottom: 6,
  },
  tagText: {
    fontSize: 12,
    color: '#3C3C43',
  },
});

export default ResultCard; 