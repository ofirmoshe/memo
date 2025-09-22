import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Image,
  Modal,
  SafeAreaView,
  Linking,
  Animated,
  FlatList,
  TextInput,
  Share,
  Clipboard,

} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { useFocusEffect } from '@react-navigation/native';

import { apiService, UserItem, TagGroup, TagWithCount, API_BASE_URL } from '../services/api';
import { Theme } from '../config/theme';
import { Logo } from '../components/Logo';
import { Svg, Path } from 'react-native-svg';

const { width } = Dimensions.get('window');
const PADDING = 16;
const ITEM_WIDTH = (width - (PADDING * 3)) / 2;

const TrashIcon = ({ color = '#E53935', size = 24 }: { color?: string; size?: number }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <Path d="M3 6h18" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    <Path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    <Path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" stroke={color} strokeWidth="2"/>
    <Path d="M10 11v6M14 11v6" stroke={color} strokeWidth="2" strokeLinecap="round"/>
  </Svg>
);

const ShareIcon = ({ color = '#888', size = 20 }: { color?: string; size?: number }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <Path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <Path d="M12 16V3" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    <Path d="M7 8l5-5 5 5" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </Svg>
);

const CopyIcon = ({ color = '#888', size = 20 }: { color?: string; size?: number }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <Path d="M9 9h11a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V10a1 1 0 0 1 1-1z" stroke={color} strokeWidth="2"/>
    <Path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" stroke={color} strokeWidth="2"/>
  </Svg>
);

const copyToClipboard = async (text: string) => {
  try {
    Clipboard?.setString?.(text);
  } catch {
    // Fallback to share if clipboard not available
    try { await Share.share({ message: text }); } catch {}
  }
};

interface FilterCounts {
  all: number;
  text: number;
  url: number;
  image: number;
  document: number;
}

type FilterType = 'all' | 'text' | 'url' | 'image' | 'document';
type ViewMode = 'categories' | 'all';

