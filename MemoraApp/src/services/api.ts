// Backend URL - replace with your Railway deployment URL
const BACKEND_URL = 'memo-production-9d97.up.railway.app';

export interface MemoraItem {
  id: string;
  user_id: string;
  url?: string;
  title?: string;
  description?: string;
  tags: string[];
  timestamp: string;
  content_type?: string;
  platform?: string;
  media_type: string;
  content_data?: string;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  user_context?: string;
  similarity_score?: number;
}

export interface SearchRequest {
  user_id: string;
  query: string;
  top_k?: number;
  content_type?: string;
  platform?: string;
  media_type?: string;
  similarity_threshold?: number;
}

export interface SaveTextRequest {
  user_id: string;
  text_content: string;
  title?: string;
  user_context?: string;
}

export interface ExtractRequest {
  user_id: string;
  url: string;
  user_context?: string;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = BACKEND_URL;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Search for content
  async search(request: SearchRequest): Promise<MemoraItem[]> {
    return this.makeRequest<MemoraItem[]>('/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Save text content
  async saveText(request: SaveTextRequest): Promise<MemoraItem> {
    return this.makeRequest<MemoraItem>('/save-text', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Extract and save URL content
  async extractUrl(request: ExtractRequest): Promise<MemoraItem> {
    return this.makeRequest<MemoraItem>('/extract', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Upload file
  async uploadFile(
    file: {
      uri: string;
      name: string;
      type: string;
    },
    userId: string,
    userContext?: string
  ): Promise<MemoraItem> {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.type,
    } as any);
    formData.append('user_id', userId);
    if (userContext) {
      formData.append('user_context', userContext);
    }

    return this.makeRequest<MemoraItem>('/upload-file', {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Get user items
  async getUserItems(
    userId: string,
    limit: number = 50,
    offset: number = 0,
    mediaType?: string
  ): Promise<MemoraItem[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (mediaType) {
      params.append('media_type', mediaType);
    }

    return this.makeRequest<MemoraItem[]>(`/user/${userId}/items?${params}`);
  }

  // Get user stats
  async getUserStats(userId: string): Promise<any> {
    return this.makeRequest(`/user/${userId}/stats`);
  }

  // Delete item
  async deleteItem(userId: string, itemId: string): Promise<void> {
    return this.makeRequest('/delete-item', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        item_id: itemId,
      }),
    });
  }

  // Get file
  async getFile(itemId: string, userId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/file/${itemId}?user_id=${userId}`);
    if (!response.ok) {
      throw new Error(`Failed to get file: ${response.status}`);
    }
    return response.blob();
  }

  // Health check
  async healthCheck(): Promise<any> {
    return this.makeRequest('/health');
  }
}

export const apiService = new ApiService(); 