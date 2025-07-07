const API_BASE_URL = 'https://memo-production-9d97.up.railway.app';

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
  content_data?: any;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  user_context?: string;
  similarity_score?: number;
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
  content_data?: any;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  user_context?: string;
  similarity_score?: number;
}

export interface UserStats {
  total_items: number;
  urls: number;
  texts: number;
  images: number;
  documents: number;
  top_tags: Array<[string, number]>;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
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
    return this.request<SearchResult[]>(`/search`, {
      method: 'POST',
      body: JSON.stringify({
        query,
        user_id: userId,
        top_k: 10,
        similarity_threshold: 0.0
      }),
    });
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
  async uploadFile(file: any, userId: string, userContext: string | null): Promise<any> {
    const response = await fetch(`${this.baseUrl}/upload-file`, {
      method: 'POST',
      body: file,
    });

    if (!response.ok) {
      throw new Error(`File upload failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Get user items - GET /user/{user_id}/items
  async getUserItems(userId: string): Promise<UserItem[]> {
    return this.request<UserItem[]>(`/user/${userId}/items`);
  }

  // Get user stats - GET /user/{user_id}/stats
  async getUserStats(userId: string): Promise<UserStats> {
    return this.request<UserStats>(`/user/${userId}/stats`);
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
      // The backend now handles this, so we can trust the response structure.
      return response as { intent: 'search' | 'save' | 'greeting' | 'general', english_text: string, answer: string };
    } catch (e) {
      console.error("Error calling /intent endpoint:", e);
      // A more robust fallback in case of network error etc.
      return { intent: 'save', english_text: text, answer: '' };
    }
  }

  // Debug method to help discover available endpoints
  async debugEndpoints(userId: string): Promise<void> {
    const endpointsToTest = [
      '/health',
      `/user/${userId}/items`,
      `/user/${userId}/stats`
    ];

    console.log('🔍 Testing backend endpoints...');
    
    for (const endpoint of endpointsToTest) {
      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
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

export const apiService = new ApiService(); 