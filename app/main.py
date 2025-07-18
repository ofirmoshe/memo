from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import logging
import platform
import socket
import psutil
from datetime import datetime
from sqlalchemy.orm import Session
from collections import Counter
from pydantic import BaseModel

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.models.schemas import ExtractRequest, SearchRequest, MemoraItem, SaveTextRequest, SaveFileRequest
from app.db.database import get_db, init_db, get_or_create_user, Item
from app.utils.extractor import extract_and_save_content, extract_content_from_url
from app.utils.search import search_content, get_all_items, get_all_tags, get_items_by_tag, delete_item, search_items, determine_dynamic_threshold
from app.utils.llm import analyze_content_with_llm, generate_embedding, get_content_analysis_prompt, get_llm_response, get_text_analysis_prompt, get_file_analysis_prompt, analyze_image_with_llm, detect_intent_and_translate
from app.utils.file_processor import FileProcessor
import json

# User Profile imports
try:
    from app.api.user_profile import router as user_profile_router
    USER_PROFILES_AVAILABLE = True
except ImportError:
    logger.warning("User profile system not available - continuing without it")
    USER_PROFILES_AVAILABLE = False

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

# Include user profile router if available
if USER_PROFILES_AVAILABLE:
    app.include_router(user_profile_router)
    logger.info("User profile API endpoints enabled")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")
    
    # Auto-migrate user profiles for Railway deployment
    if USER_PROFILES_AVAILABLE and os.getenv("DATABASE_URL"):
        try:
            from app.db.migrations.add_user_profiles import check_migration_needed, run_migration
            from app.db.database import engine
            
            if check_migration_needed(engine):
                logger.info("Running user profile migration for Railway deployment...")
                success = run_migration(engine, "apply")
                if success:
                    logger.info("✅ User profile migration completed successfully")
                else:
                    logger.error("❌ User profile migration failed")
            else:
                logger.info("User profile tables already exist")
        except Exception as e:
            logger.warning(f"User profile migration skipped: {e}")
            logger.info("Continuing without user profiles")

# Initialize file processor
file_processor = FileProcessor()

class IntentRequest(BaseModel):
    text: str

# API endpoints
@app.post("/intent")
async def get_intent(request: IntentRequest):
    """Detect intent from text using LLM."""
    try:
        result = detect_intent_and_translate(request.text)
        return result
    except Exception as e:
        logger.error(f"Error getting intent for text '{request.text[:50]}...': {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing intent")