export const BrowseScreen: React.FC = () => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const [memories, setMemories] = useState<UserItem[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<UserItem[]>([]);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('categories');
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([]);
  const [tagsWithCounts, setTagsWithCounts] = useState<TagWithCount[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterCounts, setFilterCounts] = useState<FilterCounts>({
    all: 0, text: 0, url: 0, image: 0, document: 0,
  });
  const [selectedMemory, setSelectedMemory] = useState<UserItem | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  // Animation values - moved outside render
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const filterSlideAnim = useRef(new Animated.Value(30)).current;
  const itemAnimations = useRef(new Map<string, { slide: Animated.Value; fade: Animated.Value; press: Animated.Value }>()).current;


  // Simple swipe detection state
  const [startX, setStartX] = useState<number | null>(null);
  const [startY, setStartY] = useState<number | null>(null);

  // Image error tracking to prevent repeated failed loads
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

  // Reset to main browse screen when tab is focused
  useFocusEffect(
    useCallback(() => {
      // Reset to categories view and clear any selected tag
      setViewMode('categories');
      setSelectedTag(null);
    }, [])
  );

  // Simple touch handlers for swipe detection
  const handleTouchStart = (evt: any) => {
    if (viewMode === 'categories' && selectedTag !== null) {
      setStartX(evt.nativeEvent.pageX);
      setStartY(evt.nativeEvent.pageY);
    }
  };

  const handleTouchEnd = (evt: any) => {
    if (viewMode === 'categories' && selectedTag !== null && startX !== null && startY !== null) {
      const endX = evt.nativeEvent.pageX;
      const endY = evt.nativeEvent.pageY;
      const deltaX = endX - startX;
      const deltaY = endY - startY;

      // Check for right swipe
      if (deltaX > 100 && Math.abs(deltaY) < 50) {
        console.log('Right swipe detected!');
        setSelectedTag(null);
      }
    }
    setStartX(null);
    setStartY(null);
  };

  const mapContentType = (mediaType: string): FilterType => {
    switch (mediaType?.toLowerCase()) {
      case 'url': return 'url';
      case 'image': return 'image';
      case 'document': return 'document';
      case 'text':
      default: return 'text';
    }
  };

  const formatTimestamp = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const calculateFilterCounts = (items: UserItem[]): FilterCounts => {
    const counts: FilterCounts = { all: items.length, text: 0, url: 0, image: 0, document: 0 };
    items.forEach(item => {
      const type = mapContentType(item.media_type || '');
      if(counts[type] !== undefined) {
        counts[type]++;
      }
    });
    return counts;
  };

  const generateFallbackTagGroups = (items: UserItem[]): TagGroup[] => {
    const tagGroups: { [key: string]: UserItem[] } = {};
    
    // Group items by tags
    items.forEach(item => {
      if (item.tags && item.tags.length > 0) {
        item.tags.forEach(tag => {
          if (!tagGroups[tag]) {
            tagGroups[tag] = [];
          }
          tagGroups[tag].push(item);
        });
      }
    });
    
    // Convert to TagGroup format and sort by count
    return Object.entries(tagGroups)
      .map(([tag, tagItems]) => ({
        tag,
        count: tagItems.length,
        items: tagItems.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      }))
      .sort((a, b) => b.count - a.count);
  };

  const loadMemories = async () => {
    if (!user) {
      console.warn('❌ loadMemories called without user');
      setIsLoading(false);
      setRefreshing(false);
      return;
    }
    
    console.log('🔄 Starting loadMemories for user:', user.id);
    
    try {
      // Load basic memories first (this should always work)
      console.log('📱 Fetching user items...');
      const items = await apiService.getUserItems(user.id);
      console.log(`✅ Loaded ${items.length} items`);
      
      const sortedItems = items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setMemories(sortedItems);
      
      // Initialize with categories view (default)
      setFilteredMemories(sortedItems);
      setFilterCounts(calculateFilterCounts(sortedItems));
      console.log('✅ Basic memories loaded and set');
      
      // Try to load tag data for tag-based view (optional, new endpoints)
      try {
        const [tagsResponse, groupsResponse] = await Promise.all([
          apiService.getTagsWithCounts(user.id),
          apiService.getTagGroups(user.id)
        ]);
        
        setTagsWithCounts(tagsResponse.tags);
        setTagGroups(groupsResponse.groups);
        console.log('✅ Tag data loaded successfully');
      } catch (tagError) {
        console.warn('⚠️ Tag endpoints not available yet:', tagError);
        // Fallback: generate tag groups from existing data
        const fallbackGroups = generateFallbackTagGroups(sortedItems);
        setTagGroups(fallbackGroups);
        setTagsWithCounts(fallbackGroups.map(group => ({ tag: group.tag, count: group.count })));
      }
    } catch (error) {
      console.error('❌ Error loading memories:', error);
      Alert.alert('Error', 'Failed to load memories. Please try again.');
    } finally {
      console.log('🏁 Finishing loadMemories - setting loading states to false');
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadMemories();
  }, [user]);

  const filterMemories = (filter: FilterType, memoriesToFilter: UserItem[]) => {
    setActiveFilter(filter);
    
    // Animate filter change with bounce effect
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 0.9,
        duration: 150,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();

    // Filter by media type (no "all" option - that's handled by view mode)
    const filtered = memoriesToFilter.filter(memory => mapContentType(memory.media_type || '') === filter);
    setFilteredMemories(filtered);
  };

  const switchViewMode = (mode: ViewMode) => {
    setViewMode(mode);
    setSelectedTag(null);
    
    if (mode === 'all') {
      // Show all memories, potentially filtered by media type
      if (activeFilter !== 'all') {
        filterMemories(activeFilter, memories);
      } else {
        setFilteredMemories(memories);
      }
    }
    // For categories view, we'll use the tagGroups data
  };

  const selectTag = (tag: string) => {
    setSelectedTag(tag);
    const tagGroup = tagGroups.find(group => group.tag === tag);
    if (tagGroup) {
      setFilteredMemories(tagGroup.items);
    }
  };

  const showAllTagItems = () => {
    setSelectedTag(null);
    // When in categories view and showing all categories, show all items chronologically
    if (viewMode === 'categories') {
      setFilteredMemories(memories);
    }
  };

  const handleDeleteMemory = (memory: UserItem) => {
    if (!user) {
      Alert.alert('Error', 'Please sign in to continue');
      return;
    }

    Alert.alert('Delete Memory', `Are you sure you want to delete "${memory.title || 'this memory'}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              if(modalVisible) closeModalDetails();
              await apiService.deleteItem(memory.id, user.id);
              await loadMemories();
            } catch (error) {
              console.error('Error deleting memory:', error);
              Alert.alert('Error', 'Failed to delete memory.');
            }
          },
        },
      ]
    );
  };
  
  const getPreviewImageUrl = (item: UserItem): string | null => {
    // Prefer explicit preview fields
    if (item.preview_thumbnail_path) {
      return `${API_BASE_URL}/file/${item.id}?user_id=${user?.id}`;
    }
    if (item.preview_image_url) {
      return item.preview_image_url;
    }
    // Legacy fallbacks
    if (item.media_type === 'image' && item.file_path) {
      return `${API_BASE_URL}/file/${item.id}?user_id=${user?.id}`;
    }
    if (item.media_type === 'url' && item.content_data?.image) {
      return item.content_data.image;
    }
    // Fallback for youtube links
    if (item.url?.includes('youtube.com') || item.url?.includes('youtu.be')) {
      const videoId = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/.exec(item.url)?.[1];
      if (videoId) return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
    }
    // Fallback for other video platforms
    if (item.url?.includes('vimeo.com')) {
      const vimeoId = item.url.match(/vimeo\.com\/(\d+)/)?.[1];
      if (vimeoId) return `https://vumbnail.com/${vimeoId}.jpg`;
    }
    return null;
  };

  const getPlaceholderIcon = (item: UserItem): string => {
    switch (item.media_type) {
      case 'url': return '🔗';
      case 'text': return '📝';
      case 'document': return '📄';
      case 'image': return '🖼️';
      default: return '📋';
    }
  };

  const getPlaceholderColor = (item: UserItem): string => {
    const colors = {
      url: '#4A90E2',
      text: '#7ED321', 
      document: '#F5A623',
      image: '#BD10E0',
      default: '#9013FE'
    };
    return colors[item.media_type as keyof typeof colors] || colors.default;
  };

  const openMemoryDetails = (memory: UserItem) => {
    setSelectedMemory(memory);
    setModalVisible(true);
  };

  const closeModalDetails = () => {
    setModalVisible(false);
    setSelectedMemory(null);
  };

  useEffect(() => {
    if (user) {
    loadMemories();
    }
    
    // Start entrance animations
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(filterSlideAnim, {
        toValue: 0,
        duration: 800,
        delay: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [user]);

  // Animate items when filtered memories change
  useEffect(() => {
    filteredMemories.forEach((item, index) => {
      if (!itemAnimations.has(item.id)) {
        itemAnimations.set(item.id, {
          slide: new Animated.Value(50),
          fade: new Animated.Value(0),
          press: new Animated.Value(1),
        });
      }
      
      const anim = itemAnimations.get(item.id)!;
      Animated.parallel([
        Animated.timing(anim.slide, {
          toValue: 0,
          duration: 500,
          delay: index * 100,
          useNativeDriver: true,
        }),
        Animated.timing(anim.fade, {
          toValue: 1,
          duration: 500,
          delay: index * 100,
          useNativeDriver: true,
        }),
      ]).start();
    });
  }, [filteredMemories]);

  const styles = getStyles(theme);

  if (!user) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={[styles.emptyStateTitle, { color: theme.colors.text }]}>Please sign in to view your memories</Text>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }
  
  const ViewModeButton = ({ mode, label }: { mode: ViewMode, label: string }) => {
    const isActive = viewMode === mode;
    return (
      <TouchableOpacity
        style={[styles.viewModeButton, { backgroundColor: isActive ? theme.colors.primary : theme.colors.surface }]}
        onPress={() => switchViewMode(mode)}
      >
        <Text style={[styles.viewModeText, { color: isActive ? theme.colors.background : theme.colors.text }]}>
          {label}
        </Text>
      </TouchableOpacity>
    );
  };

  const FilterPill = ({ filterType, label }: { filterType: FilterType, label: string }) => {
    const count = filterCounts[filterType];
    const isActive = activeFilter === filterType;
    if (count === 0) return null;

    return (
      <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
        <TouchableOpacity
          style={[styles.filterPill, { backgroundColor: isActive ? theme.colors.primary : theme.colors.surface }]}
          onPress={() => filterMemories(filterType, memories)}
        >
          <Text style={[styles.filterText, { color: isActive ? theme.colors.background : theme.colors.text }]}>{label}</Text>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  const TagPill = ({ tag, count }: { tag: string, count: number }) => {
    const isActive = selectedTag === tag;
    return (
      <TouchableOpacity
        style={[styles.tagPill, { backgroundColor: isActive ? theme.colors.primary : theme.colors.surface }]}
        onPress={() => selectTag(tag)}
      >
        <Text style={[styles.tagPillText, { color: isActive ? theme.colors.background : theme.colors.text }]}>
          {tag} ({count})
        </Text>
      </TouchableOpacity>
    );
  };

  const renderTagGroup = ({ item: tagGroup }: { item: TagGroup }) => {
    const previewItems = tagGroup.items.slice(0, 4);
    
    // Fill empty slots with placeholders if less than 4 items
    const filledItems = [...previewItems];
    while (filledItems.length < 4) {
      filledItems.push(previewItems[0] || null);
    }

    // Get or create animation values for this category
    if (!itemAnimations.has(tagGroup.tag)) {
      itemAnimations.set(tagGroup.tag, {
        slide: new Animated.Value(0),
        fade: new Animated.Value(1),
        press: new Animated.Value(1),
      });
    }
    
    const anim = itemAnimations.get(tagGroup.tag)!;

    const handlePressIn = () => {
      Animated.spring(anim.press, {
        toValue: 0.92,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }).start();
    };

    const handlePressOut = () => {
      Animated.spring(anim.press, {
        toValue: 1,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }).start();
    };
    
    return (
      <View style={styles.categoryContainer}>
        <Animated.View style={{
          transform: [{ scale: anim.press }]
        }}>
          <TouchableOpacity
            style={styles.categoryCard}
            onPress={() => selectTag(tagGroup.tag)}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            activeOpacity={1}
          >
            {/* Thumbnail Grid - 2x2 layout like iPhone folders */}
            <View style={styles.categoryThumbnails}>
              {filledItems.map((item, index) => {
                if (!item) return <View key={index} style={styles.categoryThumbnailEmpty} />;
                
                const previewImage = getPreviewImageUrl(item);
                const thumbnailSize = (ITEM_WIDTH - 30) / 2;
                const gap = 1; // Minimal gap for corner alignment
                const positions = [
                  { top: 0, left: 0 },                           // Top-left
                  { top: 0, left: thumbnailSize + gap },         // Top-right  
                  { top: thumbnailSize + gap, left: 0 },         // Bottom-left
                  { top: thumbnailSize + gap, left: thumbnailSize + gap }  // Bottom-right
                ];
                
                return (
                  <View key={`${item.id}-${index}`} style={[styles.categoryThumbnail, positions[index]]}>
                    {previewImage && !failedImages.has(previewImage) ? (
                      <Image 
                        source={{ uri: previewImage, cache: 'force-cache' }} 
                        style={styles.categoryThumbnailImage} 
                        resizeMode="cover"
                        fadeDuration={200}
                        onError={(error) => {
                          console.log('Category thumbnail failed to load:', previewImage, error);
                          setFailedImages(prev => new Set(prev).add(previewImage));
                        }}
                      />
                    ) : (
                      <View style={[styles.categoryThumbnailPlaceholder, { backgroundColor: getPlaceholderColor(item) }]}>
                        <Text style={styles.categoryThumbnailIcon}>
                          {getPlaceholderIcon(item)}
                        </Text>
                      </View>
                    )}
                  </View>
                );
              })}
            </View>
          </TouchableOpacity>
        </Animated.View>
        
        {/* Category Info - Outside the card like iPhone */}
        <View style={styles.categoryInfo}>
          <Text style={styles.categoryTitle} numberOfLines={1}>
            {tagGroup.tag.charAt(0).toUpperCase() + tagGroup.tag.slice(1)}
          </Text>
          <Text style={styles.categoryCount}>
            {tagGroup.count}
          </Text>
        </View>
      </View>
    );
  };

  const renderItem = ({ item, index }: { item: UserItem, index: number }) => {
    const previewImage = getPreviewImageUrl(item);
    
    // Get or create animation values for this item
    if (!itemAnimations.has(item.id)) {
      itemAnimations.set(item.id, {
        slide: new Animated.Value(50),
        fade: new Animated.Value(0),
        press: new Animated.Value(1),
      });
    }
    
    const anim = itemAnimations.get(item.id)!;

    const handlePressIn = () => {
      Animated.spring(anim.press, {
        toValue: 0.95,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }).start();
    };

    const handlePressOut = () => {
      Animated.spring(anim.press, {
        toValue: 1,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }).start();
    };

    return (
      <Animated.View style={{ 
        transform: [{ translateY: anim.slide }, { scale: anim.press }],
        opacity: anim.fade,
      }}>
        <TouchableOpacity 
          style={styles.itemContainer} 
          onPress={() => openMemoryDetails(item)} 
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          activeOpacity={0.8}
        >
          {previewImage && !failedImages.has(previewImage) ? (
            <Image 
              source={{ uri: previewImage, cache: 'force-cache' }} 
              style={styles.itemImage} 
              resizeMode="cover"
              fadeDuration={200}
              onError={(error) => {
                // Handle image load error by showing placeholder
                console.log('Main item image failed to load:', previewImage, error);
                setFailedImages(prev => new Set(prev).add(previewImage));
              }}
            />
          ) : (
            <View style={[styles.placeholderContainer, { backgroundColor: getPlaceholderColor(item) + '20' }]}>
              <Text style={[styles.placeholderIcon, { color: getPlaceholderColor(item) }]}>
                {getPlaceholderIcon(item)}
              </Text>
              <Text style={styles.placeholderText} numberOfLines={2}>
                {item.media_type === 'url' ? 'Web Link' : 
                 item.media_type === 'text' ? 'Text Note' :
                 item.media_type === 'document' ? 'Document' :
                 item.media_type === 'image' ? 'Image' : 'Content'}
              </Text>
            </View>
          )}
          <View style={styles.cardContentContainer}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle} numberOfLines={2}>
                {item.title || 'Untitled Memory'}
              </Text>
              <Text style={styles.cardDescription} numberOfLines={2}>
                {item.description || 'No description available'}
              </Text>
            </View>
            <View style={styles.cardFooter}>
              <View style={styles.tagsContainer}>
                {item.tags && item.tags.length > 0 && (
                  <View style={styles.tag}>
                    <Text style={styles.tagText} numberOfLines={1} ellipsizeMode="tail">{item.tags[0]}</Text>
                  </View>
                )}
                {item.tags && item.tags.length > 1 && <Text style={styles.moreTagsText} numberOfLines={1}>+{item.tags.length - 1}</Text>}
              </View>
              <Text style={styles.timestamp} numberOfLines={1}>{formatTimestamp(item.timestamp)}</Text>
            </View>
          </View>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <Animated.View style={[styles.header, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
        <View style={styles.headerContent}>
          {viewMode === 'categories' && selectedTag !== null ? (
            // Category-specific header
            <>
              <TouchableOpacity 
                style={styles.headerBackButton}
                onPress={() => setSelectedTag(null)}
              >
                <Text style={styles.headerBackText}>←</Text>
              </TouchableOpacity>
              <Text style={styles.headerTitle}>
                {selectedTag.charAt(0).toUpperCase() + selectedTag.slice(1)}
              </Text>
              <View style={styles.headerBackButton} />
            </>
          ) : (
            // Default header
            <>
              <Logo size={42} color={theme.colors.primary} />
              <Text style={styles.headerTitle}>Browse</Text>
            </>
          )}
        </View>
      </Animated.View>
      
      {/* Content wrapper */}
      <View style={{ flex: 1 }}>
              {/* View Mode Switcher - Hide when viewing specific category */}
        {!(viewMode === 'categories' && selectedTag !== null) && (
          <Animated.View style={[styles.viewModeContainer, { transform: [{ translateY: filterSlideAnim }] }]}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.viewModeContent}>
              <ViewModeButton mode="categories" label="Categories" />
              <ViewModeButton mode="all" label="All" />
            </ScrollView>
          </Animated.View>
        )}

        {/* Filters based on current view mode */}
        {viewMode === 'all' && (
          <Animated.View style={[styles.filterContainer, { transform: [{ translateY: filterSlideAnim }] }]}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterContent}>
              <FilterPill filterType="url" label="Links" />
              <FilterPill filterType="text" label="Notes" />
              <FilterPill filterType="image" label="Images" />
              <FilterPill filterType="document" label="Documents" />
            </ScrollView>
          </Animated.View>
        )}

        

        {viewMode === 'categories' && selectedTag === null ? (
          // Show category cards in 2x2 grid
          <FlatList
            key="categoryGrid"
            data={tagGroups}
            renderItem={renderTagGroup}
            keyExtractor={(item) => item.tag}
            numColumns={2}
            columnWrapperStyle={styles.row}
            contentContainerStyle={styles.memoriesContent}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
            removeClippedSubviews={true}
            maxToRenderPerBatch={6}
            windowSize={5}
            initialNumToRender={4}
          />
        ) : filteredMemories.length > 0 ? (
        // Show items grid view - two columns
        <View 
          style={{ flex: 1 }} 
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
                      <FlatList
              key="itemsGrid"
              data={filteredMemories}
              renderItem={renderItem}
              keyExtractor={(item) => item.id}
              numColumns={2}
              columnWrapperStyle={styles.row}
              contentContainerStyle={styles.memoriesContent}
              showsVerticalScrollIndicator={false}
              refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
              scrollEventThrottle={16}
              removeClippedSubviews={true}
              maxToRenderPerBatch={6}
              windowSize={5}
              initialNumToRender={4}
            />
        </View>
      ) : (
        <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
          <Text style={styles.emptyStateTitle}>
            No {viewMode === 'all' && activeFilter !== 'all' ? activeFilter : 
                viewMode === 'categories' && selectedTag ? `"${selectedTag}"` : ''} memories found
          </Text>
          <Text style={styles.emptyStateSubtitle}>Try adding some in the Chat tab!</Text>
        </Animated.View>
      )}
      </View>

      <Modal visible={modalVisible} animationType="slide" presentationStyle="pageSheet" onRequestClose={closeModalDetails}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              accessibilityLabel="Delete memory"
              onPress={() => selectedMemory && handleDeleteMemory(selectedMemory)}
              style={styles.modalDeleteIconButton}
            >
              <TrashIcon color={theme.colors.error} size={22} />
            </TouchableOpacity>
            <TouchableOpacity onPress={closeModalDetails} style={styles.modalCloseButton}>
              <Text style={styles.modalCloseText}>Done</Text>
            </TouchableOpacity>
          </View>
          {selectedMemory && (
            <ScrollView style={styles.modalContent}>
              <Text style={styles.modalTitle}>{selectedMemory.title || 'Untitled'}</Text>
              <Text style={styles.modalTimestamp}>{formatTimestamp(selectedMemory.timestamp)}</Text>
              
              {selectedMemory.preview_image_url && (
                <TouchableOpacity
                  onPress={() => {
                    if (selectedMemory.url) {
                      Linking.openURL(selectedMemory.url);
                    }
                  }}
                  activeOpacity={0.8}
                  disabled={!selectedMemory.url}
                >
                  <Image
                    source={{ uri: selectedMemory.preview_image_url, cache: 'force-cache' }}
                    style={styles.modalImage}
                    resizeMode="cover"
                    fadeDuration={150}
                    onError={(error) => {
                      console.log('Modal image failed to load:', selectedMemory.preview_image_url, error);
                    }}
                  />
                </TouchableOpacity>
              )}
              
              <Text style={styles.modalDescription}>{selectedMemory.description}</Text>
              
              {selectedMemory.url && (
                <View style={styles.linkRow}>
                  <TouchableOpacity
                    style={styles.linkInput}
                    onPress={() => Linking.openURL(selectedMemory.url!)}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.linkInputText} numberOfLines={1} ellipsizeMode="tail">
                      {selectedMemory.url}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={async () => { await copyToClipboard(selectedMemory.url!); }}
                    style={styles.iconButton}
                    accessibilityLabel="Copy link"
                  >
                    <CopyIcon color={theme.colors.text} size={18} />
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={async () => {
                      try { await Share.share({ message: selectedMemory.url! }); } catch {}
                    }}
                    style={styles.iconButton}
                    accessibilityLabel="Share link"
                  >
                    <ShareIcon color={theme.colors.text} size={18} />
                  </TouchableOpacity>
                </View>
              )}
              
              {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                <View style={styles.modalTagsContainer}>
                  <Text style={styles.modalTagsTitle}>Tags:</Text>
                  <View style={styles.modalTags}>
                    {selectedMemory.tags.map((tag, index) => (
                      <View key={index} style={styles.modalTag}>
                        <Text style={styles.modalTagText}>{tag}</Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginLeft: 16,
    flex: 1,
    textAlign: 'center',
  },
  headerBackButton: {
    width: 58, // Same as logo + margin for balance
    height: 42,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerBackText: {
    fontSize: 24,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  viewModeContainer: {
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  viewModeContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  viewModeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  viewModeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  filterContainer: {
    paddingVertical: 8,
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
  },
  tagPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  tagPillText: {
    fontSize: 12,
    fontWeight: '600',
  },
  memoriesContent: {
    paddingHorizontal: PADDING,
    paddingTop: 12,
    paddingBottom: 20,
  },
  row: {
    justifyContent: 'space-between',
  },
  itemContainer: {
    width: ITEM_WIDTH,
    height: 240, // Fixed height for consistent grid
    marginBottom: PADDING,
    backgroundColor: theme.colors.card,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemImage: {
    width: '100%',
    height: 120,
    backgroundColor: theme.colors.surface,
  },
  placeholderContainer: {
    width: '100%',
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
  },
  placeholderIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 12,
    color: theme.colors.textTertiary,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  cardContentContainer: { padding: 12, flex: 1, justifyContent: 'space-between' },
  cardHeader: { marginBottom: 4 },
  cardTitle: { fontSize: 14, fontWeight: '600', color: theme.colors.text, marginBottom: 4 },
  cardDescription: { fontSize: 12, color: theme.colors.textSecondary, marginBottom: 0, lineHeight: 16 },
  cardFooter: { marginTop: 'auto', paddingTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  tagsContainer: { flexDirection: 'row', flexWrap: 'nowrap', alignItems: 'center', overflow: 'hidden', flexShrink: 1, maxWidth: '75%' },
  tag: { backgroundColor: theme.colors.surface, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6, marginRight: 6 },
  tagText: { fontSize: 10, fontWeight: '600', color: theme.colors.textTertiary, maxWidth: 60, flexShrink: 1 },
  moreTagsText: { fontSize: 10, fontWeight: '600', color: theme.colors.textTertiary },
  timestamp: { fontSize: 10, color: theme.colors.textTertiary, opacity: 0.8, flexShrink: 0, marginLeft: 8 },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyStateSubtitle: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  modalDeleteIconButton: {
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  modalCloseButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.primary,
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 8,
  },
  modalTimestamp: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: 16,
  },
  modalImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    marginBottom: 16,
    backgroundColor: theme.colors.surface,
  },
  modalDescription: {
    fontSize: 16,
    color: theme.colors.text,
    lineHeight: 24,
    marginBottom: 16,
  },
  modalUrl: {
    fontSize: 14,
    color: theme.colors.primary,
    textDecorationLine: 'underline',
    marginBottom: 16,
  },
  linkRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  linkInput: { flex: 1, borderWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface, color: theme.colors.text, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 8 },
  linkInputText: {
    fontSize: 14,
    color: theme.colors.text,
  },
  iconButton: { paddingHorizontal: 10, paddingVertical: 8, backgroundColor: theme.colors.surface, borderRadius: 8, borderWidth: 1, borderColor: theme.colors.border },
  modalTagsContainer: {
    marginBottom: 24,
  },
  modalTagsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
  },
  modalTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  modalTag: {
    backgroundColor: theme.colors.surface,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  modalTagText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  tagGroupContainer: {
    backgroundColor: theme.colors.card,
    marginHorizontal: PADDING,
    marginBottom: 12,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tagGroupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tagGroupTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  tagGroupCount: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  tagGroupPreview: {
    flexDirection: 'column',
    gap: 4,
  },
  tagGroupPreviewItem: {
    paddingVertical: 4,
  },
  tagGroupPreviewText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  // iPhone-style category cards
  categoryContainer: {
    width: ITEM_WIDTH,
    alignItems: 'center',
    marginBottom: PADDING,
    marginTop: 4,
  },
  categoryCard: {
    width: ITEM_WIDTH,
    height: ITEM_WIDTH, // Square like iPhone folders
    // Glassmorphism effect with backdrop blur simulation
    backgroundColor: theme.colors.background === '#000000' || theme.colors.background === '#1C1C1E'
      ? 'rgba(255, 255, 255, 0.08)' // Dark mode - ultra subtle white overlay
      : 'rgba(255, 255, 255, 0.3)', // Light mode - light subtle white overlay
    borderRadius: 28,
    padding: 14,
    // Multi-layered border for depth
    borderWidth: 1,
    borderColor: theme.colors.background === '#000000' || theme.colors.background === '#1C1C1E'
      ? 'rgba(255, 255, 255, 0.12)' // Dark mode - subtle light border
      : 'rgba(255, 255, 255, 0.6)', // Light mode - light white border
    // Premium shadow with multiple layers
    shadowColor: theme.colors.background === '#000000' || theme.colors.background === '#1C1C1E' ? '#000' : '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: theme.colors.background === '#000000' || theme.colors.background === '#1C1C1E' ? 0.6 : 0.2,
    shadowRadius: 20,
    elevation: 8,
    alignItems: 'center',
    justifyContent: 'center',
    // Additional styling for premium feel
    overflow: 'hidden', // Ensures clean edges
  },
  categoryThumbnails: {
    width: ITEM_WIDTH - 28, // Even larger container
    height: ITEM_WIDTH - 28,
    position: 'relative',
    borderRadius: 16,
    overflow: 'visible', // Allow shadows to show
    backgroundColor: 'transparent',
  },
  categoryThumbnail: {
    position: 'absolute',
    width: (ITEM_WIDTH - 30) / 2, // Much bigger thumbnails
    height: (ITEM_WIDTH - 30) / 2,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 0,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 4,
  },
  categoryThumbnailEmpty: {
    position: 'absolute',
    width: (ITEM_WIDTH - 30) / 2,
    height: (ITEM_WIDTH - 30) / 2,
    borderRadius: 16,
    backgroundColor: theme.colors.background === '#000000' || theme.colors.background === '#1C1C1E'
      ? 'rgba(255, 255, 255, 0.06)' // Dark mode
      : 'rgba(0, 0, 0, 0.04)', // Light mode
    borderWidth: 0,
  },
  categoryThumbnailImage: {
    width: '100%',
    height: '100%',
  },
  categoryThumbnailPlaceholder: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
  },
  categoryThumbnailIcon: {
    fontSize: 24,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  categoryInfo: {
    alignItems: 'center',
    width: '100%',
    marginTop: 8,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  categoryTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.text,
    textAlign: 'center',
    letterSpacing: -0.2,
    marginRight: 6,
  },
    categoryCount: {
    fontSize: 13,
    fontWeight: '500',
    color: theme.colors.textSecondary,
    opacity: 0.8,
  },

  });  