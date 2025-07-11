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
        'coupon': ['discount', 'deal', 'offer', 'promotion', 'sale'],
        'discount': ['coupon', 'deal', 'offer', 'promotion', 'sale'],
        'deal': ['coupon', 'discount', 'offer', 'promotion', 'sale'],
        'store': ['shop', 'market', 'supermarket', 'retail'],
        'shop': ['store', 'market', 'supermarket', 'retail'],
    }
    
    # Extract base terms
    base_terms = extract_keywords(query)
    expanded_terms = set(base_terms)
    
    # Add synonyms
    for term in base_terms:
        if term in synonyms:
            expanded_terms.update(synonyms[term])
    
    # Handle specific multi-word phrases
    query_lower = query.lower()
    if 'rami levy' in query_lower:
        expanded_terms.update(['rami', 'levy', 'supermarket', 'grocery'])
    if 'family tree' in query_lower:
        expanded_terms.update(['genealogy', 'ancestry', 'relatives', 'lineage'])
    if 'good movie' in query_lower or 'interesting film' in query_lower:
        expanded_terms.update(['recommendation', 'watch', 'entertainment'])
    
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
        total_score = 0
        matched_keywords = 0
        keyword_scores = []
        
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
            
            # 1. Exact matches (normalized weights)
            if keyword.lower() in title_text.lower():
                keyword_score += 1.0  # Reduced from 3.0
            if keyword.lower() in description_text.lower():
                keyword_score += 0.8  # Reduced from 2.0
            if keyword.lower() in content_text.lower():
                keyword_score += 0.6  # Reduced from 1.5
            if keyword.lower() in tags_text.lower():
                keyword_score += 0.9  # Reduced from 2.5
            if keyword.lower() in user_context_text.lower():
                keyword_score += 0.4  # Reduced from 1.0
            
            # 2. Fuzzy matches (normalized weights)
            fuzzy_title = fuzzy_match_score(keyword, title_text, 0.7)
            fuzzy_description = fuzzy_match_score(keyword, description_text, 0.7)
            fuzzy_content = fuzzy_match_score(keyword, content_text, 0.7)
            fuzzy_tags = fuzzy_match_score(keyword, tags_text, 0.7)
            
            keyword_score += fuzzy_title * 0.7  # Reduced from 2.0
            keyword_score += fuzzy_description * 0.5  # Reduced from 1.5
            keyword_score += fuzzy_content * 0.3  # Reduced from 1.0
            keyword_score += fuzzy_tags * 0.6  # Reduced from 2.0
            
            # 3. Stemmed matches (lower weight)
            stemmed_keyword = simple_stem(keyword)
            if stemmed_keyword != keyword:
                if stemmed_keyword in all_text.lower():
                    keyword_score += 0.2  # Reduced from 0.5
            
            if keyword_score > 0:
                matched_keywords += 1
                keyword_scores.append(keyword_score)
        
        # 4. Check for exact phrase matches (bonus for multi-word queries)
        original_query = " ".join(keywords)
        if len(keywords) > 1 and original_query.lower() in all_text.lower():
            phrase_bonus = 0.5  # Significant bonus for exact phrase matches
            if original_query.lower() in title_text.lower():
                phrase_bonus += 0.3  # Extra bonus if in title
            elif original_query.lower() in tags_text.lower():
                phrase_bonus += 0.2  # Extra bonus if in tags
            keyword_scores.append(phrase_bonus)
        
        # Calculate final score with better normalization
        if keyword_scores:
            # Average of keyword scores
            avg_keyword_score = sum(keyword_scores) / len(keyword_scores)
            
            # Bonus for matching multiple keywords (but not too much)
            keyword_coverage = matched_keywords / len(keywords)
            coverage_bonus = 1 + (0.3 * keyword_coverage)  # Max 30% bonus
            
            # Final score: normalize to 0-1 range
            total_score = min(1.0, avg_keyword_score * coverage_bonus / 2.0)  # Divide by 2 to normalize
        
        # Only include items with some relevance
        if total_score > 0:
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
                "similarity_score": total_score
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
    
    # First pass: identify important multi-word terms that shouldn't be split
    query_lower = query.lower()
    important_phrases = []
    
    # Check for known important phrases
    known_phrases = [
        'rami levy', 'family tree', 'good movie', 'interesting film', 
        'home decor', 'python programming', 'machine learning'
    ]
    
    for phrase in known_phrases:
        if phrase in query_lower:
            important_phrases.append(phrase)
            # Add individual words too
            for word in phrase.split():
                if word not in stopwords and len(word) > 2:
                    keywords.append(word)
    
    # Second pass: add other individual words
    for word in words:
        # Skip stopwords and very short words
        if word not in stopwords and len(word) > 2:
            # Don't add if already part of an important phrase
            already_included = False
            for phrase in important_phrases:
                if word in phrase.split():
                    already_included = True
                    break
            if not already_included:
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
        embedding_weight = 0.6  # Reduced from 0.7 for more balance
        for result in embedding_results:
            results_map[result["id"]] = {
                **result,
                "embedding_score": result["similarity_score"],
                "keyword_score": 0.0,
                "similarity_score": result["similarity_score"] * embedding_weight
            }
        
        # Add or update with keyword results
        keyword_weight = 0.4  # Increased from 0.3 for more balance
        for result in keyword_results:
            if result["id"] in results_map:
                # Combine scores if item already in results
                results_map[result["id"]]["keyword_score"] = result["similarity_score"]
                results_map[result["id"]]["similarity_score"] += result["similarity_score"] * keyword_weight
            else:
                # Add new item with adjusted score
                results_map[result["id"]] = {
                    **result,
                    "embedding_score": 0.0,
                    "keyword_score": result["similarity_score"],
                    "similarity_score": result["similarity_score"] * keyword_weight
                }
        
        # Apply relevance boost for items that match in both embedding and keyword search
        for item_id, result in results_map.items():
            if result["embedding_score"] > 0 and result["keyword_score"] > 0:
                # Boost score for items that match both semantically and lexically
                boost = 0.2 * min(result["embedding_score"], result["keyword_score"])
                result["similarity_score"] += boost
            
            # Apply relevance penalty for very generic matches
            # This helps reduce noise from overly broad keyword matches
            if result["keyword_score"] > 0 and result["embedding_score"] < 0.3:
                # If keyword score is high but embedding score is low, it might be a generic match
                generic_penalty = 0.1 * (result["keyword_score"] - result["embedding_score"])
                result["similarity_score"] = max(0.1, result["similarity_score"] - generic_penalty)
        
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

