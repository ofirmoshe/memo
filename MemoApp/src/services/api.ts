import axios from 'axios';
import { useMutation, useQuery } from '@tanstack/react-query';
import { config } from '../config';
import { SaveUrlRequest, SearchRequest, SearchResponse, ContentItem, ApiError } from '../types/api';

const API_BASE_URL = config.api.baseUrl;

// Demo data
const demoContentItems: ContentItem[] = [
  {
    id: '1',
    url: 'https://example.com/article1',
    title: 'The Future of AI in Healthcare',
    content_type: 'article',
    platform: 'web',
    created_at: '2023-01-15T10:30:00Z',
    user_id: 'demo-user',
  },
  {
    id: '2',
    url: 'https://example.com/video1',
    title: 'Building Scalable Web Applications',
    content_type: 'video',
    platform: 'youtube',
    created_at: '2023-02-20T15:45:00Z',
    user_id: 'demo-user',
  },
  {
    id: '3',
    url: 'https://example.com/podcast1',
    title: 'The Art of Product Management',
    content_type: 'audio',
    platform: 'spotify',
    created_at: '2023-03-10T09:15:00Z',
    user_id: 'demo-user',
  },
  {
    id: '4',
    url: 'https://example.com/article2',
    title: 'Understanding TypeScript Generics',
    content_type: 'article',
    platform: 'web',
    created_at: '2023-04-05T14:20:00Z',
    user_id: 'demo-user',
  },
  {
    id: '5',
    url: 'https://example.com/video2',
    title: 'React Native Performance Optimization',
    content_type: 'video',
    platform: 'youtube',
    created_at: '2023-05-12T11:30:00Z',
    user_id: 'demo-user',
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

const demoSaveUrl = async (params: SaveUrlRequest): Promise<ContentItem> => {
  await delay(config.demo.delay);
  
  const newItem: ContentItem = {
    id: Date.now().toString(),
    url: params.url,
    title: `New Content - ${new Date().toLocaleDateString()}`,
    content_type: 'web',
    platform: 'web',
    created_at: new Date().toISOString(),
    user_id: params.user_id,
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

// API functions with demo mode support
export const searchContentFn = config.api.useDemoData ? demoSearchContent : realSearchContent;
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