@app.post("/extract")
async def extract_and_save(request: ExtractRequest, db: Session = Depends(get_db)):
    """Extract content from URL and save it to the database."""
    try:
        logger.info(f"Processing URL: {request.url} for user: {request.user_id}")
        
        # Get or create user
        user = get_or_create_user(db, request.user_id)
        
        # Extract content from URL
        content = extract_content_from_url(request.url)
        
        if not content:
            raise HTTPException(status_code=400, detail="Failed to extract content from URL")
        
        # Check if extraction failed (e.g., TikTok photo posts)
        if content.get("success") == False:
            error_msg = content.get("error", "Content extraction failed")
            logger.warning(f"Content extraction failed for {request.url}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Create enhanced prompt with user context
        prompt = get_content_analysis_prompt(
            content=content.get("text", ""),
            url=request.url,
            user_context=request.user_context,
            media_type="url"
        )
        
        # Get LLM analysis
        llm_response = get_llm_response(prompt)
        
        try:
            analysis = json.loads(llm_response)
        except json.JSONDecodeError:
            # Fallback analysis if JSON parsing fails
            analysis = {
                "title": content.get("title", "Extracted Content"),
                "description": content.get("text", "")[:500],
                "tags": ["web_content"],
                "content_type": "web_content",
                "platform": "unknown"
            }
        
        # Generate embedding for search
        embedding_text = f"{analysis.get('title', '')} {analysis.get('description', '')} {request.user_context or ''}"
        embedding = generate_embedding(embedding_text)
        
        # Create and save item
        item = Item(
            user_id=request.user_id,
            url=request.url,
            title=analysis.get("title"),
            description=analysis.get("description"),
            tags=analysis.get("tags", []),
            embedding=embedding,
            content_type=analysis.get("content_type"),
            platform=analysis.get("platform"),
            media_type="url",
            user_context=request.user_context
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        logger.info(f"Successfully saved item with ID: {item.id}")
        
        return {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "content_type": item.content_type,
            "platform": item.platform,
            "media_type": item.media_type
        }
        
    except Exception as e:
        logger.error(f"Error processing URL {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")

@app.post("/save-text")
async def save_text(request: SaveTextRequest, db: Session = Depends(get_db)):
    """Save text content directly to the database."""
    try:
        logger.info(f"Saving text content for user: {request.user_id}")
        
        # Get or create user
        user = get_or_create_user(db, request.user_id)
        
        # Get English translation for LLM analysis
        try:
            llm_result = detect_intent_and_translate(request.text_content)
            english_text = llm_result.get("english_text", request.text_content)
        except Exception as e:
            logger.warning(f"Translation failed, using original text: {str(e)}")
            english_text = request.text_content
        
        # Create prompt for text analysis using English text
        prompt = get_text_analysis_prompt(
            text_content=english_text,
            user_context=request.user_context
        )
        
        # Get LLM analysis
        llm_response = get_llm_response(prompt)
        
        try:
            analysis = json.loads(llm_response)
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = {
                "title": request.title or "Text Note",
                "description": english_text[:500],
                "tags": ["personal_note"],
                "content_type": "personal_note",
                "platform": "personal"
            }
        
        # Generate embedding for search using English text
        embedding_text = f"{analysis.get('title', '')} {analysis.get('description', '')} {english_text} {request.user_context or ''}"
        embedding = generate_embedding(embedding_text)
        
        # Create and save item - store ORIGINAL text content
        item = Item(
            user_id=request.user_id,
            title=analysis.get("title"),
            description=analysis.get("description"),
            tags=analysis.get("tags", []),
            embedding=embedding,
            content_type=analysis.get("content_type"),
            platform=analysis.get("platform"),
            media_type="text",
            content_data=request.text_content,  # Store original text
            user_context=request.user_context
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        logger.info(f"Successfully saved text item with ID: {item.id}")
        
        return {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "content_type": item.content_type,
            "platform": item.platform,
            "media_type": item.media_type,
            "original_text": request.text_content  # Return original text
        }
        
    except Exception as e:
        logger.error(f"Error saving text for user {request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving text: {str(e)}")

@app.post("/save-file")
async def save_file(request: SaveFileRequest, db: Session = Depends(get_db)):
    """Save file content to the database after processing."""
    try:
        logger.info(f"Saving file {request.original_filename} for user: {request.user_id}")
        
        # Get or create user
        user = get_or_create_user(db, request.user_id)
        
        # Extract content from file
        extraction_result = file_processor.extract_content_from_file(
            request.file_path, request.mime_type
        )
        
        if extraction_result.get('error'):
            raise HTTPException(status_code=400, detail=f"Error processing file: {extraction_result['error']}")
        
        # Check if this is an image that requires multimodal LLM analysis
        if extraction_result.get('requires_llm_analysis') and request.mime_type.startswith('image/'):
            # Use multimodal LLM for image analysis
            try:
                llm_analysis = analyze_image_with_llm(request.file_path, request.user_context)
                extracted_text = llm_analysis.get('extracted_text', '')
                
                # Use the LLM analysis directly
                analysis = {
                    'title': llm_analysis.get('title', request.original_filename),
                    'description': llm_analysis.get('description', ''),
                    'tags': llm_analysis.get('tags', []),
                    'content_type': llm_analysis.get('content_type', 'image'),
                    'platform': llm_analysis.get('platform', 'personal')
                }
                
            except Exception as e:
                logger.error(f"Error with multimodal LLM analysis: {str(e)}")
                # Fallback analysis for images
                analysis = {
                    'title': request.original_filename,
                    'description': f"Image file: {request.original_filename}",
                    'tags': ['image', 'uploaded'],
                    'content_type': 'image',
                    'platform': 'personal'
                }
                extracted_text = ''
        else:
            # For documents, use traditional text extraction + LLM analysis
            extracted_text = extraction_result.get('text_content', '')
            metadata = extraction_result.get('metadata', {})
            
            if extracted_text:
                # Create prompt for file analysis
                prompt = get_file_analysis_prompt(
                    extracted_text=extracted_text,
                    file_path=request.file_path,
                    mime_type=request.mime_type,
                    metadata=metadata,
                    user_context=request.user_context
                )
                
                # Get LLM analysis
                llm_response = get_llm_response(prompt)
                
                try:
                    analysis = json.loads(llm_response)
                except json.JSONDecodeError:
                    # Fallback analysis
                    media_category = file_processor.get_file_category(request.mime_type)
                    analysis = {
                        "title": request.original_filename,
                        "description": extracted_text[:500] if extracted_text else f"Uploaded {media_category} file",
                        "tags": [media_category, "uploaded_file"],
                        "content_type": f"{media_category}_file",
                        "platform": "personal"
                    }
            else:
                # No text content extracted
                media_category = file_processor.get_file_category(request.mime_type)
                analysis = {
                    "title": request.original_filename,
                    "description": f"Uploaded {media_category} file",
                    "tags": [media_category, "uploaded_file"],
                    "content_type": f"{media_category}_file",
                    "platform": "personal"
                }
        
        # Generate embedding for search
        embedding_text = f"{analysis.get('title', '')} {analysis.get('description', '')} {extracted_text} {request.user_context or ''}"
        embedding = generate_embedding(embedding_text)
        
        # Determine media type
        media_type = "image" if request.mime_type.startswith("image/") else "document"
        
        # Create and save item
        item = Item(
            user_id=request.user_id,
            title=analysis.get("title"),
            description=analysis.get("description"),
            tags=analysis.get("tags", []),
            embedding=embedding,
            content_type=analysis.get("content_type"),
            platform=analysis.get("platform"),
            media_type=media_type,
            content_data=extracted_text,
            file_path=request.file_path,
            file_size=request.file_size,
            mime_type=request.mime_type,
            user_context=request.user_context
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        logger.info(f"Successfully saved file item with ID: {item.id}")
        
        return {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "content_type": item.content_type,
            "platform": item.platform,
            "media_type": item.media_type,
            "extracted_text_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        }
        
    except Exception as e:
        logger.error(f"Error saving file for user {request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.post("/search", response_model=List[MemoraItem])
async def search_content(request: SearchRequest, db: Session = Depends(get_db)):
    """Search for saved content."""
    try:
        logger.info(f"Searching for: {request.query} (user: {request.user_id})")
        logger.info(f"Search parameters: top_k={request.top_k}, similarity_threshold={request.similarity_threshold}")
        
        # First get results without threshold filtering
        results = search_items(
            db=db,
            user_id=request.user_id,
            query=request.query,
            top_k=request.top_k,
            content_type=request.content_type,
            platform=request.platform,
            media_type=request.media_type,
            similarity_threshold=0.0  # Get all results first
        )
        
        # Apply dynamic threshold if no explicit threshold was provided
        if request.similarity_threshold == 0.0:
            dynamic_threshold = determine_dynamic_threshold(request.query, results)
            logger.info(f"Using dynamic threshold: {dynamic_threshold:.3f}")
            results = [r for r in results if r.get('similarity_score', 0) >= dynamic_threshold]
            
            # If using fallback threshold (0.15), limit results to prevent noise
            if dynamic_threshold <= 0.15:
                # Only show top 5 results when using fallback threshold
                results = results[:5]
                logger.info(f"Limited fallback results to {len(results)} items")
        else:
            # Use explicit threshold
            results = [r for r in results if r.get('similarity_score', 0) >= request.similarity_threshold]
        
        # Log search results for debugging
        logger.info(f"Search returned {len(results)} results")
        if results:
            top_scores = [f"{r.get('similarity_score', 0):.3f}" for r in results[:5]]
            logger.info(f"Top 5 similarity scores: {top_scores}")
            
            # Log some sample results for debugging
            for i, result in enumerate(results[:3]):
                logger.info(f"Result {i+1}: title='{result.get('title', '')[:50]}...', score={result.get('similarity_score', 0):.3f}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching for user {request.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")

@app.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Get user statistics."""
    try:
        # Get or create user
        user = get_or_create_user(db, user_id)
        
        # Get all user items
        items = db.query(Item).filter(Item.user_id == user_id).all()
        
        # Calculate statistics
        total_items = len(items)
        media_type_counts = Counter(item.media_type for item in items)
        
        # Get top tags
        all_tags = []
        for item in items:
            if item.tags:
                all_tags.extend(item.tags)
        
        top_tags = Counter(all_tags).most_common(10)
        
        return {
            "total_items": total_items,
            "urls": media_type_counts.get("url", 0),
            "texts": media_type_counts.get("text", 0),
            "images": media_type_counts.get("image", 0),
            "documents": media_type_counts.get("document", 0),
            "top_tags": top_tags
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@app.get("/user/{user_id}/items", response_model=List[MemoraItem])
async def get_user_items(user_id: str, limit: int = 50, offset: int = 0, media_type: str = None, db: Session = Depends(get_db)):
    """Get user's saved items with pagination."""
    try:
        # Get or create user
        user = get_or_create_user(db, user_id)
        
        # Build query
        query = db.query(Item).filter(Item.user_id == user_id)
        
        if media_type:
            query = query.filter(Item.media_type == media_type)
        
        # Apply pagination and ordering
        items = query.order_by(Item.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        result = []
        for item in items:
            result.append(MemoraItem(
                id=item.id,
                user_id=item.user_id,
                url=item.url,
                title=item.title,
                description=item.description,
                tags=item.tags or [],
                timestamp=item.timestamp,
                content_type=item.content_type,
                platform=item.platform,
                media_type=item.media_type,
                content_data=item.content_data,
                file_path=item.file_path,
                file_size=item.file_size,
                mime_type=item.mime_type,
                user_context=item.user_context
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting items for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving items: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint for Railway deployment.
    """
    try:
        # Basic health check without database dependency during startup
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "memora-api",
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint with system information for debugging.
    """
    try:
        # Get database connection status
        try:
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
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    user_context: Optional[str] = Form(None)
):
    """Upload and process a file directly (for Telegram bot)."""
    try:
        logger.info(f"Uploading file {file.filename} for user: {user_id}")
        
        # Read file data
        file_data = await file.read()
        
        # Check file size
        if len(file_data) > file_processor.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds maximum allowed size")
        
        # Check if file type is supported
        if not file_processor.is_supported_file_type(file.content_type):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        # Save file
        file_path, mime_type, file_size = file_processor.save_file(
            file_data, file.filename, user_id
        )
        
        # Create SaveFileRequest and process it
        from app.models.schemas import SaveFileRequest
        request = SaveFileRequest(
            user_id=user_id,
            file_path=file_path,
            original_filename=file.filename,
            mime_type=mime_type,
            file_size=file_size,
            user_context=user_context
        )
        
        # Get database session
        db = next(get_db())
        try:
            # Process the file using the existing save_file logic
            result = await save_file(request, db)
            return result
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/file/{item_id}")
async def get_file(item_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Serve a file by item ID."""
    try:
        # Get the item from database
        item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
        
        if not item:
            logger.error(f"Item not found: {item_id} for user: {user_id}")
            raise HTTPException(status_code=404, detail="File not found")
        
        if not item.file_path:
            logger.error(f"No file path for item: {item_id}")
            raise HTTPException(status_code=404, detail="File path not available")
        
        # Convert relative path to absolute path if needed
        file_path = item.file_path
        if not os.path.isabs(file_path):
            # If it's a relative path, make it relative to the current working directory
            file_path = os.path.abspath(file_path)
        
        logger.info(f"Item {item_id} - Original path: {item.file_path}")
        logger.info(f"Item {item_id} - Resolved path: {file_path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            logger.error(f"File not found on disk: {file_path}")
            # List directory contents for debugging
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path):
                try:
                    files_in_dir = os.listdir(dir_path)
                    logger.info(f"Files in directory {dir_path}: {files_in_dir}")
                except Exception as e:
                    logger.error(f"Could not list directory {dir_path}: {e}")
            else:
                logger.error(f"Directory does not exist: {dir_path}")
            raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")
        
        logger.info(f"Successfully found file: {file_path}")
        
        # Return the file
        return FileResponse(
            path=file_path,
            filename=item.title or "download",
            media_type=item.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/debug/file/{item_id}")
async def debug_file(item_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    """Debug endpoint to check file information."""
    try:
        # Get the item from database
        item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
        
        if not item:
            return {"error": "Item not found"}
        
        file_path = item.file_path
        abs_file_path = os.path.abspath(file_path) if file_path else None
        
        debug_info = {
            "item_id": item_id,
            "user_id": user_id,
            "original_file_path": file_path,
            "absolute_file_path": abs_file_path,
            "current_working_directory": os.getcwd(),
            "file_exists": os.path.exists(abs_file_path) if abs_file_path else False,
            "item_info": {
                "title": item.title,
                "media_type": item.media_type,
                "mime_type": item.mime_type,
                "file_size": item.file_size
            }
        }
        
        # Check directory contents
        if abs_file_path:
            dir_path = os.path.dirname(abs_file_path)
            if os.path.exists(dir_path):
                try:
                    debug_info["directory_contents"] = os.listdir(dir_path)
                except Exception as e:
                    debug_info["directory_error"] = str(e)
            else:
                debug_info["directory_exists"] = False
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/delete-item")
async def delete_single_item(
    user_id: str = Body(...),
    item_id: str = Body(...),
    db: Session = Depends(get_db)
):
    """Delete a single item for a user by item_id."""
    try:
        item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(item)
        db.commit()
        return {"success": True, "message": "Item deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")

@app.post("/delete-all-items")
async def delete_all_items(
    user_id: str = Body(...),
    db: Session = Depends(get_db)
):
    """Delete all items for a user."""
    try:
        num_deleted = db.query(Item).filter(Item.user_id == user_id).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {num_deleted} items"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting all items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting all items: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 