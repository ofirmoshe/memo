export interface ContentItem {
  id: string;
  url: string;
  title: string;
  content_type: string | null;
  platform?: string | null;
  timestamp?: string;
  user_id: string;
  description?: string;
  tags?: string[];
  similarity_score?: number;
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