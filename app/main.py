from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import logging
import platform
import socket
import psutil
from datetime import datetime

from app.models.schemas import ExtractRequest, SearchRequest, MemoraItem
from app.db.database import get_db, init_db
from app.utils.extractor import extract_and_save_content
from app.utils.search import search_content, get_all_items, get_all_tags, get_items_by_tag

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

@app.get("/items", response_model=List[MemoraItem])
async def get_items(
    user_id: str,
    content_type: Optional[str] = None,
    platform: Optional[str] = None,
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: Optional[int] = Query(0, ge=0)
):
    """
    Get all saved content for a user.
    
    Optionally filter by content type and platform, with pagination support.
    """
    try:
        results = get_all_items(
            user_id=user_id,
            content_type=content_type,
            platform=platform,
            limit=limit,
            offset=offset
        )
        return results
    except Exception as e:
        logger.error(f"Error getting items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags", response_model=List[str])
async def get_tags(user_id: str):
    """
    Get all unique tags used by a user.
    """
    try:
        results = get_all_tags(user_id=user_id)
        return results
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/by-tag/{tag}", response_model=List[MemoraItem])
async def get_items_by_tag_endpoint(
    tag: str,
    user_id: str,
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: Optional[int] = Query(0, ge=0)
):
    """
    Get all items for a user with a specific tag.
    """
    try:
        results = get_items_by_tag(
            user_id=user_id,
            tag=tag,
            limit=limit,
            offset=offset
        )
        return results
    except Exception as e:
        logger.error(f"Error getting items by tag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint with detailed system information for debugging.
    """
    try:
        # Get database connection status
        db = next(get_db())
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get system information
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    # Get Docker container information if available
    in_docker = os.path.exists("/.dockerenv")
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_usage = {
        "total": f"{memory.total / (1024 * 1024 * 1024):.2f} GB",
        "available": f"{memory.available / (1024 * 1024 * 1024):.2f} GB",
        "percent": f"{memory.percent}%"
    }
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_usage = {
        "total": f"{disk.total / (1024 * 1024 * 1024):.2f} GB",
        "free": f"{disk.free / (1024 * 1024 * 1024):.2f} GB",
        "percent": f"{disk.percent}%"
    }
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "server": {
            "hostname": hostname,
            "ip": ip_address,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "in_docker": in_docker
        },
        "database": {
            "status": db_status
        },
        "resources": {
            "memory": memory_usage,
            "disk": disk_usage,
            "cpu_percent": psutil.cpu_percent(interval=0.1)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 