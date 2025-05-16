from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

class ExtractRequest(BaseModel):
    """Request for extracting content from a URL and saving it."""
    user_id: str = Field(..., description="User ID")
    url: str = Field(..., description="URL to extract content from")

class SearchRequest(BaseModel):
    """Request for searching content."""
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Number of results to return")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    platform: Optional[str] = Field(None, description="Filter by platform")
    similarity_threshold: Optional[float] = Field(0.0, description="Minimum similarity score threshold (0.0 to 1.0)")

class MemoraItem(BaseModel):
    """Item stored in the Memora database."""
    id: str
    user_id: str
    url: str
    title: str
    description: str
    tags: List[str]
    timestamp: datetime
    content_type: Optional[str] = None
    platform: Optional[str] = None
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True 