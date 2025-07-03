import os
import logging
import requests
from typing import Dict, List, Any, Tuple
import uuid
from datetime import datetime
import json
import re
from urllib.parse import urlparse, parse_qs

from sqlalchemy.orm import Session

from app.db.database import get_or_create_user, Item, SessionLocal
from app.utils.llm import analyze_content_with_llm, generate_embedding
from app.scrapers.web_scraper import scrape_website
from app.scrapers.social_scraper import scrape_social_media
from app.utils.content_detector import content_detector, ContentType

# Configure logging
logger = logging.getLogger(__name__)

# Predefined tag categories for content organization
STANDARD_TAG_CATEGORIES = [
    "technology", "programming", "science", "health", "business", 
    "finance", "education", "entertainment", "sports", "travel",
    "food", "fashion", "art", "design", "politics", "news",
    "environment", "history", "philosophy", "psychology",
    "productivity", "self-improvement", "career"
]

def is_social_media_url(url: str) -> bool:
    """
    Determine if a URL is from a social media platform using enhanced detection.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if the URL is from a social media platform, False otherwise
    """
    # Parse URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()
    
    # Updated pattern-based detection for social media platforms
    social_media_patterns = [
        # TikTok - includes shortened URLs and various patterns
        {"domain": ["tiktok.com", "vt.tiktok.com", "vm.tiktok.com", "m.tiktok.com"], 
         "path_patterns": [r"/@[\w\.]+/video/\d+", r"/t/[\w]+", r"/v/[\w]+"]}
        ,
        # Instagram
        {"domain": ["instagram.com", "www.instagram.com", "instagr.am"],
         "path_patterns": [r"/p/[\w-]+", r"/reel/[\w-]+", r"/stories/[\w\.]+", r"/tv/[\w-]+"]}
        ,
        # YouTube - Updated to handle youtu.be format
        {"domain": ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "youtube-nocookie.com"],
         "path_patterns": [r"/watch\?", r"/shorts/", r"/playlist", r"/c/", r"/channel/", r"/user/", r"/[\w-]+$"]}  # Added pattern for youtu.be/VIDEO_ID
        ,
        # Facebook - Updated to handle new share URL formats
        {"domain": ["facebook.com", "www.facebook.com", "fb.com", "fb.watch", "m.facebook.com"],
         "path_patterns": [r"/[\w\.]+/posts/", r"/watch/", r"/story\.php", r"/video\.php", r"/events/", r"/share/v/", r"/share/p/", r"/share/r/", r"/share/[\w]+/"]},  # Added share patterns including direct content ID format
        # LinkedIn
        {"domain": ["linkedin.com", "www.linkedin.com", "lnkd.in"],
         "path_patterns": [r"/posts/", r"/pulse/", r"/feed/update/", r"/in/"]}
        ,
        # Twitter/X
        {"domain": ["twitter.com", "www.twitter.com", "t.co", "x.com", "www.x.com"],
         "path_patterns": [r"/[\w]+/status/", r"/i/web/"]}
        ,
        # Pinterest
        {"domain": ["pinterest.com", "www.pinterest.com", "pin.it"],
         "path_patterns": [r"/pin/", r"/[\w]+/[\w-]+/"]}
        ,
        # Reddit
        {"domain": ["reddit.com", "www.reddit.com", "old.reddit.com", "redd.it"],
         "path_patterns": [r"/r/[\w]+/comments/", r"/comments/", r"/user/"]}
        ,
        # Threads
        {"domain": ["threads.net", "www.threads.net"],
         "path_patterns": [r"/@[\w\.]+", r"/t/[\w-]+"]}
    ]
    
    # Check for matches in domain + path patterns
    for platform in social_media_patterns:
        # First check if domain matches
        if any(d in domain for d in platform["domain"]):
            # If no specific path patterns or path matches a pattern, consider it a match
            if not platform["path_patterns"] or any(re.search(pattern, path) for pattern in platform["path_patterns"]):
                return True
    
    # Additional checks for ambiguous URLs
    
    # 1. Check for social media domains in query parameters (for shortened URLs)
    query_params = parse_qs(parsed_url.query)
    for param_values in query_params.values():
        for value in param_values:
            if any(social_platform["domain"][0] in value for social_platform in social_media_patterns):
                return True
    
    # 2. Check for content-type hints in URL
    content_type_indicators = ["video", "photo", "image", "media", "post", "status", "reel", "story", "watch"]
    if any(indicator in path for indicator in content_type_indicators):
        # Additional check for path structure typical of content platforms
        path_segments = [seg for seg in path.split("/") if seg]
        # Social media URLs often have a specific pattern of segments
        if len(path_segments) >= 2 and any(len(seg) > 4 and not seg.isalpha() for seg in path_segments):
            return True
    
    return False

