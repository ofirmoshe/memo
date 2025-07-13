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
    Search for items by keywords with improved precision.
    
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
        # Calculate keyword match score with better precision
        score = 0
        total_matches = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Check in title (highest weight)
            if keyword_lower in item.title.lower():
                # Exact word match gets higher score than substring match
                if f" {keyword_lower} " in f" {item.title.lower()} ":
                    score += 3  # Exact word match in title
                else:
                    score += 2  # Substring match in title
                total_matches += 1
            
            # Check in description (medium weight)
            if keyword_lower in item.description.lower():
                # Exact word match gets higher score than substring match
                if f" {keyword_lower} " in f" {item.description.lower()} ":
                    score += 2  # Exact word match in description
                else:
                    score += 1  # Substring match in description
                total_matches += 1
            
            # Check in tags (high weight for exact matches)
            if any(keyword_lower in tag.lower() for tag in item.tags):
                # Exact tag match gets highest score
                if any(keyword_lower == tag.lower() for tag in item.tags):
                    score += 4  # Exact tag match
                else:
                    score += 2  # Partial tag match
                total_matches += 1
            
            # Check in content_data if available (low weight)
            if item.content_data and keyword_lower in item.content_data.lower():
                if f" {keyword_lower} " in f" {item.content_data.lower()} ":
                    score += 1  # Exact word match in content
                else:
                    score += 0.5  # Substring match in content
                total_matches += 1
        
        # Calculate precision score: reward items that match more keywords
        if len(keywords) > 0:
            keyword_coverage = total_matches / len(keywords)  # Percentage of keywords matched
            score = score * keyword_coverage  # Penalize items that match few keywords
        
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
    Determine optimal similarity threshold based on query characteristics and result quality distribution.
    
    This approach is distribution-based rather than using hardcoded thresholds, making it stable
    across different search algorithm implementations.
    
    Strategy:
    1. Analyze the distribution of relevance scores
    2. Detect quality gaps and natural breakpoints
    3. Use statistical measures to determine optimal cutoff
    4. Adapt based on query characteristics (short vs long queries)
    
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
    
    if len(scores) == 1:
        # Single result - show it if it's not completely irrelevant
        return max(0.0, scores[0] - 0.01)
    
    # Analyze query characteristics
    query_words = query.strip().split()
    query_length = len(query_words)
    is_short_query = query_length <= 2
    
    # Calculate statistical measures of the distribution
    max_score = scores[0]
    min_score = scores[-1]
    score_range = max_score - min_score
    
    # If all scores are very similar, use a lenient threshold
    if score_range < 0.1:
        return min_score
    
    # Calculate percentiles for distribution analysis
    n = len(scores)
    p75_idx = max(0, int(n * 0.25) - 1)  # Top 25%
    p50_idx = max(0, int(n * 0.5) - 1)   # Top 50%
    p25_idx = max(0, int(n * 0.75) - 1)  # Top 75%
    
    p75_score = scores[p75_idx]
    p50_score = scores[p50_idx]
    p25_score = scores[p25_idx]
    
    # Method 1: Look for natural gaps in the distribution
    # Find the largest gap between consecutive scores
    largest_gap = 0
    gap_position = -1
    
    for i in range(len(scores) - 1):
        gap = scores[i] - scores[i + 1]
        if gap > largest_gap:
            largest_gap = gap
            gap_position = i
    
    # Method 2: Detect "clear winner" scenarios - but be more conservative
    # When top result is significantly better than the rest
    clear_winner_threshold = None
    if len(scores) >= 3:
        top_score = scores[0]
        second_score = scores[1]
        avg_rest = sum(scores[1:]) / len(scores[1:])
        
        # Check for significant separation from top result
        gap_from_second = top_score - second_score
        gap_from_avg = top_score - avg_rest
        
        # Use relative gaps instead of absolute values
        relative_gap_second = gap_from_second / max(top_score, 0.01)
        relative_gap_avg = gap_from_avg / max(top_score, 0.01)
        
        # Be more conservative: require larger relative gaps
        if relative_gap_second > 0.5 or relative_gap_avg > 0.6:
            # Set threshold to include top result(s) but exclude the gap
            clear_winner_threshold = second_score + (gap_from_second * 0.5)
            logger.info(f"Clear winner detected - Top: {top_score:.3f}, Gap: {gap_from_second:.3f} ({relative_gap_second:.1%})")
    
    # Method 3: Use statistical measures for different query types
    if is_short_query:
        # For short queries, be more inclusive
        # Use median as baseline, but don't exclude too much
        base_threshold = p50_score
        
        # Adjust based on score distribution
        if score_range > 0.3:
            # Wide distribution - use 75th percentile
            statistical_threshold = p75_score
        else:
            # Narrow distribution - be more lenient
            statistical_threshold = p25_score
    else:
        # For longer queries, be more selective
        # Use 75th percentile as baseline
        base_threshold = p75_score
        
        # Adjust based on distribution characteristics
        if score_range > 0.4:
            # Very wide distribution - be more selective
            statistical_threshold = p75_score
        else:
            # Moderate distribution - use median
            statistical_threshold = p50_score
    
    # Method 4: Gap-based threshold - improved logic
    gap_threshold = None
    if largest_gap > 0.15 and gap_position < len(scores) * 0.7:  # Gap in top 70% of results
        # Use the gap as a natural breakpoint, but be conservative
        gap_threshold = scores[gap_position + 1] + (largest_gap * 0.1)  # Only 10% above the gap
        logger.info(f"Significant gap detected at position {gap_position + 1}: {largest_gap:.3f}")
    
    # Combine all methods and choose the most appropriate threshold
    candidate_thresholds = []
    
    # Add statistical threshold (always available)
    candidate_thresholds.append(("statistical", statistical_threshold))
    
    # Add gap-based threshold if significant
    if gap_threshold is not None:
        candidate_thresholds.append(("gap", gap_threshold))
    
    # Add clear winner threshold if detected
    if clear_winner_threshold is not None:
        candidate_thresholds.append(("clear_winner", clear_winner_threshold))
    
    # Choose the best threshold - prioritize natural gaps over clear winners
    if gap_threshold is not None and largest_gap > 0.2:
        # Strong gap takes precedence
        final_threshold = gap_threshold
        method = "gap"
    elif clear_winner_threshold is not None and len(scores) >= 5:
        # Clear winner only for larger result sets
        final_threshold = clear_winner_threshold
        method = "clear_winner"
    else:
        # Use statistical threshold
        final_threshold = statistical_threshold
        method = "statistical"
    
    # Ensure we don't exclude everything
    results_above_threshold = sum(1 for score in scores if score >= final_threshold)
    
    # Minimum results guarantee
    min_results = 1 if is_short_query else 1
    
    if results_above_threshold < min_results:
        # Fallback: ensure we show at least minimum results
        if len(scores) >= min_results:
            final_threshold = scores[min_results - 1]
            method = "minimum_guarantee"
        else:
            final_threshold = min_score
            method = "show_all"
    
    # Maximum results limit to prevent noise
    max_results = 8 if is_short_query else 6
    if results_above_threshold > max_results:
        # Too many results - raise threshold
        final_threshold = scores[max_results - 1]
        method = "maximum_limit"
    
    # Log the decision
    logger.info(f"Dynamic threshold for '{query}' (query_length: {query_length}): {final_threshold:.3f}")
    logger.info(f"Method: {method}, Score range: {min_score:.3f}-{max_score:.3f}, Results: {results_above_threshold}/{len(scores)}")
    
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
                "similarity_score": result["similarity_score"] * 0.6  # 60% weight for embedding similarity
            }
        
        # Add or update with keyword results
        for result in keyword_results:
            if result["id"] in results_map:
                # Combine scores if item already in results
                keyword_score = result["similarity_score"]
                # Normalize keyword score to 0-1 range (assuming max keyword score is around 10)
                normalized_keyword_score = min(keyword_score / 10.0, 1.0)
                results_map[result["id"]]["keyword_score"] = normalized_keyword_score
                results_map[result["id"]]["similarity_score"] += normalized_keyword_score * 0.4  # 40% weight for keyword matching
            else:
                # Add new item with adjusted score
                keyword_score = result["similarity_score"]
                normalized_keyword_score = min(keyword_score / 10.0, 1.0)
                results_map[result["id"]] = {
                    **result,
                    "embedding_score": 0.0,
                    "keyword_score": normalized_keyword_score,
                    "similarity_score": normalized_keyword_score * 0.4  # 40% weight for keyword matching
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