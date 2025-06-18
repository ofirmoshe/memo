import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  Platform,
  ScrollView,
  KeyboardAvoidingView,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from '../components/Logo';
import { useGetItems, useGetTags } from '../services/api';
import { getUser } from '../services/user';
import { ContentItem } from '../types/api';
import MemoCard from '../components/MemoCard';
import theme from '../config/theme';

type HomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Home'>;

// Define content types with their icons and colors
const CONTENT_TYPES = [
  { id: 'all', label: 'All', icon: 'grid-outline', color: '#007AFF' },
  { id: 'article', label: 'Articles', icon: 'document-text', color: '#FF9500' },
  { id: 'video', label: 'Videos', icon: 'videocam', color: '#FF3B30' },
  { id: 'audio', label: 'Audio', icon: 'musical-notes', color: '#AF52DE' },
  { id: 'social_media', label: 'Social', icon: 'people', color: '#5856D6' },
  { id: 'image', label: 'Images', icon: 'image', color: '#34C759' },
];

// Icon mapping for common tag categories
const TAG_ICONS: Record<string, string> = {
  technology: 'hardware-chip',
  programming: 'code-slash',
  science: 'flask',
  health: 'fitness',
  business: 'briefcase',
  finance: 'cash',
  education: 'school',
  entertainment: 'film',
  sports: 'basketball',
  travel: 'airplane',
  food: 'restaurant',
  fashion: 'shirt',
  art: 'color-palette',
  design: 'brush',
  politics: 'megaphone',
  news: 'newspaper',
  environment: 'leaf',
  history: 'time',
  philosophy: 'book',
  psychology: 'brain',
  productivity: 'checkbox',
  career: 'briefcase',
  default: 'pricetag',
};

// Tag colors for visual distinction
const TAG_COLORS = [
  '#007AFF', // Blue
  '#FF9500', // Orange
  '#FF3B30', // Red
  '#34C759', // Green
  '#5856D6', // Purple
  '#FF2D55', // Pink
  '#AF52DE', // Violet
  '#FFCC00', // Yellow
];

// Interface for grouped items
interface TagGroup {
  tag: string;
  items: ContentItem[];
  color: string;
  icon: string;
}

