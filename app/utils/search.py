import logging
import numpy as np
from typing import List, Dict, Any
import re
from sqlalchemy import func
from difflib import SequenceMatcher

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

def fuzzy_match_score(query_word: str, text: str, threshold: float = 0.6) -> float:
    """
    Calculate fuzzy matching score between a query word and text.
    
    Args:
        query_word: Word to search for
        text: Text to search in
        threshold: Minimum similarity threshold
        
    Returns:
        Best matching score found
    """
    if not query_word or not text:
        return 0.0
    
    query_word = query_word.lower()
    text = text.lower()
    
    # Direct substring match gets highest score
    if query_word in text:
        return 1.0
    
    # Check for fuzzy matches with individual words
    words = re.findall(r'\b\w+\b', text)
    best_score = 0.0
    
    for word in words:
        if len(word) < 3:  # Skip very short words
            continue
            
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, query_word, word).ratio()
        
        # Also check if query_word is a substring of word or vice versa
        if query_word in word or word in query_word:
            similarity = max(similarity, 0.8)
        
        best_score = max(best_score, similarity)
    
    return best_score if best_score >= threshold else 0.0

def expand_query_terms(query: str) -> List[str]:
    """
    Expand query terms with synonyms and related words.
    
    Args:
        query: Original query
        
    Returns:
        List of expanded terms
    """
    # Common synonyms and related terms
    synonyms = {
        'movie': ['film', 'cinema', 'video', 'flick'],
        'film': ['movie', 'cinema', 'video', 'flick'],
        'recipe': ['cooking', 'food', 'dish', 'meal', 'cuisine'],
        'cooking': ['recipe', 'food', 'dish', 'meal', 'cuisine'],
        'family': ['genealogy', 'ancestry', 'relatives', 'kinship'],
        'genealogy': ['family', 'ancestry', 'relatives', 'kinship'],
        'tree': ['genealogy', 'ancestry', 'family', 'lineage'],
        'good': ['great', 'excellent', 'amazing', 'wonderful', 'fantastic'],
        'interesting': ['fascinating', 'engaging', 'compelling', 'intriguing'],
        'tutorial': ['guide', 'howto', 'instructions', 'lesson'],
        'guide': ['tutorial', 'howto', 'instructions', 'lesson'],
        'article': ['post', 'blog', 'content', 'piece'],
        'post': ['article', 'blog', 'content', 'piece'],
    }
    
    # Extract base terms
    base_terms = extract_keywords(query)
    expanded_terms = set(base_terms)
    
    # Add synonyms
    for term in base_terms:
        if term in synonyms:
            expanded_terms.update(synonyms[term])
    
    return list(expanded_terms)

