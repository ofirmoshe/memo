from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Union, Literal, Dict, Any
from datetime import datetime

class ExtractRequest(BaseModel):
    """Request for extracting content from a URL and saving it."""
    user_id: str = Field(..., description="User ID")
    url: str = Field(..., description="URL to extract content from")
    user_context: Optional[str] = Field(None, description="User-provided context for the URL")

class SaveTextRequest(BaseModel):
    """Request for saving text content directly."""
    user_id: str = Field(..., description="User ID")
    text_content: str = Field(..., description="Text content to save")
    title: Optional[str] = Field(None, description="Optional title for the text")
    user_context: Optional[str] = Field(None, description="User-provided context for the text")

class SaveFileRequest(BaseModel):
    """Request for saving file content (will be used internally after file processing)."""
    user_id: str = Field(..., description="User ID")
    file_path: str = Field(..., description="Path to the saved file")
    original_filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="File size in bytes")
    user_context: Optional[str] = Field(None, description="User-provided context for the file")

class SearchRequest(BaseModel):
    """Request for searching content."""
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Number of results to return")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    platform: Optional[str] = Field(None, description="Filter by platform")
    media_type: Optional[Literal["url", "text", "image", "document"]] = Field(None, description="Filter by media type")
    similarity_threshold: Optional[float] = Field(0.0, description="Minimum similarity score threshold (0.0 to 1.0)")

class MemoraItem(BaseModel):
    """Item stored in the Memora database."""
    id: str
    user_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    timestamp: datetime
    content_type: Optional[str] = None
    platform: Optional[str] = None
    media_type: str = "url"
    content_data: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    user_context: Optional[str] = None
    similarity_score: Optional[float] = None
    # New fields
    content_text: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    preview_image_url: Optional[str] = None
    preview_thumbnail_path: Optional[str] = None

    class Config:
        from_attributes = True 