def extract_content(url: str) -> Dict[str, Any]:
    """
    Extract content from a URL.
    
    Args:
        url: The URL to extract content from
        
    Returns:
        Dict containing extracted content
    """
    logger.info(f"Extracting content from URL: {url}")
    
    # Detect content type
    content_type, subtype = content_detector.detect_content_type(url)
    
    # Log detected content type
    logger.info(f"Detected content type: {content_type.value}, subtype: {subtype}")
    
    # Use appropriate scraper based on content type
    if content_type == ContentType.SOCIAL_MEDIA:
        logger.info(f"Identified as social media URL: {url}")
        content = scrape_social_media(url)
        
        # Check if social media scraping was successful
        if not content.get("success", False):
            logger.warning(f"Social media scraping failed: {content.get('error', 'Unknown error')}")
            # Try fallback to general website scraping
            logger.info("Attempting fallback to general website scraping")
            content = scrape_website(url)
            content["content_type"] = content_type.value
            content["scraping_note"] = "Fell back to general website scraping due to social media extraction failure"
        else:
            # Remove the success field as it's not needed downstream
            content.pop("success", None)
            content.pop("error", None)
        
        # Add metadata about the detected platform if available
        if subtype:
            content["platform"] = subtype
    else:
        logger.info(f"Identified as general website URL: {url}")
        content = scrape_website(url)
        # Add metadata about the detected content type
        content["content_type"] = content_type.value
    
    return content

def standardize_tags(tags: List[str]) -> List[str]:
    """
    Standardize tags by matching them to predefined categories when possible,
    while preserving unique tags that don't match any standard category.
    
    Args:
        tags: List of tags to standardize
        
    Returns:
        List of standardized tags
    """
    standardized_tags = []
    remaining_tags = []
    
    # Convert all tags to lowercase for matching
    lowercase_tags = [tag.lower() for tag in tags]
    
    # First pass: exact matches with standard categories
    for tag in lowercase_tags:
        if tag in STANDARD_TAG_CATEGORIES:
            if tag not in standardized_tags:
                standardized_tags.append(tag)
        else:
            remaining_tags.append(tag)
    
    # Second pass: partial matches with standard categories
    for tag in remaining_tags[:]:  # Use a copy to safely modify the original list
        matched = False
        for category in STANDARD_TAG_CATEGORIES:
            # Check if tag is a subset of a category or vice versa
            if tag in category or category in tag:
                if category not in standardized_tags:
                    standardized_tags.append(category)
                matched = True
                remaining_tags.remove(tag)
                break
    
    # Add remaining unique tags that didn't match any standard category
    standardized_tags.extend(remaining_tags)
    
    return standardized_tags

