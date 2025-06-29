import axios from 'axios';
import { useMutation, useQuery, UseMutationResult } from '@tanstack/react-query';
import { config } from '../config';
import { 
  SaveUrlRequest, 
  SearchRequest, 
  SearchResponse, 
  ContentItem, 
  ApiError, 
  GetItemsRequest,
  GetTagsRequest,
  GetItemsByTagRequest
} from '../types/api';

const API_BASE_URL = config.api.baseUrl;

// Demo data
const demoContentItems: ContentItem[] = [
  {
    id: '1',
    url: 'https://example.com/article1',
    title: 'The Future of AI in Healthcare',
    content_type: 'article',
    platform: 'web',
    timestamp: '2023-01-15T10:30:00Z',
    user_id: 'demo-user',
    description: 'This article explores how artificial intelligence will transform healthcare over the next decade, focusing on diagnostics, personalized treatment, and administrative improvements.',
    tags: ['healthcare', 'artificial intelligence', 'technology', 'medicine'],
    similarity_score: 0.92,
  },
  {
    id: '2',
    url: 'https://example.com/video1',
    title: 'Building Scalable Web Applications',
    content_type: 'video',
    platform: 'youtube',
    timestamp: '2023-02-20T15:45:00Z',
    user_id: 'demo-user',
    description: 'A comprehensive tutorial on building web applications that can scale to millions of users, covering architecture, caching strategies, and database optimization.',
    tags: ['web development', 'scalability', 'programming', 'tutorial'],
    similarity_score: 0.85,
  },
  {
    id: '3',
    url: 'https://example.com/podcast1',
    title: 'The Art of Product Management',
    content_type: 'audio',
    platform: 'spotify',
    timestamp: '2023-03-10T09:15:00Z',
    user_id: 'demo-user',
    description: 'An insightful podcast episode discussing the challenges and best practices in modern product management, featuring interviews with industry leaders.',
    tags: ['product management', 'business', 'leadership', 'podcast'],
    similarity_score: 0.78,
  },
  {
    id: '4',
    url: 'https://example.com/article2',
    title: 'Understanding TypeScript Generics',
    content_type: 'article',
    platform: 'web',
    timestamp: '2023-04-05T14:20:00Z',
    user_id: 'demo-user',
    description: 'A deep dive into TypeScript generics, explaining how they work, when to use them, and how they can make your code more robust and reusable.',
    tags: ['typescript', 'programming', 'javascript', 'tutorial'],
    similarity_score: 0.72,
  },
  {
    id: '5',
    url: 'https://example.com/video2',
    title: 'React Native Performance Optimization',
    content_type: 'video',
    platform: 'youtube',
    timestamp: '2023-05-12T11:30:00Z',
    user_id: 'demo-user',
    description: 'Learn practical techniques to optimize the performance of your React Native applications, including memory management, rendering optimizations, and native module integration.',
    tags: ['react native', 'mobile development', 'performance', 'optimization'],
    similarity_score: 0.65,
  },
];

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Demo API functions
const demoSearchContent = async (params: SearchRequest): Promise<SearchResponse> => {
  await delay(config.demo.delay);
  
  if (!params.query) {
    return { items: [], total: 0 };
  }

  const query = params.query.toLowerCase();
  const filteredItems = demoContentItems.filter(item => 
    item.title.toLowerCase().includes(query) ||
    item.url.toLowerCase().includes(query) ||
    (item.platform?.toLowerCase() || '').includes(query)
  );

  return {
    items: filteredItems,
    total: filteredItems.length,
  };
};

const demoGetItems = async (params: GetItemsRequest): Promise<ContentItem[]> => {
  await delay(config.demo.delay);
  
  let filteredItems = [...demoContentItems];
  
  // Apply content_type filter if specified
  if (params.content_type) {
    filteredItems = filteredItems.filter(item => 
      item.content_type === params.content_type
    );
  }
  
  // Apply platform filter if specified
  if (params.platform) {
    filteredItems = filteredItems.filter(item => 
      item.platform === params.platform
    );
  }
  
  // Apply pagination
  const offset = params.offset || 0;
  const limit = params.limit || 100;
  
  return filteredItems.slice(offset, offset + limit);
};

const demoGetTags = async (params: GetTagsRequest): Promise<string[]> => {
  await delay(config.demo.delay);
  
  // Extract unique tags from demo items
  const tags = new Set<string>();
  demoContentItems.forEach(item => {
    if (item.tags) {
      item.tags.forEach(tag => tags.add(tag));
    }
  });
  
  return Array.from(tags).sort();
};