def simple_stem(word: str) -> str:
    """
    Simple stemming to handle common word variations.
    
    Args:
        word: Word to stem
        
    Returns:
        Stemmed word
    """
    word = word.lower()
    
    # Handle common suffixes
    suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment', 's']
    
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    
    return word

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
    Enhanced search for items by keywords with fuzzy matching and better scoring.
    
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
        # Calculate enhanced keyword match score
        score = 0
        matched_keywords = 0
        
        # Prepare text fields for searching
        title_text = item.title or ""
        description_text = item.description or ""
        content_text = item.content_data or ""
        tags_text = " ".join(item.tags) if item.tags else ""
        user_context_text = item.user_context or ""
        
        # Combine all searchable text
        all_text = f"{title_text} {description_text} {content_text} {tags_text} {user_context_text}"
        
        for keyword in keywords:
            keyword_score = 0
            
            # 1. Exact matches (highest weight)
            if keyword.lower() in title_text.lower():
                keyword_score += 3.0  # Highest weight for title matches
            if keyword.lower() in description_text.lower():
                keyword_score += 2.0
            if keyword.lower() in content_text.lower():
                keyword_score += 1.5
            if keyword.lower() in tags_text.lower():
                keyword_score += 2.5  # High weight for tag matches
            if keyword.lower() in user_context_text.lower():
                keyword_score += 1.0
            
            # 2. Fuzzy matches (medium weight)
            fuzzy_title = fuzzy_match_score(keyword, title_text, 0.7)
            fuzzy_description = fuzzy_match_score(keyword, description_text, 0.7)
            fuzzy_content = fuzzy_match_score(keyword, content_text, 0.7)
            fuzzy_tags = fuzzy_match_score(keyword, tags_text, 0.7)
            
            keyword_score += fuzzy_title * 2.0
            keyword_score += fuzzy_description * 1.5
            keyword_score += fuzzy_content * 1.0
            keyword_score += fuzzy_tags * 2.0
            
            # 3. Stemmed matches (lower weight)
            stemmed_keyword = simple_stem(keyword)
            if stemmed_keyword != keyword:
                if stemmed_keyword in all_text.lower():
                    keyword_score += 0.5
            
            if keyword_score > 0:
                matched_keywords += 1
                score += keyword_score
        
        # Bonus for matching multiple keywords
        if matched_keywords > 1:
            score *= (1 + 0.1 * (matched_keywords - 1))
        
        # Normalize score by number of keywords searched
        if len(keywords) > 0:
            score = score / len(keywords)
        
        # Only include items with some relevance
        if score > 0:
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
    Enhanced keyword extraction with better stopword handling.
    
    Args:
        query: Query string
        
    Returns:
        List of keywords
    """
    # Expanded stopwords list
    stopwords = {
        "a", "an", "the", "in", "on", "at", "for", "to", "and", "or", "of", "with", "that", "this", "it", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must",
        "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "our", "their",
        "but", "if", "so", "as", "up", "out", "by", "from", "into", "over", "under", "about", "through", "during", "before", "after",
        "find", "search", "look", "show", "get", "give", "want", "need", "like", "know", "think", "see", "come", "go", "make", "take"
    }
    
    # Extract words and clean them
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = []
    
    for word in words:
        # Skip stopwords and very short words
        if word not in stopwords and len(word) > 2:
            keywords.append(word)
    
    # If no keywords found, use original words (excluding very common ones)
    if not keywords:
        minimal_stopwords = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
        keywords = [word for word in words if word not in minimal_stopwords and len(word) > 1]
    
    return keywords

def search_content(user_id: str, query: str, top_k: int = 5, content_type: str = None, platform: str = None, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Enhanced search for content using a natural language query.
    
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
    
    # Handle edge cases
    if not query or not query.strip():
        logger.warning("Empty query provided")
        return []
    
    query = query.strip()
    
    # Generate embedding for query
    query_embedding = generate_embedding(query)
    
    # Extract and expand keywords from query
    base_keywords = extract_keywords(query)
    expanded_keywords = expand_query_terms(query)
    all_keywords = list(set(base_keywords + expanded_keywords))
    
    logger.info(f"Base keywords: {base_keywords}")
    logger.info(f"Expanded keywords: {expanded_keywords}")
    
    # If no keywords found, use the original query words
    if not all_keywords:
        all_keywords = query.lower().split()
        logger.info(f"Using fallback keywords: {all_keywords}")
    
    db = SessionLocal()
    try:
        # Get results from embedding-based search
        embedding_results = search_by_embedding(db, user_id, query_embedding, top_k * 3)
        
        # Get results from keyword-based search
        keyword_results = search_by_keywords(db, user_id, all_keywords, top_k * 3)
        
        # Combine results (hybrid search)
        results_map = {}
        
        # Add embedding results with weight
        embedding_weight = 0.7  # Slightly higher weight for semantic similarity
        for result in embedding_results:
            results_map[result["id"]] = {
                **result,
                "similarity_score": result["similarity_score"] * embedding_weight
            }
        
        # Add or update with keyword results
        keyword_weight = 0.3  # Lower weight for keyword matching
        for result in keyword_results:
            if result["id"] in results_map:
                # Combine scores if item already in results
                results_map[result["id"]]["similarity_score"] += result["similarity_score"] * keyword_weight
            else:
                # Add new item with adjusted score
                results_map[result["id"]] = {
                    **result,
                    "similarity_score": result["similarity_score"] * keyword_weight
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