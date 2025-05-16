export interface ContentItem {
  id: string;
  url: string;
  title: string;
  content_type: string;
  platform?: string;
  created_at: string;
  user_id: string;
}

export interface SearchResponse {
  items: ContentItem[];
  total: number;
}

export interface SaveUrlRequest {
  user_id: string;
  url: string;
}

export interface SearchRequest {
  user_id: string;
  query: string;
  top_k?: number;
  content_type?: string;
  platform?: string;
}

export interface ApiError {
  message: string;
  code: string;
} 