const demoGetItemsByTag = async (params: GetItemsByTagRequest): Promise<ContentItem[]> => {
  await delay(config.demo.delay);
  
  // Filter items by tag
  const filteredItems = demoContentItems.filter(item => 
    item.tags?.some(tag => tag.toLowerCase() === params.tag.toLowerCase())
  );
  
  // Apply pagination
  const offset = params.offset || 0;
  const limit = params.limit || 100;
  
  return filteredItems.slice(offset, offset + limit);
};

const demoSaveUrl = async (params: SaveUrlRequest): Promise<ContentItem> => {
  await delay(config.demo.delay);
  
  const newItem: ContentItem = {
    id: Date.now().toString(),
    url: params.url,
    title: `New Content - ${new Date().toLocaleDateString()}`,
    content_type: 'web',
    platform: 'web',
    timestamp: new Date().toISOString(),
    user_id: params.user_id,
    description: 'Automatically saved content from URL submission.',
    tags: ['saved', 'web'],
    similarity_score: 1.0,
  };

  demoContentItems.unshift(newItem);
  return newItem;
};

const demoCheckHealth = async (): Promise<boolean> => {
  await delay(config.demo.delay);
  return true;
};

// Real API functions
const realSearchContent = async (params: SearchRequest): Promise<SearchResponse> => {
  console.log('Making search request with params:', params);
  const response = await axios.get(`${API_BASE_URL}/search`, { params });
  console.log('Search response:', response.data);
  return {
    items: response.data,
    total: response.data.length
  };
};

const realGetItems = async (params: GetItemsRequest): Promise<ContentItem[]> => {
  console.log('Making get items request with params:', params);
  const response = await axios.get(`${API_BASE_URL}/items`, { params });
  console.log('Get items response:', response.data);
  return response.data;
};

const realGetTags = async (params: GetTagsRequest): Promise<string[]> => {
  console.log('Making get tags request with params:', params);
  const response = await axios.get(`${API_BASE_URL}/tags`, { params });
  console.log('Get tags response:', response.data);
  return response.data;
};

const realGetItemsByTag = async (params: GetItemsByTagRequest): Promise<ContentItem[]> => {
  console.log('Making get items by tag request with params:', params);
  const { tag, ...queryParams } = params;
  const response = await axios.get(`${API_BASE_URL}/items/by-tag/${encodeURIComponent(tag)}`, { 
    params: queryParams 
  });
  console.log('Get items by tag response:', response.data);
  return response.data;
};

const realSaveUrl = async (params: SaveUrlRequest): Promise<ContentItem> => {
  const response = await axios.post(`${API_BASE_URL}/extract_and_save`, params);
  return response.data;
};

const realCheckHealth = async (): Promise<boolean> => {
  try {
    await axios.get(`${API_BASE_URL}/health`);
    return true;
  } catch {
    return false;
  }
};

const realDeleteItem = async (itemId: string, userId: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/items/${itemId}`, { params: { user_id: userId } });
};

// API functions with demo mode support
export const searchContentFn = config.api.useDemoData ? demoSearchContent : realSearchContent;
export const getItemsFn = config.api.useDemoData ? demoGetItems : realGetItems;
export const getTagsFn = config.api.useDemoData ? demoGetTags : realGetTags;
export const getItemsByTagFn = config.api.useDemoData ? demoGetItemsByTag : realGetItemsByTag;
export const saveUrlFn = config.api.useDemoData ? demoSaveUrl : realSaveUrl;
export const checkHealthFn = config.api.useDemoData ? demoCheckHealth : realCheckHealth;

// React Query hooks
export const useSearchContent = (params: SearchRequest, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchContentFn(params),
    enabled: options?.enabled ?? true,
  });
};

export const useGetItems = (params: GetItemsRequest, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['items', params],
    queryFn: () => getItemsFn(params),
    enabled: options?.enabled ?? true,
  });
};

export const useGetTags = (params: GetTagsRequest, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['tags', params],
    queryFn: () => getTagsFn(params),
    enabled: options?.enabled ?? true,
  });
};

export const useGetItemsByTag = (params: GetItemsByTagRequest, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['itemsByTag', params],
    queryFn: () => getItemsByTagFn(params),
    enabled: options?.enabled ?? true,
  });
};

export const useSaveUrl = () => {
  return useMutation({
    mutationFn: saveUrlFn,
  });
};

export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: checkHealthFn,
    staleTime: 1000 * 60, // 1 minute
  });
};

export const useDeleteItem = (): UseMutationResult<void, unknown, { itemId: string; userId: string }, unknown> => {
  return useMutation(async ({ itemId, userId }: { itemId: string; userId: string }) => {
    await realDeleteItem(itemId, userId);
  });
}; 