def determine_dynamic_threshold(query: str, results: List[Dict[str, Any]]) -> float:
    """
    Determine optimal similarity threshold based on result quality distribution.
    
    Strategy:
    1. Try primary threshold (0.35) - good quality results
    2. If too few results, fallback to secondary threshold (0.15) - but only if needed
    3. Always prioritize quality over quantity
    
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
    
    # Primary threshold for good quality results
    primary_threshold = 0.35
    secondary_threshold = 0.15
    
    # Count results above primary threshold
    high_quality_count = sum(1 for score in scores if score >= primary_threshold)
    
    # If we have good results (3+ above 0.35), use primary threshold
    if high_quality_count >= 3:
        final_threshold = primary_threshold
        logger.info(f"Using primary threshold {primary_threshold:.3f} - found {high_quality_count} high-quality results")
    
    # If we have some good results (1-2 above 0.35), still use primary but be slightly more lenient
    elif high_quality_count >= 1:
        # Use primary threshold but allow one more result if it's close
        final_threshold = max(0.30, primary_threshold)
        logger.info(f"Using slightly relaxed threshold {final_threshold:.3f} - found {high_quality_count} high-quality results")
    
    # If no good results, check if we have any reasonable results in the fallback range
    else:
        reasonable_count = sum(1 for score in scores if score >= secondary_threshold)
        if reasonable_count >= 1:
            # Use secondary threshold but cap the number of results we'll show
            final_threshold = secondary_threshold
            logger.info(f"Using fallback threshold {final_threshold:.3f} - found {reasonable_count} reasonable results")
        else:
            # Very poor results - don't show anything rather than showing irrelevant results
            final_threshold = 1.0  # Set impossibly high threshold to filter out all results
            logger.info(f"All results are poor quality (max score: {max(scores) if scores else 0:.3f}) - filtering out all results")
    
    # Log the decision
    max_score = max(scores) if scores else 0
    logger.info(f"Dynamic threshold for '{query}': {final_threshold:.3f} (max_score: {max_score:.3f}, total_results: {len(scores)})")
    
    return final_threshold 