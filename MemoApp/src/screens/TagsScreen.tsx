import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  ScrollView,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from '../components/Logo';
import { useGetTags, useGetItemsByTag } from '../services/api';
import { getUser } from '../services/user';
import MemoCard from '../components/MemoCard';
import { ContentItem } from '../types/api';
import theme from '../config/theme';

type TagsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Tags'>;
type TagsScreenRouteProp = RouteProp<RootStackParamList, 'Tags'>;

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

const TagsScreen = () => {
  const navigation = useNavigation<TagsScreenNavigationProp>();
  const route = useRoute<TagsScreenRouteProp>();
  const initialTag = route.params?.tag;
  
  const [userId, setUserId] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(initialTag || null);
  const windowWidth = Dimensions.get('window').width;
  
  // Get user ID on component mount
  useEffect(() => {
    const loadUserId = async () => {
      const id = await getUser();
      setUserId(id);
    };
    
    loadUserId();
  }, []);
  
  // Update selected tag when route params change
  useEffect(() => {
    if (route.params?.tag) {
      setSelectedTag(route.params.tag);
    }
  }, [route.params]);
  
  // Fetch all tags
  const { data: tags, isLoading: isLoadingTags } = useGetTags(
    { user_id: userId || 'demo-user' },
    { enabled: !!userId }
  );
  
  // Fetch items for selected tag
  const { data: tagItems, isLoading: isLoadingItems } = useGetItemsByTag(
    {
      user_id: userId || 'demo-user',
      tag: selectedTag || '',
    },
    { enabled: !!userId && !!selectedTag }
  );
  
  // Handle tag selection
  const handleTagSelect = (tag: string) => {
    setSelectedTag(tag);
  };
  
  // Navigate to home screen
  const handleHomePress = () => {
    navigation.navigate('Home');
  };
  
  // Navigate to search screen
  const handleSearchPress = () => {
    navigation.navigate('Search');
  };
  
  // Navigate to URL submission screen
  const handleAddPress = () => {
    navigation.navigate('UrlSubmission');
  };
  
  // Handle item press
  const handleItemPress = (item: ContentItem) => {
    navigation.navigate('ItemDetail', { item });
  };
  
  // Calculate number of columns based on screen width
  const numColumns = Math.max(2, Math.floor(windowWidth / 180));
  
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
  
  return (
    <SafeAreaView style={styles.container} edges={['top', 'right', 'left', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconButton} onPress={handleHomePress}>
          <Icon name="home" size={28} color={theme.colors.primary} />
        </TouchableOpacity>
        <View style={styles.logoContainer}>
          <Logo size={32} color={theme.colors.primary} />
          <Text style={styles.appName}>Memora</Text>
        </View>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.iconButton} onPress={handleSearchPress}>
            <Icon name="search" size={28} color={theme.colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconButton} onPress={handleAddPress}>
            <Icon name="add-circle" size={32} color={theme.colors.accent} />
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Tags List */}
      <View style={styles.tagsContainer}>
        <Text style={styles.sectionTitle}>Browse by Tags</Text>
        {isLoadingTags ? (
          <ActivityIndicator size="small" color="#007AFF" style={styles.loader} />
        ) : tags && tags.length > 0 ? (
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tagsList}
          >
            {tags.map((tag) => (
              <TouchableOpacity
                key={tag}
                style={[
                  styles.tagButton,
                  { backgroundColor: getTagColor(tag) + '20' },
                  selectedTag === tag && { backgroundColor: getTagColor(tag) + '40' },
                ]}
                onPress={() => handleTagSelect(tag)}
              >
                <Icon 
                  name={getTagIcon(tag)} 
                  size={16} 
                  color={getTagColor(tag)} 
                  style={styles.tagIcon} 
                />
                <Text
                  style={[
                    styles.tagText,
                    { color: getTagColor(tag) },
                  ]}
                >
                  {tag}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        ) : (
          <Text style={styles.emptyTagsText}>No tags found</Text>
        )}
      </View>
      
      {/* Content Grid */}
      <View style={styles.contentContainer}>
        {selectedTag ? (
          <>
            <View style={styles.selectedTagHeader}>
              <Icon 
                name={getTagIcon(selectedTag)} 
                size={20} 
                color={getTagColor(selectedTag)} 
              />
              <Text style={styles.selectedTagText}>{selectedTag}</Text>
              <TouchableOpacity 
                style={styles.clearButton} 
                onPress={() => setSelectedTag(null)}
              >
                <Icon name="close-circle" size={20} color="#8E8E93" />
              </TouchableOpacity>
            </View>
            
            {isLoadingItems ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.loadingText}>Loading items...</Text>
              </View>
            ) : tagItems && tagItems.length > 0 ? (
              <FlatList
                data={tagItems}
                keyExtractor={item => item.id}
                numColumns={numColumns}
                renderItem={({ item }) => (
                  <MemoCard
                    item={item}
                    onPress={() => handleItemPress(item)}
                    width={(windowWidth - 24 - (numColumns - 1) * 8) / numColumns}
                  />
                )}
                contentContainerStyle={styles.gridContainer}
                columnWrapperStyle={styles.row}
              />
            ) : (
              <View style={styles.emptyContainer}>
                <Icon name="folder-open-outline" size={64} color="#E5E5EA" />
                <Text style={styles.emptyTitle}>No items with this tag</Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.noSelectionContainer}>
            <Icon name="pricetags" size={64} color="#E5E5EA" />
            <Text style={styles.noSelectionTitle}>Select a tag to view items</Text>
            <Text style={styles.noSelectionSubtitle}>
              Tags help you organize and discover your saved content
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
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
    borderRadius: 22,
    backgroundColor: 'rgba(99,102,241,0.08)',
    marginLeft: theme.spacing.sm,
  },
  tagsContainer: {
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 0,
    backgroundColor: theme.colors.cardGlass,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
    marginLeft: theme.spacing.lg,
  },
  loader: {
    marginVertical: theme.spacing.sm,
  },
  tagsList: {
    paddingHorizontal: theme.spacing.md,
    paddingBottom: theme.spacing.xs,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tagButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    marginHorizontal: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
    borderRadius: 18,
    backgroundColor: theme.colors.cardGlass,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  tagIcon: {
    marginRight: theme.spacing.sm,
  },
  tagText: {
    fontSize: theme.font.size.sm,
    fontWeight: '500',
  },
  emptyTagsText: {
    fontSize: theme.font.size.sm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginVertical: theme.spacing.md,
  },
  contentContainer: {
    flex: 1,
  },
  selectedTagHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.cardGlass,
    borderRadius: 16,
    margin: theme.spacing.md,
    shadowColor: theme.colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 2,
  },
  selectedTagText: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginLeft: theme.spacing.sm,
    flex: 1,
  },
  clearButton: {
    padding: theme.spacing.xs,
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
  gridContainer: {
    padding: theme.spacing.md,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: theme.spacing.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  emptyTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: theme.spacing.lg,
  },
  noSelectionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  noSelectionTitle: {
    fontSize: theme.font.size.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  noSelectionSubtitle: {
    fontSize: theme.font.size.md,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
});

export default TagsScreen; 