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

export interface SearchRequest {
  user_id: string;
  query: string;
  top_k?: number;
  content_type?: string;
  platform?: string;
  similarity_threshold?: number;
}

export interface GetItemsRequest {
  user_id: string;
  content_type?: string;
  platform?: string;
  limit?: number;
  offset?: number;
}

export interface GetTagsRequest {
  user_id: string;
}

export interface GetItemsByTagRequest {
  user_id: string;
  tag: string;
  limit?: number;
  offset?: number;
}

export interface SaveUrlRequest {
  user_id: string;
  url: string;
}

export interface ApiError {
  message: string;
  status: number;
}