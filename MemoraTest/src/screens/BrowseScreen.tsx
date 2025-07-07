import React, { useState, useEffect, useCallback } from 'react';
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
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { apiService, UserItem } from '../services/api';
import { Theme } from '../config/theme';
import LinkIcon from '../components/icons/LinkIcon';

const API_BASE_URL = 'https://memo-production-9d97.up.railway.app';
const { width } = Dimensions.get('window');
const PADDING = 16;
const ITEM_WIDTH = (width - (PADDING * 3)) / 2;

interface FilterCounts {
  all: number;
  text: number;
  url: number;
  image: number;
  document: number;
}

const USER_ID = '831447258';

type FilterType = 'all' | 'text' | 'url' | 'image' | 'document';

export const BrowseScreen: React.FC = () => {
  const { theme } = useTheme();
  const [memories, setMemories] = useState<UserItem[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<UserItem[]>([]);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterCounts, setFilterCounts] = useState<FilterCounts>({
    all: 0, text: 0, url: 0, image: 0, document: 0,
  });
  const [selectedMemory, setSelectedMemory] = useState<UserItem | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

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

  const loadMemories = async () => {
    try {
      const items = await apiService.getUserItems(USER_ID);
      const sortedItems = items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setMemories(sortedItems);
      filterMemories(activeFilter, sortedItems);
      setFilterCounts(calculateFilterCounts(sortedItems));
    } catch (error) {
      console.error('Error loading memories:', error);
      Alert.alert('Error', 'Failed to load memories. Please try again.');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadMemories();
  }, [activeFilter]);

  const filterMemories = (filter: FilterType, memoriesToFilter: UserItem[]) => {
    setActiveFilter(filter);
    if (filter === 'all') {
      setFilteredMemories(memoriesToFilter);
    } else {
      const filtered = memoriesToFilter.filter(memory => mapContentType(memory.media_type || '') === filter);
      setFilteredMemories(filtered);
    }
  };

  const handleDeleteMemory = (memory: UserItem) => {
    Alert.alert('Delete Memory', `Are you sure you want to delete "${memory.title || 'this memory'}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              if(modalVisible) closeModalDetails();
              await apiService.deleteItem(memory.id, USER_ID);
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

  const openMemoryDetails = (memory: UserItem) => {
    setSelectedMemory(memory);
    setModalVisible(true);
  };

  const closeModalDetails = () => {
    setModalVisible(false);
    setSelectedMemory(null);
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const styles = getStyles(theme);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }
  
  const FilterPill = ({ filterType, label }: { filterType: FilterType, label: string }) => {
    const count = filterCounts[filterType];
    const isActive = activeFilter === filterType;
    if (count === 0 && filterType !== 'all') return null;

    return (
      <TouchableOpacity
        style={[styles.filterPill, { backgroundColor: isActive ? theme.colors.primary : theme.colors.surface }]}
        onPress={() => filterMemories(filterType, memories)}
      >
        <Text style={[styles.filterText, { color: isActive ? theme.colors.background : theme.colors.text }]}>{label}</Text>
      </TouchableOpacity>
    );
  };

  const renderItem = ({ item }: { item: UserItem }) => {
    const previewImage = getPreviewImageUrl(item);

    return (
      <TouchableOpacity style={styles.itemContainer} onPress={() => openMemoryDetails(item)} key={item.id}>
        {previewImage ? (
          <Image source={{ uri: previewImage }} style={styles.itemImage} resizeMode="cover" />
        ) : (
          !item.file_path && item.media_type === 'url' && (
            <View style={styles.itemImagePlaceholder}>
              <LinkIcon color={theme.colors.textTertiary} width={40} height={40}/>
            </View>
          )
        )}
        <View style={styles.cardContent}>
          <Text style={styles.cardTitle} numberOfLines={3}>{item.title || 'Untitled Memory'}</Text>
          {item.description && item.description !== item.title && (
            <Text style={styles.cardDescription} numberOfLines={2}>{item.description}</Text>
          )}
          <View style={styles.cardFooter}>
            <View style={styles.tagsContainer}>
              {item.tags?.slice(0, 2).map((tag, i) => <View key={i} style={styles.tag}><Text style={styles.tagText}>{tag}</Text></View>)}
              {item.tags && item.tags.length > 2 && <Text style={styles.moreTagsText}>+{item.tags.length - 2}</Text>}
            </View>
            <Text style={styles.timestamp}>{formatTimestamp(item.timestamp)}</Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Browse</Text>
      </View>
      <View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterContent}>
          <FilterPill filterType="all" label="All" />
          <FilterPill filterType="url" label="Links" />
          <FilterPill filterType="text" label="Notes" />
          <FilterPill filterType="image" label="Images" />
          <FilterPill filterType="document" label="Documents" />
        </ScrollView>
      </View>

      <ScrollView
        contentContainerStyle={styles.memoriesContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
      >
        {filteredMemories.length > 0 ? (
          <View style={styles.grid}>
            {filteredMemories.map((memory) => renderItem({ item: memory }))}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle}>No {activeFilter !== 'all' ? activeFilter : ''} memories found</Text>
            <Text style={styles.emptyStateSubtitle}>Try adding some in the Chat tab!</Text>
          </View>
        )}
      </ScrollView>

      {selectedMemory && (
        <Modal visible={modalVisible} animationType="slide" presentationStyle="pageSheet" onRequestClose={closeModalDetails}>
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={closeModalDetails} style={styles.modalButton}><Text style={styles.modalButtonText}>Close</Text></TouchableOpacity>
              <Text style={styles.modalTitle} numberOfLines={1}>{selectedMemory.title || 'Memory Details'}</Text>
              <TouchableOpacity onPress={() => handleDeleteMemory(selectedMemory)} style={styles.modalButton}><Text style={[styles.modalButtonText, { color: theme.colors.error }]}>Delete</Text></TouchableOpacity>
            </View>
            <ScrollView style={styles.modalContent}>
              {getPreviewImageUrl(selectedMemory) && <Image source={{ uri: getPreviewImageUrl(selectedMemory)! }} style={styles.modalPreviewImage} resizeMode="contain" />}
              <Text style={styles.modalMemoryTitle}>{selectedMemory.title || 'Untitled'}</Text>
              {selectedMemory.url && <Text style={styles.modalUrl}>{selectedMemory.url}</Text>}
              {selectedMemory.description && <Text style={styles.modalDescription}>{selectedMemory.description}</Text>}
              {selectedMemory.content_data && typeof selectedMemory.content_data === 'string' && (
                <View style={styles.modalSection}><Text style={styles.modalSectionTitle}>Content</Text><Text style={styles.modalContentData}>{selectedMemory.content_data}</Text></View>
              )}
              {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                <View style={styles.modalSection}><Text style={styles.modalSectionTitle}>Tags</Text><View style={styles.modalTagsContainer}>{selectedMemory.tags.map((tag, i) => <View key={i} style={styles.modalTag}><Text style={styles.modalTagText}>{tag}</Text></View>)}</View></View>
              )}
              <View style={styles.modalSection}><Text style={styles.modalSectionTitle}>Details</Text><Text style={styles.modalMetadata}>Type: {mapContentType(selectedMemory.media_type || '').toUpperCase()}</Text><Text style={styles.modalMetadata}>Created: {new Date(selectedMemory.timestamp).toLocaleString()}</Text>{selectedMemory.platform && <Text style={styles.modalMetadata}>Platform: {selectedMemory.platform}</Text>}{selectedMemory.user_context && <Text style={styles.modalMetadata}>Context: {selectedMemory.user_context}</Text>}</View>
            </ScrollView>
          </SafeAreaView>
        </Modal>
      )}
    </SafeAreaView>
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.background },
  header: { paddingHorizontal: PADDING, paddingTop: 16, paddingBottom: 8 },
  headerTitle: { fontSize: theme.typography.h1.fontSize, fontWeight: 'bold', color: theme.colors.text },
  filterContent: { paddingHorizontal: PADDING, paddingVertical: 12 },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 100,
    marginRight: 8,
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
  },
  memoriesContent: { paddingHorizontal: PADDING, paddingBottom: 32 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  itemContainer: {
    width: ITEM_WIDTH,
    marginBottom: PADDING,
    backgroundColor: theme.colors.card,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  itemImage: {
    width: '100%',
    height: 120,
  },
  itemImagePlaceholder: {
    width: '100%',
    height: 120,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardContent: { padding: 12, flex: 1 },
  cardTitle: { fontSize: 14, fontWeight: '600', color: theme.colors.text, marginBottom: 4 },
  cardDescription: { fontSize: 12, color: theme.colors.textSecondary, marginBottom: 8, lineHeight: 16 },
  cardFooter: { marginTop: 'auto', paddingTop: 8 },
  tagsContainer: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 },
  tag: { backgroundColor: theme.colors.surface, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6, marginRight: 6, marginBottom: 6 },
  tagText: { fontSize: 10, fontWeight: '600', color: theme.colors.textTertiary },
  moreTagsText: { fontSize: 10, fontWeight: '600', color: theme.colors.textTertiary },
  timestamp: { fontSize: 10, color: theme.colors.textTertiary, opacity: 0.8 },
  emptyState: { alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  emptyStateTitle: { fontSize: 18, fontWeight: '600', color: theme.colors.textSecondary, marginBottom: 8 },
  emptyStateSubtitle: { fontSize: 14, color: theme.colors.textTertiary },
  modalContainer: { flex: 1, backgroundColor: theme.colors.surface },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  modalButton: { padding: 8 },
  modalButtonText: { fontSize: 16, color: theme.colors.primary, fontWeight: '600' },
  modalTitle: { flex: 1, textAlign: 'center', fontSize: 16, fontWeight: '700', color: theme.colors.text },
  modalContent: { flex: 1, paddingHorizontal: 16 },
  modalPreviewImage: { width: '100%', height: 250, borderRadius: 12, marginVertical: 16, backgroundColor: theme.colors.surface },
  modalMemoryTitle: { fontSize: 24, fontWeight: 'bold', color: theme.colors.text, marginBottom: 8 },
  modalUrl: { fontSize: 14, color: theme.colors.primary, marginBottom: 16 },
  modalDescription: { fontSize: 16, color: theme.colors.textSecondary, lineHeight: 24, marginBottom: 24 },
  modalSection: { marginBottom: 24 },
  modalSectionTitle: { fontSize: 18, fontWeight: 'bold', color: theme.colors.text, marginBottom: 12 },
  modalContentData: { fontSize: 16, color: theme.colors.textSecondary, lineHeight: 24 },
  modalTagsContainer: { flexDirection: 'row', flexWrap: 'wrap' },
  modalTag: { backgroundColor: theme.colors.background, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, marginRight: 8, marginBottom: 8 },
  modalTagText: { fontSize: 14, color: theme.colors.textSecondary, fontWeight: '500' },
  modalMetadata: { fontSize: 12, color: theme.colors.textTertiary, lineHeight: 18, marginBottom: 4 },
}); 