import logging
import numpy as np
from typing import List, Dict, Any
import re
from sqlalchemy import func

from app.db.database import SessionLocal, Item
from app.utils.llm import generate_embedding

# Configure logging
logger = logging.getLogger(__name__)

def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        float: Cosine similarity
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_by_embedding(db, user_id: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for items by embedding similarity.
    
    Args:
        db: Database session
        user_id: User ID
        query_embedding: Query embedding
        top_k: Number of results to return
        
    Returns:
        List of items
    """
    # Get all items for the user
    items = db.query(Item).filter(Item.user_id == user_id).all()
    
    # Calculate similarity for each item
    results = []
    for item in items:
        similarity = cosine_similarity(query_embedding, item.embedding)
        results.append({
            "id": item.id,
            "user_id": item.user_id,
            "url": item.url,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "timestamp": item.timestamp,
            "similarity_score": float(similarity)
        })
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    # Return top k results
    return results[:top_k]

def search_by_keywords(db, user_id: str, keywords: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for items by keywords.
    
    Args:
        db: Database session
        user_id: User ID
        keywords: List of keywords
        top_k: Number of results to return
        
    Returns:
        List of items
    """
    items = db.query(Item).filter(Item.user_id == user_id).all()
    
    results = []
    for item in items:
        # Calculate keyword match score (simple count of matching keywords)
        score = 0
        for keyword in keywords:
            # Check in title
            if keyword.lower() in item.title.lower():
                score += 2  # Higher weight for title matches
            
            # Check in description
            if keyword.lower() in item.description.lower():
                score += 1
            
            # Check in tags
            if any(keyword.lower() in tag.lower() for tag in item.tags):
                score += 1.5  # Medium weight for tag matches
        
        # Normalize score
        if len(keywords) > 0:
            score = score / len(keywords)
        
        results.append({
            "id": item.id,
            "user_id": item.user_id,
            "url": item.url,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "timestamp": item.timestamp,
            "similarity_score": score
        })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    # Return top k results
    return results[:top_k]

def extract_keywords(query: str) -> List[str]:
    """
    Extract keywords from a query.
    
    Args:
        query: Query string
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction (remove common words and split)
    stopwords = {"a", "an", "the", "in", "on", "at", "for", "to", "and", "or", "of", "with", "that", "this", "it", "is", "are", "was", "were", "be", "been"}
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    return keywords

def search_content(user_id: str, query: str, top_k: int = 5, content_type: str = None, platform: str = None) -> List[Dict[str, Any]]:
    """
    Search for content using a natural language query.
    
    Args:
        user_id: User ID
        query: Search query
        top_k: Number of results to return
        content_type: Optional filter by content type
        platform: Optional filter by platform
        
    Returns:
        List of items
    """
    logger.info(f"Searching content for user {user_id} with query: {query}")
    
    # Generate embedding for query
    query_embedding = generate_embedding(query)
    
    # Extract keywords from query
    keywords = extract_keywords(query)
    logger.info(f"Extracted keywords: {keywords}")
    
    db = SessionLocal()
    try:
        # Get results from embedding-based search
        embedding_results = search_by_embedding(db, user_id, query_embedding, top_k * 2)
        
        # Get results from keyword-based search
        keyword_results = search_by_keywords(db, user_id, keywords, top_k * 2)
        
        # Combine results (hybrid search)
        # Create a map of id -> result for easier merging
        results_map = {}
        
        # Add embedding results
        for result in embedding_results:
            results_map[result["id"]] = {
                **result,
                "similarity_score": result["similarity_score"] * 0.7  # 70% weight for embedding similarity
            }
        
        # Add or update with keyword results
        for result in keyword_results:
            if result["id"] in results_map:
                # Combine scores if item already in results
                results_map[result["id"]]["similarity_score"] += result["similarity_score"] * 0.3  # 30% weight for keyword matching
            else:
                # Add new item with adjusted score
                results_map[result["id"]] = {
                    **result,
                    "similarity_score": result["similarity_score"] * 0.3  # 30% weight for keyword matching
                }
        
        # Convert map back to list
        combined_results = list(results_map.values())
        
        # Apply filters if specified
        if content_type or platform:
            filtered_results = []
            for result in combined_results:
                # Check if result matches content_type filter
                if content_type and result.get("content_type") != content_type:
                    continue
                
                # Check if result matches platform filter
                if platform and result.get("platform") != platform:
                    continue
                
                # If we get here, the result matches all filters
                filtered_results.append(result)
            
            combined_results = filtered_results
        
        # Sort by similarity score
        combined_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top k results
        return combined_results[:top_k]
    
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        raise
    finally:
        db.close() 