export const API_BASE_URL = 'https://memora-production-da39.up.railway.app';

export interface SearchResult {
  id: string;
  user_id: string;
  url?: string;
  title?: string;
  description?: string;
  tags: string[];
  timestamp: string;
  content_type?: string;
  platform?: string;
  media_type?: string;
  content_data?: any; // legacy, may be removed later
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  user_context?: string;
  similarity_score?: number;
  // New explicit fields
  content_text?: string;
  content_json?: Record<string, any> | null;
  preview_image_url?: string | null;
  preview_thumbnail_path?: string | null;
}

export interface UserItem {
  id: string;
  user_id: string;
  url?: string;
  title?: string;
  description?: string;
  tags: string[];
  timestamp: string;
  content_type?: string;
  platform?: string;
  media_type?: string;
  content_data?: any; // legacy, may be removed later
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  user_context?: string;
  similarity_score?: number;
  // New explicit fields
  content_text?: string;
  content_json?: Record<string, any> | null;
  preview_image_url?: string | null;
  preview_thumbnail_path?: string | null;
}

export interface UserStats {
  total_items: number;
  urls: number;
  texts: number;
  images: number;
  documents: number;
  top_tags: Array<[string, number]>;
}

export interface TagWithCount {
  tag: string;
  count: number;
}

export interface TagGroup {
  tag: string;
  count: number;
  items: UserItem[];
}

export interface TagGroupsResponse {
  groups: TagGroup[];
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  // Helper method to safely parse content_data
  private parseContentData(contentData: any): any {
    if (!contentData) return null;
    if (typeof contentData === 'object') {
      return contentData;
    }
    if (typeof contentData === 'string') {
      try {
        return JSON.parse(contentData);
      } catch (error) {
        console.warn('Failed to parse content_data as JSON:', error);
        return null;
      }
    }
    return null;
  }

  private mapItem<T extends SearchResult | UserItem>(raw: any): T {
    return {
      ...raw,
      content_data: this.parseContentData(raw.content_data),
    } as T;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // Search functionality - POST /search
  async search(query: string, userId: string): Promise<SearchResult[]> {
    const data = await this.request<SearchResult[]>(`/search`, {
      method: 'POST',
      body: JSON.stringify({
        query,
        user_id: userId,
        top_k: 10,
        similarity_threshold: 0.0
      }),
    });
    return data.map(d => this.mapItem<SearchResult>(d));
  }

  // Save a simple text note
  saveText(text: string, userId: string): Promise<UserItem & { message: string }> {
    return this.request('/save-text', {
      method: 'POST',
      body: JSON.stringify({ text_content: text, user_id: userId }),
    });
  }

  // Extract content from a URL
  extractUrl(url: string, userId: string, userContext: string | null): Promise<UserItem & { message:string }> {
    return this.request('/extract', {
      method: 'POST',
      body: JSON.stringify({ url, user_id: userId, user_context: userContext }),
    });
  }

  // Upload a file
  async uploadFile(formData: FormData, userId: string): Promise<UserItem> {
    try {
      formData.append('user_id', userId);
      const response = await fetch(`${this.baseUrl}/upload-file`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to upload file: ${errorText}`);
      }
      return response.json();
    } catch (e) {
      console.error("Error uploading file:", e);
      throw e;
    }
  }

  // Search items - POST /search
  async searchItems(userId: string, query: string): Promise<UserItem[]> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, query: query, top_k: 10 })
    });
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    const data = await response.json();
    return data.map((item: any) => this.mapItem<UserItem>(item));
  }

  // Get user items - GET /user/{user_id}/items
  async getUserItems(userId: string): Promise<UserItem[]> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/items`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    const data = await response.json();
    return data.map((item: any) => this.mapItem<UserItem>(item));
  }

  // Get user stats - GET /user/{user_id}/stats
  async getUserStats(userId: string): Promise<UserStats> {
    return this.request<UserStats>(`/user/${userId}/stats`);
  }

  // Get tags with counts - GET /user/{user_id}/tags
  async getTagsWithCounts(userId: string): Promise<{ tags: TagWithCount[] }> {
    return this.request<{ tags: TagWithCount[] }>(`/user/${userId}/tags`);
  }

  // Get tag groups - GET /user/{user_id}/items/by-tag
  async getTagGroups(userId: string): Promise<TagGroupsResponse> {
    return this.request<TagGroupsResponse>(`/user/${userId}/items/by-tag`);
  }

  // Delete item - POST /delete-item
  async deleteItem(itemId: string, userId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/delete-item`, {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId, user_id: userId }),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }

  // Detect intent
  async detectIntent(text: string): Promise<{ intent: 'search' | 'save' | 'greeting' | 'general', english_text: string, answer: string }> {
    try {
      const response = await this.request(`/intent`, {
        method: 'POST',
        body: JSON.stringify({ text }),
      });
      return response as { intent: 'search' | 'save' | 'greeting' | 'general', english_text: string, answer: string };
    } catch (e) {
      console.error("Error calling /intent endpoint:", e);
      return { intent: 'save', english_text: text, answer: '' };
    }
  }

  // Debug method to help discover available endpoints
  async debugEndpoints(userId: string): Promise<void> {
    const endpointsToTest = ['/health', `/user/${userId}/items`, `/user/${userId}/stats`];
    console.log('🔍 Testing backend endpoints...');
    for (const endpoint of endpointsToTest) {
      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`, { headers: { 'Content-Type': 'application/json' } });
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ ${endpoint} - Status: ${response.status}`, data);
        } else {
          console.log(`❌ ${endpoint} - Status: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        console.log(`💥 ${endpoint} - Error:`, error);
      }
    }
  }
}

export const apiService = new ApiService(API_BASE_URL);

// Add the new method to the exported service object
(apiService as any).uploadFile = apiService.uploadFile.bind(apiService); 