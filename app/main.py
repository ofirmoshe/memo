from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import logging

from app.models.schemas import ExtractRequest, SearchRequest, MemoraItem
from app.db.database import get_db, init_db
from app.utils.extractor import extract_and_save_content
from app.utils.search import search_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Memora API",
    description="AI-powered personal memory assistant API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

# API endpoints
@app.post("/extract_and_save", response_model=MemoraItem)
async def extract_and_save(request: ExtractRequest):
    """
    Extract content from a URL and save it in the database.
    """
    try:
        result = extract_and_save_content(
            user_id=request.user_id,
            url=request.url
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=List[MemoraItem])
async def search(
    user_id: str,
    query: str,
    top_k: Optional[int] = Query(5, ge=1, le=20),
    content_type: Optional[str] = None,
    platform: Optional[str] = None,
    similarity_threshold: Optional[float] = Query(0.3, ge=0.0, le=1.0)
):
    """
    Search for saved content using a natural language query.
    
    Optionally filter by content type, platform, and similarity threshold.
    """
    try:
        results = search_content(
            user_id=user_id,
            query=query,
            top_k=top_k,
            content_type=content_type,
            platform=platform,
            similarity_threshold=similarity_threshold
        )
        return results
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 