const HomeScreen = () => {
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const [userId, setUserId] = useState<string | null>(null);
  const [selectedContentType, setSelectedContentType] = useState<string | null>('all');
  const [refreshing, setRefreshing] = useState(false);
  const [groupedItems, setGroupedItems] = useState<TagGroup[]>([]);
  const windowWidth = Dimensions.get('window').width;
  const insets = useSafeAreaInsets();
  
  // Get user ID on component mount
  useEffect(() => {
    const loadUserId = async () => {
      const id = await getUser();
      setUserId(id);
    };
    
    loadUserId();
  }, []);
  
  // Fetch all items
  const { 
    data: items, 
    isLoading: isLoadingItems, 
    refetch: refetchItems 
  } = useGetItems(
    {
      user_id: userId || 'demo-user',
      content_type: selectedContentType === 'all' ? undefined : selectedContentType || undefined,
    },
    { enabled: !!userId }
  );
  
  // Fetch all tags
  const { 
    data: tags, 
    isLoading: isLoadingTags,
    refetch: refetchTags
  } = useGetTags(
    { user_id: userId || 'demo-user' },
    { enabled: !!userId }
  );
  
  // Group items by tags
  useEffect(() => {
    if (items && tags) {
      // Create a map to store items by tag
      const tagItemsMap: Record<string, ContentItem[]> = {};
      
      // Initialize with empty arrays for all tags
      tags.forEach(tag => {
        tagItemsMap[tag] = [];
      });
      
      // Add items to their respective tags
      items.forEach(item => {
        if (item.tags && item.tags.length > 0) {
          item.tags.forEach(tag => {
            if (tagItemsMap[tag]) {
              tagItemsMap[tag].push(item);
            }
          });
        } else {
          // For items with no tags, create an "untagged" category
          if (!tagItemsMap["untagged"]) {
            tagItemsMap["untagged"] = [];
          }
          tagItemsMap["untagged"].push(item);
        }
      });
      
      // Convert map to array and sort by number of items (descending)
      const groupedArray: TagGroup[] = Object.entries(tagItemsMap)
        .filter(([_, tagItems]) => tagItems.length > 0) // Remove empty tags
        .map(([tag, tagItems]) => ({
          tag,
          items: tagItems,
          color: getTagColor(tag),
          icon: getTagIcon(tag),
        }))
        .sort((a, b) => b.items.length - a.items.length);
      
      setGroupedItems(groupedArray);
    }
  }, [items, tags]);
  
  // Handle refresh
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([refetchItems(), refetchTags()]);
    setRefreshing(false);
  }, [refetchItems, refetchTags]);
  
  // Handle content type selection
  const handleContentTypeSelect = (contentType: string) => {
    setSelectedContentType(contentType);
  };
  
  // Navigate to search screen
  const handleSearchPress = () => {
    navigation.navigate('Search');
  };
  
  // Navigate to URL submission screen
  const handleAddPress = () => {
    navigation.navigate('UrlSubmission');
  };
  
  // Navigate to tags screen
  const handleTagsPress = () => {
    navigation.navigate('Tags');
  };
  
  // Navigate to tag details screen
  const handleTagPress = (tag: string) => {
    navigation.navigate('Tags', { tag });
  };
  
  // Handle item press
  const handleItemPress = (item: ContentItem) => {
    navigation.navigate('ItemDetail', { item });
  };
  
  // Get color for a tag
  const getTagColor = (tag: string): string => {
    // Use hash of tag name to consistently pick a color
    const hash = tag.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return TAG_COLORS[hash % TAG_COLORS.length];
  };
  
  // Get icon for a tag
  const getTagIcon = (tag: string): string => {
    const lowerTag = tag.toLowerCase();
    
    // Check for exact matches
    if (TAG_ICONS[lowerTag]) {
      return TAG_ICONS[lowerTag];
    }
    
    // Check for partial matches
    for (const [key, icon] of Object.entries(TAG_ICONS)) {
      if (lowerTag.includes(key) || key.includes(lowerTag)) {
        return icon;
      }
    }
    
    return TAG_ICONS.default;
  };
  
  // Calculate number of columns based on screen width
  const numColumns = Math.max(2, Math.floor(windowWidth / 180));
  
  // Render content type selector
  const renderContentTypeSelector = () => (
    <View style={styles.contentTypeWrapper}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.contentTypeContainer}>
        {CONTENT_TYPES.map(type => (
          <TouchableOpacity
            key={type.id}
            style={[
              styles.contentTypeButton,
              selectedContentType === type.id && { backgroundColor: type.color + '20' },
            ]}
            onPress={() => handleContentTypeSelect(type.id)}>
            <Icon
              name={type.icon}
              size={20}
              color={selectedContentType === type.id ? type.color : '#8E8E93'}
            />
            <Text
              style={[
                styles.contentTypeText,
                selectedContentType === type.id && { color: type.color },
              ]}>
              {type.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
  
  // Render a tag group
  const renderTagGroup = (tagGroup: TagGroup) => {
    return (
      <View style={styles.tagGroupContainer} key={tagGroup.tag}>
        <TouchableOpacity 
          style={styles.tagHeaderContainer}
          onPress={() => handleTagPress(tagGroup.tag)}
        >
          <View style={[styles.tagIconContainer, { backgroundColor: tagGroup.color }]}>
            <Icon name={tagGroup.icon} size={16} color="#FFFFFF" />
          </View>
          <Text style={styles.tagTitle}>{tagGroup.tag}</Text>
          <Text style={styles.itemCount}>{tagGroup.items.length}</Text>
          <Icon name="chevron-forward" size={16} color="#8E8E93" />
        </TouchableOpacity>
        
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tagItemsContainer}
        >
          {tagGroup.items.slice(0, 5).map((item) => (
            <MemoCard
              key={item.id}
              item={item}
              onPress={() => handleItemPress(item)}
              width={160}
            />
          ))}
          {tagGroup.items.length > 5 && (
            <TouchableOpacity 
              style={[styles.viewMoreButton, { borderColor: tagGroup.color }]}
              onPress={() => handleTagPress(tagGroup.tag)}
            >
              <Text style={[styles.viewMoreText, { color: tagGroup.color }]}>
                View {tagGroup.items.length - 5} more
              </Text>
              <Icon name="arrow-forward" size={16} color={tagGroup.color} />
            </TouchableOpacity>
          )}
        </ScrollView>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'right', 'left', 'bottom']}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Logo size={32} color={theme.colors.primary} />
            <Text style={styles.appName}>Memora</Text>
          </View>
          <View style={styles.headerButtons}>
            <TouchableOpacity style={styles.iconButton} onPress={handleTagsPress}>
              <Icon name="pricetags" size={28} color={theme.colors.primary} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton} onPress={handleSearchPress}>
              <Icon name="search" size={28} color={theme.colors.primary} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton} onPress={handleAddPress}>
              <Icon name="add-circle" size={28} color={theme.colors.accent} />
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Content Type Selector */}
        {renderContentTypeSelector()}
        
        {/* Content Grid */}
        {isLoadingItems || isLoadingTags ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Loading your memories...</Text>
          </View>
        ) : groupedItems.length > 0 ? (
          <FlatList
            data={groupedItems}
            keyExtractor={item => item.tag}
            renderItem={({ item }) => renderTagGroup(item)}
            contentContainerStyle={[
              styles.gridContainer,
              { paddingBottom: insets.bottom }
            ]}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
          />
        ) : (
          <View style={styles.emptyContainer}>
            <Icon name="folder-open-outline" size={64} color="#E5E5EA" />
            <Text style={styles.emptyTitle}>No memories yet</Text>
            <Text style={styles.emptySubtitle}>
              Save your first URL to start building your digital memory
            </Text>
            <TouchableOpacity style={styles.addButton} onPress={handleAddPress}>
              <Icon name="add" size={24} color="#FFFFFF" />
              <Text style={styles.addButtonText}>Add URL</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
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
  headerButtons: {
    flexDirection: 'row',
  },
  iconButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: theme.spacing.sm,
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
  },
  contentTypeWrapper: {
    borderBottomWidth: 0,
    backgroundColor: 'rgba(99,102,241,0.06)',
    paddingBottom: 2,
  },
  contentTypeContainer: {
    flexDirection: 'row',
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
  },
  contentTypeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    marginHorizontal: theme.spacing.xs,
    borderRadius: 18,
    backgroundColor: theme.colors.cardGlass,
    minWidth: 90,
    justifyContent: 'center',
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  contentTypeText: {
    fontSize: theme.font.size.sm,
    fontWeight: '500',
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.sm,
  },
  gridContainer: {
    padding: theme.spacing.md,
  },
  tagGroupContainer: {
    marginBottom: theme.spacing.xl,
  },
  tagHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 16,
    marginBottom: theme.spacing.md,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 2,
  },
  tagIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing.sm,
    backgroundColor: theme.colors.primary,
  },
  tagTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    flex: 1,
  },
  itemCount: {
    fontSize: theme.font.size.sm,
    color: theme.colors.textSecondary,
    marginRight: theme.spacing.sm,
  },
  tagItemsContainer: {
    paddingLeft: theme.spacing.xs,
    paddingRight: theme.spacing.lg,
  },
  viewMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: 120,
    height: 160,
    borderRadius: 16,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    marginHorizontal: theme.spacing.sm,
    backgroundColor: theme.colors.background,
  },
  viewMoreText: {
    fontSize: theme.font.size.sm,
    fontWeight: '500',
    marginRight: theme.spacing.xs,
    color: theme.colors.primary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: theme.spacing.md,
    fontSize: theme.font.size.md,
    color: theme.colors.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  emptyTitle: {
    fontSize: theme.font.size.xl,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  emptySubtitle: {
    fontSize: theme.font.size.md,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderRadius: 24,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2,
  },
  addButtonText: {
    fontSize: theme.font.size.md,
    fontWeight: 'bold',
    color: theme.colors.card,
    marginLeft: theme.spacing.sm,
  },
});

export default HomeScreen; 