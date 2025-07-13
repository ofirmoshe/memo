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
        a: First vector (can be list or numpy array)
        b: Second vector (can be list or numpy array)
        
    Returns:
        float: Cosine similarity
    """
    # Convert to numpy arrays and flatten if needed
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    
    # Check if arrays have the same shape
    if a.shape != b.shape:
        raise ValueError(f"Vector shapes don't match: {a.shape} vs {b.shape}")
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)

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
        if item.embedding:
            try:
                # Ensure embedding is a valid list of numbers
                if not isinstance(item.embedding, list) or not item.embedding:
                    logger.warning(f"Invalid embedding for item {item.id}: not a list or empty")
                    continue
                    
                similarity = cosine_similarity(query_embedding, item.embedding)
                results.append({
                    "id": item.id,
                    "user_id": item.user_id,
                    "url": item.url,
                    "title": item.title,
                    "description": item.description,
                    "tags": item.tags,
                    "timestamp": item.timestamp,
                    "content_type": item.content_type,
                    "platform": item.platform,
                    "media_type": item.media_type,
                    "content_data": item.content_data,
                    "file_path": item.file_path,
                    "file_size": item.file_size,
                    "mime_type": item.mime_type,
                    "user_context": item.user_context,
                    "similarity_score": float(similarity)
                })
            except Exception as e:
                logger.error(f"Error calculating similarity for item {item.id}: {str(e)}")
                continue
    
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
            "content_type": item.content_type,
            "platform": item.platform,
            "media_type": item.media_type,
            "content_data": item.content_data,
            "file_path": item.file_path,
            "file_size": item.file_size,
            "mime_type": item.mime_type,
            "user_context": item.user_context,
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

def determine_dynamic_threshold(query: str, results: List[Dict[str, Any]]) -> float:
    """
    Determine optimal similarity threshold based on query characteristics and result quality.
    
    Strategy:
    1. For short queries (1-2 words), be more lenient with thresholds
    2. For longer queries, maintain higher quality standards
    3. Detect when there's a clear winner with high relevance - increase threshold
    4. Always ensure we show at least some results if they exist
    
    Args:
        query: The search query
        results: List of search results with similarity scores
        
    Returns:
        Optimal threshold value
    """
    if not results:
        return 0.0
    
    # Extract and sort similarity scores
    scores = [r.get('similarity_score', 0) for r in results]
    scores.sort(reverse=True)
    max_score = max(scores) if scores else 0
    
    # Analyze query characteristics
    query_words = query.strip().split()
    query_length = len(query_words)
    is_short_query = query_length <= 2
    
    # Define base thresholds based on query type
    if is_short_query:
        # For short queries like "recipe", "decor", be more lenient
        primary_threshold = 0.25    # Lowered from 0.35
        secondary_threshold = 0.15  # Fallback threshold
        min_results_needed = 1      # Show results even if just 1 decent match
    else:
        # For longer queries, maintain higher standards
        primary_threshold = 0.35
        secondary_threshold = 0.20  # Slightly higher fallback for longer queries
        min_results_needed = 2      # Need at least 2 good results
    
    # NEW: Detect "clear winner" scenarios - high relevance with significant gap
    if len(scores) >= 2:
        top_score = scores[0]
        second_score = scores[1]
        
        # Check if there's a clear winner with high relevance
        is_high_relevance = top_score >= 0.5  # High relevance threshold
        significant_gap = (top_score - second_score) >= 0.2  # Significant gap
        
        # Alternative check: top result is much better than average of rest
        if len(scores) >= 3:
            avg_rest = sum(scores[1:]) / len(scores[1:])
            large_gap_vs_average = (top_score - avg_rest) >= 0.25
        else:
            large_gap_vs_average = False
        
        # If there's a clear winner, be more selective
        if is_high_relevance and (significant_gap or large_gap_vs_average):
            # Increase threshold to be more selective, but ensure the top result qualifies
            if is_short_query:
                adjusted_threshold = min(0.35, top_score * 0.7)  # More selective for short queries
            else:
                adjusted_threshold = min(0.45, top_score * 0.75)  # Even more selective for long queries
            
            # Ensure the adjusted threshold doesn't exclude the clear winner
            adjusted_threshold = min(adjusted_threshold, top_score - 0.05)  # Leave some margin
            
            logger.info(f"Clear winner detected - Top: {top_score:.3f}, Second: {second_score:.3f}, Gap: {top_score - second_score:.3f}")
            logger.info(f"Increasing threshold from {primary_threshold:.3f} to {adjusted_threshold:.3f} to be more selective")
            
            # Use the adjusted threshold as primary and ensure we have at least 1 result
            primary_threshold = adjusted_threshold
            min_results_needed = 1  # At least show the clear winner
    
    # Count results above thresholds
    high_quality_count = sum(1 for score in scores if score >= primary_threshold)
    reasonable_count = sum(1 for score in scores if score >= secondary_threshold)
    
    # Decision logic
    if high_quality_count >= min_results_needed:
        final_threshold = primary_threshold
        logger.info(f"Using primary threshold {primary_threshold:.3f} for {'short' if is_short_query else 'long'} query - found {high_quality_count} high-quality results")
    
    elif reasonable_count >= min_results_needed:
        # Use secondary threshold
        final_threshold = secondary_threshold
        logger.info(f"Using secondary threshold {final_threshold:.3f} for {'short' if is_short_query else 'long'} query - found {reasonable_count} reasonable results")
    
    else:
        # Very poor results - but for short queries, be even more lenient
        if is_short_query and max_score > 0.10:
            final_threshold = 0.10  # Very lenient for short queries
            logger.info(f"Using very lenient threshold {final_threshold:.3f} for short query - max score: {max_score:.3f}")
        else:
            # No good results found
            final_threshold = 1.0  # Filter out all results
            logger.info(f"All results are poor quality (max score: {max_score:.3f}) - filtering out all results")
    
    # Log the decision
    logger.info(f"Dynamic threshold for '{query}' (query_length: {query_length}): {final_threshold:.3f} (max_score: {max_score:.3f}, total_results: {len(scores)})")
    
    return final_threshold

def search_content(user_id: str, query: str, top_k: int = 5, content_type: str = None, platform: str = None, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Search for content using a natural language query.
    
    Args:
        user_id: User ID
        query: Search query
        top_k: Number of results to return
        content_type: Optional filter by content type
        platform: Optional filter by platform
        similarity_threshold: Minimum similarity score threshold (0.0 to 1.0)
        
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
                "embedding_score": result["similarity_score"],
                "keyword_score": 0.0,
                "similarity_score": result["similarity_score"] * 0.7  # 70% weight for embedding similarity
            }
        
        # Add or update with keyword results
        for result in keyword_results:
            if result["id"] in results_map:
                # Combine scores if item already in results
                results_map[result["id"]]["keyword_score"] = result["similarity_score"]
                results_map[result["id"]]["similarity_score"] += result["similarity_score"] * 0.3  # 30% weight for keyword matching
            else:
                # Add new item with adjusted score
                results_map[result["id"]] = {
                    **result,
                    "embedding_score": 0.0,
                    "keyword_score": result["similarity_score"],
                    "similarity_score": result["similarity_score"] * 0.3  # 30% weight for keyword matching
                }
        
        # Convert map back to list
        combined_results = list(results_map.values())
        
        # Apply filters
        filtered_results = []
        for result in combined_results:
            # Apply similarity threshold filter
            if result["similarity_score"] < similarity_threshold:
                continue
                
            # Apply content_type filter if specified
            if content_type and result.get("content_type") != content_type:
                continue
            
            # Apply platform filter if specified
            if platform and result.get("platform") != platform:
                continue
            
            # If we get here, the result matches all filters
            filtered_results.append(result)
        
        # Use filtered results
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

def get_all_items(user_id: str, content_type: str = None, platform: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all items for a user with optional filtering.
    
    Args:
        user_id: User ID
        content_type: Optional filter by content type
        platform: Optional filter by platform
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        List of items
    """
    logger.info(f"Getting all items for user {user_id}")
    
    db = SessionLocal()
    
    try:
        # Start with base query
        query = db.query(Item).filter(Item.user_id == user_id)
        
        # Apply content_type filter if specified
        if content_type:
            query = query.filter(Item.content_type == content_type)
        
        # Apply platform filter if specified
        if platform:
            query = query.filter(Item.platform == platform)
        
        # Apply pagination
        query = query.order_by(Item.timestamp.desc()).offset(offset).limit(limit)
        
        # Execute query
        items = query.all()
        
        # Convert items to dict
        results = []
        for item in items:
            results.append({
                "id": item.id,
                "user_id": item.user_id,
                "url": item.url,
                "title": item.title,
                "description": item.description,
                "tags": item.tags,
                "timestamp": item.timestamp,
                "content_type": item.content_type,
                "platform": item.platform
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Error getting items: {str(e)}")
        raise
    finally:
        db.close()

def get_all_tags(user_id: str) -> List[str]:
    """
    Get all unique tags used by a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of unique tags
    """
    logger.info(f"Getting all tags for user {user_id}")
    
    db = SessionLocal()
    
    try:
        # Get all items for the user
        items = db.query(Item).filter(Item.user_id == user_id).all()
        
        # Extract and flatten tags
        all_tags = []
        for item in items:
            if item.tags:
                all_tags.extend(item.tags)
        
        # Get unique tags
        unique_tags = list(set(all_tags))
        
        # Sort alphabetically
        unique_tags.sort()
        
        return unique_tags
    
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise
    finally:
        db.close()

def get_items_by_tag(user_id: str, tag: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all items for a user with a specific tag.
    
    Args:
        user_id: User ID
        tag: Tag to filter by
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        List of items
    """
    logger.info(f"Getting items with tag '{tag}' for user {user_id}")
    
    db = SessionLocal()
    
    try:
        # Get all items for the user
        items = db.query(Item).filter(Item.user_id == user_id).all()
        
        # Filter items by tag
        filtered_items = []
        for item in items:
            if item.tags and tag.lower() in [t.lower() for t in item.tags]:
                filtered_items.append(item)
        
        # Apply pagination
        paginated_items = filtered_items[offset:offset + limit]
        
        # Convert items to dict
        results = []
        for item in paginated_items:
            results.append({
                "id": item.id,
                "user_id": item.user_id,
                "url": item.url,
                "title": item.title,
                "description": item.description,
                "tags": item.tags,
                "timestamp": item.timestamp,
                "content_type": item.content_type,
                "platform": item.platform
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Error getting items by tag: {str(e)}")
        raise
    finally:
        db.close()

def delete_item(user_id: str, item_id: str) -> bool:
    """
    Delete an item by item_id for a specific user.
    Args:
        user_id: User ID
        item_id: Item ID
    Returns:
        True if deleted, False if not found
    """
    logger.info(f"Deleting item {item_id} for user {user_id}")
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting item: {str(e)}")
        raise
    finally:
        db.close()

def search_items(db, user_id: str, query: str, top_k: int = 5, content_type: str = None, 
                platform: str = None, media_type: str = None, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Search for items using semantic similarity with enhanced filtering.
    
    Args:
        db: Database session
        user_id: User ID to search for
        query: Search query
        top_k: Number of results to return
        content_type: Filter by content type
        platform: Filter by platform
        media_type: Filter by media type (url, text, image, document)
        similarity_threshold: Minimum similarity score
        
    Returns:
        List of matching items with similarity scores
    """
    try:
        # Generate embedding for the query
        query_embedding = generate_embedding(query)
        
        # Build base query
        db_query = db.query(Item).filter(Item.user_id == user_id)
        
        # Apply filters
        if content_type:
            db_query = db_query.filter(Item.content_type == content_type)
        if platform:
            db_query = db_query.filter(Item.platform == platform)
        if media_type:
            db_query = db_query.filter(Item.media_type == media_type)
        
        # Get all matching items
        items = db_query.all()
        
        if not items:
            return []
        
        # Calculate similarities
        results = []
        for item in items:
            if item.embedding:
                try:
                    # Ensure embedding is a valid list of numbers
                    if not isinstance(item.embedding, list) or not item.embedding:
                        logger.warning(f"Invalid embedding for item {item.id}: not a list or empty")
                        continue
                        
                    # Calculate cosine similarity
                    similarity = cosine_similarity(query_embedding, item.embedding)
                    
                    if similarity >= similarity_threshold:
                        results.append({
                            'item': item,
                            'similarity': similarity
                        })
                except Exception as e:
                    logger.error(f"Error calculating similarity for item {item.id}: {str(e)}")
                    continue
        
        # Sort by similarity and take top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]
        
        # Convert to response format
        response = []
        for result in results:
            item = result['item']
            response.append({
                'id': item.id,
                'user_id': item.user_id,
                'url': item.url,
                'title': item.title,
                'description': item.description,
                'tags': item.tags or [],
                'timestamp': item.timestamp,
                'content_type': item.content_type,
                'platform': item.platform,
                'media_type': item.media_type,
                'content_data': item.content_data,
                'file_path': item.file_path,
                'file_size': item.file_size,
                'mime_type': item.mime_type,
                'user_context': item.user_context,
                'similarity_score': result['similarity']
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching items: {str(e)}")
        raise 