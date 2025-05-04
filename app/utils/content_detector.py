"""
Content type detection module for Memora.
"""
import logging
import re
import requests
from urllib.parse import urlparse, parse_qs
from enum import Enum
from typing import Dict, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content type enumeration."""
    SOCIAL_MEDIA = "social_media"
    NEWS_ARTICLE = "news_article" 
    BLOG_POST = "blog_post"
    DOCUMENTATION = "documentation"
    ECOMMERCE = "ecommerce"
    VIDEO = "video"
    IMAGE = "image"
    UNKNOWN = "unknown"

class ContentDetector:
    """Content detector for various types of web content."""
    
    def __init__(self):
        """Initialize the content detector."""
        # Social media platform patterns
        self.social_media_patterns = [
            # TikTok - includes shortened URLs and various patterns
            {"platform": "tiktok", "domains": ["tiktok.com", "vt.tiktok.com", "vm.tiktok.com", "m.tiktok.com"], 
             "path_patterns": [r"/@[\w\.]+/video/\d+", r"/t/[\w]+", r"/v/[\w]+"]},
            # Instagram
            {"platform": "instagram", "domains": ["instagram.com", "www.instagram.com", "instagr.am"],
             "path_patterns": [r"/p/[\w-]+", r"/reel/[\w-]+", r"/stories/[\w\.]+", r"/tv/[\w-]+"]},
            # YouTube
            {"platform": "youtube", "domains": ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "youtube-nocookie.com"],
             "path_patterns": [r"/watch\?", r"/shorts/", r"/playlist", r"/c/", r"/channel/", r"/user/"]},
            # Facebook
            {"platform": "facebook", "domains": ["facebook.com", "www.facebook.com", "fb.com", "fb.watch", "m.facebook.com"],
             "path_patterns": [r"/[\w\.]+/posts/", r"/watch/", r"/story.php", r"/video.php", r"/events/"]},
            # LinkedIn
            {"platform": "linkedin", "domains": ["linkedin.com", "www.linkedin.com", "lnkd.in"],
             "path_patterns": [r"/posts/", r"/pulse/", r"/feed/update/", r"/in/"]},
            # Twitter/X
            {"platform": "twitter", "domains": ["twitter.com", "www.twitter.com", "t.co", "x.com", "www.x.com"],
             "path_patterns": [r"/[\w]+/status/", r"/i/web/"]},
            # Pinterest
            {"platform": "pinterest", "domains": ["pinterest.com", "www.pinterest.com", "pin.it"],
             "path_patterns": [r"/pin/", r"/[\w]+/[\w-]+/"]},
            # Reddit
            {"platform": "reddit", "domains": ["reddit.com", "www.reddit.com", "old.reddit.com", "redd.it"],
             "path_patterns": [r"/r/[\w]+/comments/", r"/comments/", r"/user/"]},
            # Threads
            {"platform": "threads", "domains": ["threads.net", "www.threads.net"],
             "path_patterns": [r"/@[\w\.]+", r"/t/[\w-]+"]}
        ]
        
        # News domains
        self.news_domains = [
            "nytimes.com", "washingtonpost.com", "bbc.com", "bbc.co.uk", "cnn.com", 
            "foxnews.com", "reuters.com", "bloomberg.com", "apnews.com", "npr.org",
            "theguardian.com", "economist.com", "wsj.com", "ft.com", "cnbc.com",
            "aljazeera.com", "news.yahoo.com", "news.google.com"
        ]
        
        # E-commerce domains
        self.ecommerce_domains = [
            "amazon", "ebay", "walmart", "etsy", "shopify", "alibaba", "aliexpress",
            "bestbuy", "target", "wayfair", "newegg", "homedepot", "ikea", "macys",
            "shop", "store", "buy", "product", "item"
        ]
        
        # Documentation domains
        self.documentation_domains = [
            "docs.", "documentation.", "help.", "support.", "manual.", "guide.",
            "readthedocs", "developer.", "dev.", "api.", "sdk."
        ]
        
        # Blog indicators
        self.blog_indicators = [
            "blog.", ".blog", "/blog", "article", "post", "/posts/", "medium.com",
            "wordpress", "blogger", "substack", "hashnode"
        ]
    
    def detect_content_type(self, url: str, fetch_headers: bool = True) -> Tuple[ContentType, Optional[str]]:
        """
        Detect the type of content from a URL.
        
        Args:
            url: The URL to detect content type for
            fetch_headers: Whether to make a HEAD request to check content type
            
        Returns:
            Tuple of ContentType and platform/subtype if applicable
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        
        # Quick check for known shortened domains that we know are social media
        if domain in ["vt.tiktok.com", "vm.tiktok.com"]:
            return ContentType.SOCIAL_MEDIA, "tiktok"
            
        if domain in ["t.co", "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "buff.ly"]:
            # Try to follow the redirect to get the actual URL
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.head(url, headers=headers, timeout=3, allow_redirects=False)
                if response.status_code in [301, 302, 303, 307, 308] and 'Location' in response.headers:
                    redirect_url = response.headers['Location']
                    logger.info(f"URL shortener detected, following redirect to: {redirect_url}")
                    # Recursively call this method with the new URL
                    return self.detect_content_type(redirect_url, fetch_headers)
            except Exception as e:
                logger.warning(f"Failed to follow redirect for shortened URL {url}: {str(e)}")
        
        # Check for social media
        social_media_result = self._check_social_media(parsed_url)
        if social_media_result:
            return ContentType.SOCIAL_MEDIA, social_media_result
            
        # Check for news site
        if any(news_domain in domain for news_domain in self.news_domains):
            return ContentType.NEWS_ARTICLE, None
            
        # Check for e-commerce
        if any(ecom_domain in domain for ecom_domain in self.ecommerce_domains):
            return ContentType.ECOMMERCE, None
            
        # Check for documentation
        if any(doc_domain in domain for doc_domain in self.documentation_domains):
            return ContentType.DOCUMENTATION, None
            
        # Check for blog
        if any(blog_ind in domain or blog_ind in path for blog_ind in self.blog_indicators):
            return ContentType.BLOG_POST, None
        
        # If headers should be fetched, check content type header
        if fetch_headers:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.head(url, headers=headers, timeout=3)
                
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'video' in content_type:
                    return ContentType.VIDEO, None
                elif 'image' in content_type:
                    return ContentType.IMAGE, None
                
            except Exception as e:
                logger.warning(f"Failed to fetch headers for {url}: {str(e)}")
        
        # Check URL for media indicators
        if re.search(r'\.(mp4|avi|mov|wmv|flv|mkv|webm)(\?|$)', url.lower()):
            return ContentType.VIDEO, None
        elif re.search(r'\.(jpg|jpeg|png|gif|svg|webp|bmp|tiff)(\?|$)', url.lower()):
            return ContentType.IMAGE, None
        
        # Default to unknown
        return ContentType.UNKNOWN, None
    
    def _check_social_media(self, parsed_url) -> Optional[str]:
        """
        Check if a URL is from a social media platform.
        
        Args:
            parsed_url: Parsed URL
            
        Returns:
            Platform name if it's a social media URL, None otherwise
        """
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        
        # Check against patterns
        for platform in self.social_media_patterns:
            if any(d in domain for d in platform["domains"]):
                if not platform["path_patterns"] or any(re.search(pattern, path) for pattern in platform["path_patterns"]):
                    return platform["platform"]
        
        # Check query parameters for social media URLs
        query_params = parse_qs(parsed_url.query)
        for param_values in query_params.values():
            for value in param_values:
                for platform in self.social_media_patterns:
                    if any(d in value for d in platform["domains"]):
                        return platform["platform"]
        
        # Additional checks for common social media URL patterns
        content_type_indicators = ["video", "photo", "image", "media", "post", "status", "reel", "story", "watch"]
        if any(indicator in path for indicator in content_type_indicators):
            path_segments = [seg for seg in path.split("/") if seg]
            if len(path_segments) >= 2 and any(len(seg) > 4 and not seg.isalpha() for seg in path_segments):
                # Can't determine specific platform but it looks like social media
                return "general_social"
                
        return None

# Create singleton instance
content_detector = ContentDetector() 