def extract_and_save_content(user_id: str, url: str) -> Dict[str, Any]:
    """
    Extract content from a URL and save it in the database.
    
    Args:
        user_id: User ID
        url: URL to extract content from
        
    Returns:
        Saved item
    """
    logger.info(f"Processing URL {url} for user {user_id}")
    
    # Detect content type before extraction
    content_type, subtype = content_detector.detect_content_type(url)
    content_type_value = content_type.value if content_type else "unknown"
    
    # Extract content from URL
    extracted_content = extract_content(url)
    
    # Check if the extracted content is a login page or access-restricted content
    title = extracted_content.get("title", "").lower()
    text = extracted_content.get("text", "").lower()
    platform = extracted_content.get("platform", "").lower()
    
    # Enhanced login detection - more comprehensive indicators
    login_indicators = [
        # Facebook-specific
        "log in to facebook",
        "log into facebook", 
        "facebook - log in or sign up",
        "facebook for social connections",
        "log in to facebook for social connections",
        "access your facebook account",
        "you must log in to continue",
        # General login indicators
        "login required",
        "access denied", 
        "authentication required",
        "please log in",
        "sign in to continue",
        "private content",
        "restricted access",
        "requires login",
        "sign up or log in",
        "create account or log in"
    ]
    
    # Check if this is a login/restricted page
    is_login_page = False
    detected_indicators = []
    
    # Check title for login indicators
    for indicator in login_indicators:
        if indicator in title:
            is_login_page = True
            detected_indicators.append(f"title: '{indicator}'")
    
    # Check text content for login indicators (first 500 chars for efficiency)
    if not is_login_page:
        text_sample = text[:500]
        for indicator in login_indicators:
            if indicator in text_sample:
                is_login_page = True
                detected_indicators.append(f"text: '{indicator}'")
                break
    
    # Additional check for generic login page patterns
    if not is_login_page:
        generic_login_patterns = [
            "connect and share with friends",
            "engage with their social network", 
            "access your.*account",
            "platform allows users to"
        ]
        import re
        for pattern in generic_login_patterns:
            if re.search(pattern, title) or re.search(pattern, text_sample):
                is_login_page = True
                detected_indicators.append(f"pattern: '{pattern}'")
                break
    
    # Log detection details for debugging
    if is_login_page:
        logger.info(f"Detected login/restricted access page for URL {url}")
        logger.info(f"Detection reasons: {', '.join(detected_indicators)}")
        logger.info(f"Title: '{extracted_content.get('title', '')}'")
        logger.info(f"Text sample: '{text[:200]}...'")
    
    # Don't save login pages or access-restricted content
    if is_login_page:
        return {
            "success": False,
            "error": "Content requires authentication or is access-restricted",
            "message": f"This {platform or 'content'} requires login or direct access to view. Please visit the URL directly.",
            "detected_indicators": detected_indicators  # For debugging
        }
    
    # Analyze content with LLM
    analysis = analyze_content_with_llm(extracted_content)
    
    # Standardize the tags
    analysis["tags"] = standardize_tags(analysis["tags"])
    
    # Generate embedding
    embedding = generate_embedding(
        analysis["description"] + " " + 
        extracted_content.get("title", "") + " " + 
        " ".join(analysis["tags"])
    )
    
    # Save to database
    db = SessionLocal()
    try:
        # Get or create user
        get_or_create_user(db, user_id)
        
        # Create item
        item = Item(
            user_id=user_id,
            url=url,
            title=extracted_content.get("title", "Untitled"),
            description=analysis["description"],
            tags=analysis["tags"],
            embedding=embedding,
            content_type=content_type_value,
            platform=subtype
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        # Convert item to dict for response
        return {
            "id": item.id,
            "user_id": item.user_id,
            "url": item.url,
            "title": item.title,
            "description": item.description,
            "tags": item.tags,
            "timestamp": item.timestamp,
            "content_type": item.content_type,
            "platform": item.platform
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving content to database: {str(e)}")
        raise
    finally:
        db.close()

def extract_content_from_url(url: str) -> Dict[str, Any]:
    """
    Extract content from a URL without saving to database.
    
    Args:
        url: The URL to extract content from
        
    Returns:
        Dict containing extracted content
    """
    logger.info(f"Extracting content from URL: {url}")
    
    try:
        # Detect content type
        content_type, subtype = content_detector.detect_content_type(url)
        
        # Log detected content type
        logger.info(f"Detected content type: {content_type.value}, subtype: {subtype}")
        
        # Use appropriate scraper based on content type
        if content_type == ContentType.SOCIAL_MEDIA:
            logger.info(f"Identified as social media URL: {url}")
            content = scrape_social_media(url)
            
            # Check if social media scraping was successful
            if not content.get("success", False):
                logger.warning(f"Social media scraping failed: {content.get('error', 'Unknown error')}")
                # Try fallback to general website scraping
                logger.info("Attempting fallback to general website scraping")
                content = scrape_website(url)
                content["content_type"] = content_type.value
                content["scraping_note"] = "Fell back to general website scraping due to social media extraction failure"
            else:
                # Remove the success field as it's not needed downstream
                content.pop("success", None)
                content.pop("error", None)
            
            # Add metadata about the detected platform if available
            if subtype:
                content["platform"] = subtype
        else:
            logger.info(f"Identified as general website URL: {url}")
            content = scrape_website(url)
            # Add metadata about the detected content type
            content["content_type"] = content_type.value
        
        return content
        
    except Exception as e:
        logger.error(f"Error extracting content from URL {url}: {str(e)}")
        return {
            "title": "Error extracting content",
            "text": f"Failed to extract content from {url}",
            "error": str(e)
        } 