import logging
import json
import os
import tempfile
import subprocess
from typing import Dict, Any, List
import re
from urllib.parse import urlparse
import sys
import requests
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.scrapers.tiktok_enhanced import extract_tiktok_enhanced

# Configure logging
logger = logging.getLogger(__name__)

def create_robust_session() -> requests.Session:
    """Create a robust requests session with proper retry logic and connection pooling."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    # Configure adapter
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=1,  # Limit pool connections to avoid socket exhaustion
        pool_maxsize=1,      # Limit pool size to avoid socket exhaustion
        pool_block=True      # Block if pool is full instead of creating new connections
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def scrape_social_media(url: str) -> Dict[str, Any]:
    """
    Extract content from a social media URL using yt-dlp.
    
    Args:
        url: Social media URL to scrape
        
    Returns:
        Dictionary with extracted content
    """
    try:
        logger.info(f"Starting social media scraping for: {url}")
        
        # Detect platform
        platform = extract_platform_name(url)
        logger.info(f"Detected platform: {platform}")
        
        # Add random delay to avoid rate limiting
        delay = random.uniform(1, 3)
        logger.info(f"Adding {delay:.1f}s delay before scraping...")
        time.sleep(delay)
        
        # Initialize variables
        success = False
        metadata = {}
        
        # Create temp directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Check if yt-dlp is installed and accessible
            try:
                version_cmd = ["yt-dlp", "--version"]
                version_process = subprocess.run(version_cmd, capture_output=True, text=True, timeout=5)
                if version_process.returncode == 0:
                    logger.info(f"Using yt-dlp version: {version_process.stdout.strip()}")
                else:
                    logger.warning("yt-dlp version check failed, but continuing anyway")
            except Exception as e:
                logger.error(f"Error checking yt-dlp version: {str(e)}")
                
            # Platform-specific handling
            if platform == "TikTok":
                # Use enhanced TikTok scraper for both videos and photo posts
                logger.info("Using enhanced TikTok scraper")
                result = extract_tiktok_enhanced(url)
                return result
            elif platform == "Facebook":
                # For Facebook, skip yt-dlp attempts due to connection issues and go straight to alternatives
                logger.info("Facebook detected - using alternative extraction methods")
                
                # Try Facebook-specific extraction methods
                try:
                    result = extract_facebook_content_robust(url)
                    if result:
                        result["success"] = True
                        return result
                except Exception as fb_error:
                    logger.warning(f"Facebook extraction failed: {str(fb_error)}")
                
                # Try Facebook oEmbed API
                try:
                    result = extract_facebook_oembed(url)
                    if result:
                        result["success"] = True
                        return result
                except Exception as oembed_error:
                    logger.warning(f"Facebook oEmbed failed: {str(oembed_error)}")
                
                # Try extracting info from URL
                try:
                    result = extract_facebook_info_from_url(url)
                    if result:
                        result["success"] = True
                        return result
                except Exception as info_error:
                    logger.warning(f"Facebook info extraction failed: {str(info_error)}")
                
            elif platform == "Instagram":
                # For Instagram, try robust extraction first
                try:
                    result = extract_instagram_content_robust(url)
                    if result:
                        result["success"] = True
                        return result
                except Exception as ig_error:
                    logger.warning(f"Instagram robust extraction failed: {str(ig_error)}")
                
                # If that fails, try yt-dlp as backup
                try:
                    simple_cmd = [
                        "yt-dlp",
                        "--skip-download",
                        "--write-info-json",
                        "--no-warnings",
                        "--ignore-errors",
                        "--socket-timeout", "15",
                        "--retries", "1",
                        "-o", f"{temp_dir}/%(id)s",
                        url
                    ]
                    
                    logger.info(f"Trying yt-dlp as backup for Instagram")
                    process = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=30)
                    
                    if process.returncode == 0:
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                        if json_files:
                            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            success = True
                            logger.info("Successfully extracted Instagram content with yt-dlp backup")
                    else:
                        logger.warning(f"Instagram yt-dlp backup failed: {str(e)}")
                except Exception as e:
                    logger.warning(f"Instagram yt-dlp backup failed: {str(e)}")
                
                # If yt-dlp also fails, try URL info extraction
                if not success:
                    try:
                        result = extract_instagram_info_from_url(url)
                        if result:
                            result["success"] = True
                            return result
                    except Exception as info_error:
                        logger.warning(f"Instagram info extraction failed: {str(info_error)}")
            else:
                # For other platforms, try yt-dlp with reduced attempts
                # Add a random delay before starting to avoid rate limiting
                initial_delay = random.uniform(1, 2)
                time.sleep(initial_delay)
                
                # Try only one simplified yt-dlp approach to avoid socket exhaustion
                try:
                    # Clean up temp directory
                    for f in os.listdir(temp_dir):
                        if f.endswith('.info.json'):
                            os.remove(os.path.join(temp_dir, f))
                    
                    # General command for other platforms
                    simple_cmd = [
                        "yt-dlp",
                        "--skip-download",
                        "--write-info-json",
                        "--no-warnings",
                        "--ignore-errors",
                        "--socket-timeout", "15",
                        "--retries", "1",
                        "-o", f"{temp_dir}/%(id)s",
                        url
                    ]
                    logger.info(f"Running simplified yt-dlp command for {platform}")
                    
                    process = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=30)
                    
                    if process.returncode == 0:
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                        if json_files:
                            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            success = True
                            logger.info(f"Successfully extracted {platform} metadata with simplified command")
                    else:
                        logger.warning(f"Simplified yt-dlp failed: {process.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"{platform} yt-dlp command timed out")
                except Exception as e:
                    logger.warning(f"{platform} yt-dlp command failed: {str(e)}")
                
                # If yt-dlp failed, try alternative methods
                if not success:
                    logger.info("yt-dlp failed, trying alternative extraction methods")
                    
                    # For YouTube, try oEmbed API
                    if platform == "YouTube":
                        result = extract_youtube_content(url, temp_dir, force_alternative=True)
                        if result:
                            result["success"] = True
                            return result
                    
                    # For other platforms, try basic web scraping
                    alternative_result = try_alternative_extraction(url, platform)
                    if alternative_result:
                        alternative_result["success"] = True
                        return alternative_result

            # If we have successfully extracted metadata, process it
            if metadata:
                # Extract relevant information based on platform
                title = metadata.get('title', 'Untitled')
                description = metadata.get('description', '')
                
                # Extract uploader/creator information
                uploader = metadata.get('uploader', '')
                uploader_url = metadata.get('uploader_url', '')
                
                # Get thumbnail URLs
                thumbnails = []
                if 'thumbnails' in metadata and isinstance(metadata['thumbnails'], list):
                    thumbnails = [t.get('url', '') for t in metadata['thumbnails'] if 'url' in t]
                elif 'thumbnail' in metadata:
                    thumbnails = [metadata['thumbnail']]
                
                # Format the extracted text
                text = f"Title: {title}\n"
                text += f"Creator: {uploader}\n"
                text += f"Description: {description}\n"
                
                # Add hashtags if available
                hashtags = metadata.get('tags', [])
                if hashtags:
                    text += f"Hashtags: {', '.join(hashtags)}\n"
                
                # Add platform-specific metadata
                if platform in ["TikTok", "YouTube", "Instagram", "Twitter", "Facebook"]:
                    # Include view count and like count if available for all platforms
                    view_count = metadata.get('view_count', 'Unknown')
                    like_count = metadata.get('like_count', 'Unknown')
                    if view_count != 'Unknown':
                        text += f"Views: {view_count}\n"
                    if like_count != 'Unknown':
                        text += f"Likes: {like_count}\n"
                
                return {
                    "success": True,
                    "title": title,
                    "text": text,
                    "description": description,  # For LLM analysis
                    "meta_description": description,
                    "uploader": uploader,
                    "uploader_url": uploader_url,
                    "creator": uploader,  # Alternative field name
                    "images": thumbnails[:5],  # Limit to first 5 thumbnails
                    "url": url,
                    "platform": platform,
                    "duration": metadata.get('duration'),
                    "view_count": metadata.get('view_count'),
                    "like_count": metadata.get('like_count'),
                    "similarity_score": 1.0,  # For search compatibility
                    "raw_metadata": {
                        "tags": metadata.get('tags', []),
                        "view_count": metadata.get('view_count'),
                        "like_count": metadata.get('like_count'),
                        "comment_count": metadata.get('comment_count'),
                        "upload_date": metadata.get('upload_date')
                    }
                }
            
            # Complete failure
            logger.error("All extraction methods failed")
            return {
                "success": False,
                "error": "All extraction methods failed. The content might be private, geo-blocked, or the platform has anti-scraping measures.",
                "title": "Failed to extract",
                "text": f"Failed to extract content from {url}",
                "meta_description": "",
                "uploader": "",
                "uploader_url": "",
                "images": [],
                "url": url,
                "platform": platform,
                "raw_metadata": {}
            }
    
    except Exception as e:
        logger.error(f"Error scraping social media URL {url}: {str(e)}")
        # Return failure information
        return {
            "success": False,
            "error": str(e),
            "title": "Failed to extract",
            "text": f"Failed to extract content from {url}. Error: {str(e)}",
            "meta_description": "",
            "uploader": "",
            "uploader_url": "",
            "images": [],
            "url": url,
            "platform": extract_platform_name(urlparse(url).netloc.lower()),
            "raw_metadata": {}
        }

def extract_facebook_content_robust(url: str) -> Dict[str, Any]:
    """
    Robust Facebook content extraction with proper connection handling.
    
    Args:
        url: Facebook URL to extract content from
        
    Returns:
        Dictionary with extracted content or None if failed
    """
    try:
        logger.info(f"Attempting robust Facebook extraction for: {url}")
        
        # Minimal delay to avoid rate limiting while keeping response time reasonable
        delay = random.uniform(1, 2)
        logger.info(f"Waiting {delay:.1f} seconds before attempting Facebook extraction...")
        time.sleep(delay)
        
        # Create a robust session
        session = create_robust_session()
        
        # Try Facebook Graph API approach (if we had an app token)
        # Since we don't have that, try a browser-like request with mobile URL
        try:
            mobile_url = url.replace("www.facebook.com", "m.facebook.com")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close",  # Use connection close to avoid pool issues
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            
            session.headers.update(headers)
            
            logger.info(f"Attempting mobile Facebook extraction: {mobile_url}")
            response = session.get(mobile_url, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to extract meaningful content
                title = ""
                description = ""
                author = ""
                
                # Look for Open Graph meta tags first
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title.get('content', '').strip()
                
                og_description = soup.find('meta', property='og:description')
                if og_description and og_description.get('content'):
                    description = og_description.get('content', '').strip()
                
                # Try to get author/page info
                og_site = soup.find('meta', property='og:site_name')
                if og_site and og_site.get('content'):
                    author = og_site.get('content', '').strip()
                
                # If we didn't get good content from OG tags, try content extraction
                if not title or title in ["Facebook", "Facebook - Log In or Sign Up"]:
                    # Try to find post content
                    content_selectors = [
                        '[data-testid="post_message"]',
                        '.userContent',
                        '.story_body_container',
                        'div[role="article"]',
                        '.mbs._6m6'
                    ]
                    
                    for selector in content_selectors:
                        element = soup.select_one(selector)
                        if element:
                            extracted_text = element.get_text(strip=True)
                            if extracted_text and len(extracted_text) > 10:
                                if not title or title in ["Facebook", "Facebook - Log In or Sign Up"]:
                                    title = extracted_text[:100] + ("..." if len(extracted_text) > 100 else "")
                                if not description:
                                    description = extracted_text
                                break
                
                # Check if we got meaningful content
                if title and title not in ["Facebook", "Facebook - Log In or Sign Up", ""] and len(title) > 5:
                    # Create detailed response
                    text = f"Title: {title}\n"
                    if author:
                        text += f"Author/Page: {author}\n"
                    if description and description != title:
                        text += f"Content: {description}\n"
                    text += f"Source: Facebook\n"
                    
                    session.close()
                    
                    return {
                        "title": title,
                        "text": text,
                        "description": description,
                        "meta_description": description,
                        "uploader": author,
                        "uploader_url": "",
                        "creator": author,
                        "images": [],
                        "url": url,
                        "platform": "Facebook",
                        "duration": None,
                        "view_count": None,
                        "like_count": None,
                        "raw_metadata": {
                            "extraction_method": "mobile_browser_extraction",
                            "mobile_url": mobile_url
                        }
                    }
                else:
                    logger.warning(f"No meaningful content extracted from Facebook mobile page. Title: '{title}'")
                    
                    # Check if this is a login page that should not be processed
                    if title in ["Facebook", "Facebook - Log In or Sign Up", "Log in to Facebook to Connect with Friends and Family", "Log Into Facebook"] or "log in" in title.lower() or "login" in title.lower():
                        logger.info("Facebook page requires login - not processing this content")
                        session.close()
                        return None
            else:
                logger.warning(f"Facebook mobile request failed with status: {response.status_code}")
        
        except Exception as mobile_error:
            logger.warning(f"Mobile Facebook extraction failed: {str(mobile_error)}")
        
        finally:
            session.close()
        
        # Quick transition to next attempt
        time.sleep(random.uniform(0.5, 1.5))
        
        # If mobile extraction failed, try a different approach - desktop with different headers
        try:
            session = create_robust_session()
            
            desktop_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close",
                "Cache-Control": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
            
            session.headers.update(desktop_headers)
            
            logger.info(f"Attempting desktop Facebook extraction: {url}")
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract content using similar method
                title = ""
                description = ""
                
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title.get('content', '').strip()
                
                og_description = soup.find('meta', property='og:description')
                if og_description and og_description.get('content'):
                    description = og_description.get('content', '').strip()
                
                if title and title not in ["Facebook", "Facebook - Log In or Sign Up", ""] and len(title) > 5:
                    text = f"Title: {title}\n"
                    if description and description != title:
                        text += f"Description: {description}\n"
                    text += f"Source: Facebook\n"
                    
                    session.close()
                    
                    return {
                        "title": title,
                        "text": text,
                        "description": description,
                        "meta_description": description,
                        "uploader": "",
                        "uploader_url": "",
                        "creator": "",
                        "images": [],
                        "url": url,
                        "platform": "Facebook",
                        "duration": None,
                        "view_count": None,
                        "like_count": None,
                        "raw_metadata": {
                            "extraction_method": "desktop_browser_extraction"
                        }
                    }
                else:
                    # Check if this is a login page that should not be processed
                    if title in ["Facebook", "Facebook - Log In or Sign Up", "Log in to Facebook to Connect with Friends and Family", "Log Into Facebook"] or (title and ("log in" in title.lower() or "login" in title.lower())):
                        logger.info("Facebook page requires login - not processing this content")
                        session.close()
                        return None
            
        except Exception as desktop_error:
            logger.warning(f"Desktop Facebook extraction failed: {str(desktop_error)}")
        
        finally:
            session.close()
        
        return None
        
    except Exception as e:
        logger.error(f"Robust Facebook extraction failed: {str(e)}")
        return None

def extract_youtube_content(url: str, temp_dir: str, force_alternative: bool = False) -> Dict[str, Any]:
    """
    Extract content from a YouTube URL using specialized methods.
    
    Args:
        url: YouTube URL to scrape
        temp_dir: Temporary directory for output
        force_alternative: Whether to force using alternative method
        
    Returns:
        Dictionary with extracted content or None if failed
    """
    try:
        # Extract video ID from URL
        video_id = None
        if "youtube.com/watch" in url:
            query = urlparse(url).query
            params = dict(param.split('=') for param in query.split('&') if '=' in param)
            video_id = params.get('v')
        elif "youtu.be/" in url:
            video_id = urlparse(url).path.strip('/')
        
        if not video_id:
            logger.error("Could not extract YouTube video ID")
            return None
        
        logger.info(f"Extracted YouTube video ID: {video_id}")
        
        # Try using youtube-dl with specific options for YouTube
        if not force_alternative:
            youtube_cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-info-json",
                "--no-warnings",
                "--ignore-errors",
                "--youtube-skip-dash-manifest",
                "--extractor-args", "youtube:player_client=web",
                "--extractor-args", "youtube:player_skip=webpage",
                "--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "-o", f"{temp_dir}/%(id)s",
                url
            ]
            
            logger.info(f"Running specialized YouTube command: {' '.join(youtube_cmd)}")
            process = subprocess.run(youtube_cmd, capture_output=True, text=True)
            
            # Check if we got a JSON file
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
            if json_files:
                with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check if we got useful metadata
                if metadata.get('title') != 'Untitled' and metadata.get('description'):
                    logger.info("Successfully extracted YouTube metadata using specialized command")
                    
                    # Format the data as needed
                    title = metadata.get('title', 'Untitled')
                    description = metadata.get('description', '')
                    uploader = metadata.get('uploader', '')
                    uploader_url = metadata.get('uploader_url', '')
                    
                    thumbnails = []
                    if 'thumbnails' in metadata and isinstance(metadata['thumbnails'], list):
                        thumbnails = [t.get('url', '') for t in metadata['thumbnails'] if 'url' in t]
                    elif 'thumbnail' in metadata:
                        thumbnails = [metadata['thumbnail']]
                    
                    text = f"Title: {title}\n"
                    text += f"Creator: {uploader}\n"
                    text += f"Description: {description}\n"
                    
                    hashtags = metadata.get('tags', [])
                    if hashtags:
                        text += f"Hashtags: {', '.join(hashtags)}\n"
                    
                    view_count = metadata.get('view_count', 'Unknown')
                    like_count = metadata.get('like_count', 'Unknown')
                    if view_count != 'Unknown':
                        text += f"Views: {view_count}\n"
                    if like_count != 'Unknown':
                        text += f"Likes: {like_count}\n"
                    
                    return {
                        "title": title,
                        "text": text,
                        "meta_description": description,
                        "uploader": uploader,
                        "uploader_url": uploader_url,
                        "images": thumbnails[:5],
                        "url": url,
                        "platform": "YouTube",
                        "raw_metadata": {
                            "tags": metadata.get('tags', []),
                            "view_count": metadata.get('view_count'),
                            "like_count": metadata.get('like_count'),
                            "comment_count": metadata.get('comment_count'),
                            "upload_date": metadata.get('upload_date')
                        }
                    }
        
        # Alternative method: Use YouTube API or scrape directly
        logger.info("Trying alternative YouTube extraction method")
        
        # Try to get basic info from YouTube oEmbed API
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        try:
            response = requests.get(oembed_url, timeout=10)
            if response.status_code == 200:
                oembed_data = response.json()
                title = oembed_data.get('title', 'Untitled')
                author = oembed_data.get('author_name', '')
                
                # Get thumbnail
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                
                # Try to get more info with a simple metadata request
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # Create a basic response
                text = f"Title: {title}\n"
                text += f"Creator: {author}\n"
                
                return {
                    "title": title,
                    "text": text,
                    "meta_description": "",
                    "uploader": author,
                    "uploader_url": f"https://www.youtube.com/channel/{oembed_data.get('channel_id', '')}",
                    "images": [thumbnail_url],
                    "url": url,
                    "platform": "YouTube",
                    "raw_metadata": {
                        "tags": [],
                        "view_count": None,
                        "like_count": None,
                        "comment_count": None,
                        "upload_date": None
                    }
                }
        except Exception as e:
            logger.warning(f"Error in YouTube oEmbed API: {str(e)}")
        
        # If we got here, we couldn't extract the data
        return None
    
    except Exception as e:
        logger.error(f"Error in YouTube extraction: {str(e)}")
        return None

def extract_platform_name(domain: str) -> str:
    """
    Extract the social media platform name from a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        Platform name
    """
    if "tiktok.com" in domain:
        return "TikTok"
    elif "instagram.com" in domain:
        return "Instagram"
    elif "youtube.com" in domain or "youtu.be" in domain:
        return "YouTube"
    elif "facebook.com" in domain or "fb.com" in domain:
        return "Facebook"
    elif "linkedin.com" in domain:
        return "LinkedIn"
    elif "pinterest.com" in domain:
        return "Pinterest"
    elif "twitter.com" in domain or "x.com" in domain:
        return "Twitter"
    elif "reddit.com" in domain:
        return "Reddit"
    elif "threads.net" in domain:
        return "Threads"
    elif "vimeo.com" in domain:
        return "Vimeo"
    elif "dailymotion.com" in domain:
        return "Dailymotion"
    elif "twitch.tv" in domain:
        return "Twitch"
    elif "snapchat.com" in domain:
        return "Snapchat"
    elif "tumblr.com" in domain:
        return "Tumblr"
    else:
        return "Social Media"

def extract_facebook_oembed(url: str) -> Dict[str, Any]:
    """
    Extract content from a Facebook URL using oEmbed API.
    
    Args:
        url: Facebook URL to scrape
        
    Returns:
        Dictionary with extracted content or None if failed
    """
    try:
        logger.info(f"Trying Facebook oEmbed API for: {url}")
        
        # Facebook oEmbed endpoint
        oembed_url = f"https://www.facebook.com/plugins/post/oembed.json/?url={url}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        
        # Try multiple times with different delays
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    logger.info(f"Retrying Facebook oEmbed API (attempt {attempt + 1}/{max_attempts}) after {delay:.1f}s delay")
                    time.sleep(delay)
                
                # Use session for better connection handling
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(oembed_url, timeout=15)
                session.close()
                
                if response.status_code == 200:
                    oembed_data = response.json()
                    
                    # Extract available information
                    title = oembed_data.get('title', 'Facebook Post')
                    author = oembed_data.get('author_name', '')
                    author_url = oembed_data.get('author_url', '')
                    html_content = oembed_data.get('html', '')
                    
                    # Try to extract more info from the HTML if available
                    description = ""
                    if html_content:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        # Look for text content in the embedded HTML
                        text_elements = soup.find_all(text=True)
                        description = ' '.join([t.strip() for t in text_elements if t.strip()])
                    
                    # Only return if we got meaningful content
                    if title and title not in ['Facebook Post', 'Facebook', '']:
                        # Create response
                        text = f"Title: {title}\n"
                        if author:
                            text += f"Author: {author}\n"
                        if description:
                            text += f"Content: {description}\n"
                        
                        return {
                            "title": title,
                            "text": text,
                            "description": description,
                            "meta_description": description,
                            "uploader": author,
                            "uploader_url": author_url,
                            "creator": author,
                            "images": [],  # oEmbed doesn't typically include images for Facebook
                            "url": url,
                            "platform": "Facebook",
                            "duration": None,
                            "view_count": None,
                            "like_count": None,
                            "raw_metadata": {
                                "oembed_data": oembed_data,
                                "extraction_method": "oembed_api"
                            }
                        }
                    else:
                        logger.warning(f"Facebook oEmbed returned generic/empty title: {title}")
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Facebook oEmbed API request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == max_attempts - 1:  # Last attempt
                    break
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Facebook oEmbed API returned invalid JSON (attempt {attempt + 1}): {str(e)}")
                if attempt == max_attempts - 1:  # Last attempt
                    break
                continue
            except Exception as e:
                logger.warning(f"Error processing Facebook oEmbed response (attempt {attempt + 1}): {str(e)}")
                if attempt == max_attempts - 1:  # Last attempt
                    break
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error in Facebook oEmbed extraction: {str(e)}")
        return None

def extract_facebook_info_from_url(url: str) -> Dict[str, Any]:
    """
    Extract basic information from Facebook URL structure when network methods fail.
    
    Args:
        url: Facebook URL
        
    Returns:
        Dictionary with basic extracted info or None
    """
    try:
        logger.info(f"Trying URL-based Facebook info extraction for: {url}")
        
        # Parse different Facebook URL patterns
        content_type = ""
        content_description = ""
        
        if "/share/v/" in url:
            # New video share URL format
            content_type = "Facebook Video"
            content_description = "Video content shared on Facebook - unable to extract specific details due to Facebook's privacy settings."
        elif "/share/p/" in url:
            # New post share URL format
            content_type = "Facebook Post"
            content_description = "Text/image post shared on Facebook - unable to extract specific content due to Facebook's privacy restrictions."
        elif "/share/r/" in url:
            # Share URL format (reel/story)
            content_type = "Facebook Reel"
            content_description = "Short-form video content (Reel) shared on Facebook - unable to extract specific details due to platform restrictions."
        elif "/share/" in url and re.search(r"/share/[\w]+/", url):
            # Generic share URL format with direct content ID
            content_type = "Facebook Content"
            content_description = "Facebook content shared via link - unable to extract specific details due to Facebook's privacy restrictions."
        elif "/posts/" in url:
            # Direct post URL
            content_type = "Facebook Post"
            content_description = "Facebook post - unable to extract specific content due to privacy settings."
        elif "/watch/" in url or "/video/" in url:
            # Video URL
            content_type = "Facebook Video"
            content_description = "Video posted on Facebook - unable to extract specific details due to platform restrictions."
        elif "/events/" in url:
            # Event URL
            content_type = "Facebook Event"
            content_description = "Facebook event listing - unable to extract specific details due to privacy settings."
        elif "/photo/" in url or "/photos/" in url:
            # Photo URL
            content_type = "Facebook Photo"
            content_description = "Photo shared on Facebook - unable to extract specific details due to platform restrictions."
        else:
            # Generic Facebook content
            content_type = "Facebook Content"
            content_description = "Facebook content - unable to extract specific details due to platform restrictions."
        
        # Extract ID from URL if possible
        url_id = ""
        page_info = ""
        
        if "/share/" in url:
            # Extract ID from share URLs - handle both typed (v/, p/, r/) and direct (/content_id/) formats
            parts = url.split("/")
            for i, part in enumerate(parts):
                if part == "share" and i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if next_part in ["v", "p", "r"] and i + 2 < len(parts):
                        # Typed format: /share/v/ID or /share/p/ID or /share/r/ID
                        url_id = parts[i + 2].split("?")[0]  # Remove query parameters
                        break
                    elif next_part not in ["v", "p", "r"] and next_part:
                        # Direct format: /share/ID
                        url_id = next_part.split("?")[0]  # Remove query parameters
                        break
        
        # Try to extract page/user info from URL
        if "facebook.com/" in url:
            url_parts = url.split("facebook.com/")
            if len(url_parts) > 1:
                path_part = url_parts[1].split("/")[0]
                if path_part and path_part not in ["share", "watch", "video", "photo", "photos", "posts", "events"]:
                    page_info = f"From page/user: {path_part}"
        
        # Create a more informative title based on the content type and ID
        if url_id:
            title = f"{content_type} (ID: {url_id})"
        else:
            title = content_type
        
        # Create comprehensive description
        full_description = content_description
        if page_info:
            full_description += f" {page_info}."
        
        # Add helpful note
        helpful_note = "Note: Facebook restricts automated content extraction. To view the actual content, please click the link to open in Facebook."
        
        # Create detailed text
        text = f"Title: {title}\n"
        text += f"Content Type: {content_type}\n"
        text += f"Description: {full_description}\n"
        if url_id:
            text += f"Content ID: {url_id}\n"
        if page_info:
            text += f"{page_info}\n"
        text += f"Platform: Facebook\n"
        text += f"URL: {url}\n"
        text += f"{helpful_note}\n"
        
        return {
            "title": title,
            "text": text,
            "description": full_description,
            "meta_description": full_description,
            "uploader": page_info.replace("From page/user: ", "") if page_info else "",
            "uploader_url": "",
            "creator": page_info.replace("From page/user: ", "") if page_info else "",
            "images": [],
            "url": url,
            "platform": "Facebook",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "is_fallback_extraction": True,  # Flag to indicate this is a fallback
            "extraction_note": helpful_note,
            "raw_metadata": {
                "extraction_method": "url_pattern_analysis",
                "content_type": content_type,
                "content_id": url_id,
                "page_info": page_info,
                "note": "Facebook content extraction limited due to platform restrictions"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Facebook URL analysis: {str(e)}")
        return None

def try_alternative_extraction(url: str, platform: str) -> Dict[str, Any]:
    """
    Try alternative extraction methods when yt-dlp fails.
    
    Args:
        url: URL to extract from
        platform: Platform name
        
    Returns:
        Dictionary with extracted content or None
    """
    try:
        logger.info(f"Trying alternative extraction for {platform}")
        
        # Add delay before alternative extraction
        time.sleep(random.uniform(2, 5))
        
        # Platform-specific headers and approaches
        if platform == "Facebook":
            # Facebook-specific alternative extraction with better error handling
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            }
            
            # Try mobile Facebook URL transformation
            mobile_url = url.replace("www.facebook.com", "m.facebook.com")
            logger.info(f"Trying mobile Facebook URL: {mobile_url}")
            
            try:
                # Use session for better connection handling
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(mobile_url, timeout=20, allow_redirects=True)
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Facebook mobile-specific extraction
                    title = ""
                    description = ""
                    
                    # Try various Facebook-specific selectors
                    title_selectors = [
                        'meta[property="og:title"]',
                        'meta[name="twitter:title"]',
                        'title',
                        '[data-testid="post_message"]',
                        '.story_body_container',
                    ]
                    
                    for selector in title_selectors:
                        element = soup.select_one(selector)
                        if element:
                            if element.name == 'meta':
                                title = element.get('content', '')
                            else:
                                title = element.get_text(strip=True)
                            if title and title != "Facebook":
                                break
                    
                    # Try to get description
                    desc_selectors = [
                        'meta[property="og:description"]',
                        'meta[name="description"]',
                        'meta[name="twitter:description"]',
                        '[data-testid="post_message"]',
                        '.userContent',
                    ]
                    
                    for selector in desc_selectors:
                        element = soup.select_one(selector)
                        if element:
                            if element.name == 'meta':
                                description = element.get('content', '')
                            else:
                                description = element.get_text(strip=True)
                            if description:
                                break
                    
                    # Try to get thumbnail
                    thumbnails = []
                    og_image = soup.find('meta', property='og:image')
                    if og_image:
                        thumbnails.append(og_image.get('content', ''))
                    
                    if title and title not in ["Facebook", "Facebook - Log In or Sign Up"]:
                        text = f"Title: {title}\n"
                        if description:
                            text += f"Description: {description}\n"
                        
                        return {
                            "title": title,
                            "text": text,
                            "description": description,
                            "meta_description": description,
                            "uploader": "",
                            "uploader_url": "",
                            "creator": "",
                            "images": thumbnails,
                            "url": url,
                            "platform": platform,
                            "duration": None,
                            "view_count": None,
                            "like_count": None,
                            "raw_metadata": {
                                "extraction_method": "mobile_scraping"
                            }
                        }
                session.close()
            except Exception as fb_error:
                logger.warning(f"Facebook mobile extraction failed: {str(fb_error)}")
        
        elif platform == "TikTok":
            # TikTok videos should be handled by yt-dlp in the main flow
            # Photo posts are already handled separately with clear error message
            # This fallback is only reached if yt-dlp fails for videos
            logger.warning("TikTok extraction reached alternative method - yt-dlp likely failed")
            return None
        
        # General approach for other platforms or as fallback
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        try:
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to extract basic information from meta tags
                title = ""
                description = ""
                
                # Try Open Graph meta tags
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '')
                
                og_description = soup.find('meta', property='og:description')
                if og_description:
                    description = og_description.get('content', '')
                
                # Try standard meta tags if OG tags not found
                if not title:
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                
                if not description:
                    desc_tag = soup.find('meta', attrs={'name': 'description'})
                    if desc_tag:
                        description = desc_tag.get('content', '')
                
                # Try to get thumbnail
                thumbnails = []
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    thumbnails.append(og_image.get('content', ''))
                
                if title and title != "Untitled":
                    text = f"Title: {title}\n"
                    if description:
                        text += f"Description: {description}\n"
                    
                    return {
                        "title": title,
                        "text": text,
                        "description": description,
                        "meta_description": description,
                        "uploader": "",
                        "uploader_url": "",
                        "creator": "",
                        "images": thumbnails,
                        "url": url,
                        "platform": platform,
                        "duration": None,
                        "view_count": None,
                        "like_count": None,
                        "raw_metadata": {
                            "extraction_method": "web_scraping"
                        }
                    }
                else:
                    # Check if this is a login page that should not be processed
                    if title in ["Facebook", "Facebook - Log In or Sign Up", "Log in to Facebook to Connect with Friends and Family", "Log Into Facebook"] or (title and ("log in" in title.lower() or "login" in title.lower())):
                        logger.info("Facebook page requires login - not processing this content")
                        session.close()
                        return None
            session.close()
        except Exception as general_error:
            logger.warning(f"General web scraping failed: {str(general_error)}")
        
        return None
        
    except Exception as e:
        logger.warning(f"Alternative extraction failed: {str(e)}")
        return None

def extract_instagram_content_robust(url: str) -> Dict[str, Any]:
    """
    Robust Instagram content extraction with proper connection handling.
    
    Args:
        url: Instagram URL to extract content from
        
    Returns:
        Dictionary with extracted content or None if failed
    """
    try:
        logger.info(f"Attempting robust Instagram extraction for: {url}")
        
        # Add delay to avoid rate limiting
        delay = random.uniform(1, 4)
        logger.info(f"Waiting {delay:.1f} seconds before attempting Instagram extraction...")
        time.sleep(delay)
        
        # Create a robust session
        session = create_robust_session()
        
        # Instagram requires specific headers to avoid blocks
        instagram_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        
        session.headers.update(instagram_headers)
        
        # Try multiple Instagram extraction approaches
        attempts = [
            {"url": url, "method": "direct"},
            {"url": url.replace("/?igsh=", "/?utm_source=ig_web_copy_link&"), "method": "clean_params"},
            {"url": url.split("?")[0], "method": "no_params"}
        ]
        
        for attempt_num, attempt in enumerate(attempts, 1):
            try:
                logger.info(f"Instagram extraction attempt {attempt_num}: {attempt['method']} - {attempt['url']}")
                
                response = session.get(attempt["url"], timeout=30)
                
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try to extract meaningful content
                    title = ""
                    description = ""
                    author = ""
                    
                    # Look for Open Graph meta tags first
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        title = og_title.get('content', '').strip()
                    
                    og_description = soup.find('meta', property='og:description')
                    if og_description and og_description.get('content'):
                        description = og_description.get('content', '').strip()
                    
                    # Try to get author info
                    og_site = soup.find('meta', property='og:site_name')
                    if og_site and og_site.get('content'):
                        author = og_site.get('content', '').strip()
                    
                    # Try alternative selectors for author
                    if not author:
                        author_meta = soup.find('meta', property='og:url')
                        if author_meta and author_meta.get('content'):
                            author_url = author_meta.get('content', '')
                            if '/p/' in author_url or '/reel/' in author_url:
                                # Extract username from URL
                                parts = author_url.split('/')
                                for i, part in enumerate(parts):
                                    if part in ['p', 'reel'] and i > 0:
                                        author = parts[i-1]
                                        break
                    
                    # Look for JSON-LD structured data which Instagram sometimes uses
                    json_scripts = soup.find_all('script', type='application/ld+json')
                    for script in json_scripts:
                        try:
                            json_data = json.loads(script.string)
                            if isinstance(json_data, dict):
                                if 'name' in json_data and not title:
                                    title = json_data['name']
                                if 'description' in json_data and not description:
                                    description = json_data['description']
                                if 'author' in json_data and not author:
                                    if isinstance(json_data['author'], dict):
                                        author = json_data['author'].get('name', '')
                                    else:
                                        author = str(json_data['author'])
                        except (json.JSONDecodeError, KeyError):
                            continue
                    
                    # Try to extract content from Instagram-specific selectors
                    if not description or len(description) < 20:
                        content_selectors = [
                            'meta[name="description"]',
                            'meta[property="twitter:description"]',
                            '.Caption'
                        ]
                        
                        for selector in content_selectors:
                            element = soup.select_one(selector)
                            if element:
                                if element.name == 'meta':
                                    extracted_text = element.get('content', '')
                                else:
                                    extracted_text = element.get_text(strip=True)
                                
                                if extracted_text and len(extracted_text) > len(description):
                                    description = extracted_text
                                    break
                    
                    # Get thumbnail if available
                    thumbnails = []
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        thumbnails.append(og_image.get('content'))
                    
                    # Check if we got meaningful content
                    if title and title not in ["Instagram", "Instagram - Discover what's happening", ""] and len(title) > 3:
                        # Create detailed response
                        text = f"Title: {title}\n"
                        if author:
                            text += f"Creator: {author}\n"
                        if description and description != title:
                            text += f"Description: {description}\n"
                        text += f"Source: Instagram\n"
                        
                        session.close()
                        
                        return {
                            "title": title,
                            "text": text,
                            "description": description,
                            "meta_description": description,
                            "uploader": author,
                            "uploader_url": f"https://www.instagram.com/{author}/" if author else "",
                            "creator": author,
                            "images": thumbnails,
                            "url": url,
                            "platform": "Instagram",
                            "duration": None,
                            "view_count": None,
                            "like_count": None,
                            "raw_metadata": {
                                "extraction_method": f"web_scraping_{attempt['method']}",
                                "attempt_url": attempt["url"]
                            }
                        }
                    else:
                        logger.warning(f"Instagram attempt {attempt_num} - No meaningful content. Title: '{title}'")
                else:
                    logger.warning(f"Instagram attempt {attempt_num} failed with status: {response.status_code}")
                
                # Add delay between attempts
                if attempt_num < len(attempts):
                    time.sleep(random.uniform(2, 4))
                    
            except Exception as attempt_error:
                logger.warning(f"Instagram extraction attempt {attempt_num} failed: {str(attempt_error)}")
                if attempt_num < len(attempts):
                    time.sleep(random.uniform(2, 4))
        
        session.close()
        return None
        
    except Exception as e:
        logger.error(f"Robust Instagram extraction failed: {str(e)}")
        return None

def extract_instagram_info_from_url(url: str) -> Dict[str, Any]:
    """
    Extract basic information from Instagram URL structure when network methods fail.
    
    Args:
        url: Instagram URL
        
    Returns:
        Dictionary with basic extracted info or None
    """
    try:
        logger.info(f"Trying URL-based Instagram info extraction for: {url}")
        
        # Parse different Instagram URL patterns
        content_type = ""
        content_description = ""
        content_id = ""
        username = ""
        
        # Extract components from URL
        if "/reel/" in url:
            content_type = "Instagram Reel"
            content_description = "Short-form vertical video content on Instagram - unable to extract specific details due to platform restrictions."
            # Extract reel ID
            reel_match = re.search(r'/reel/([A-Za-z0-9_-]+)', url)
            if reel_match:
                content_id = reel_match.group(1)
        elif "/p/" in url:
            content_type = "Instagram Post"
            content_description = "Instagram post containing images, video, or carousel content - unable to extract specific details due to platform restrictions."
            # Extract post ID
            post_match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
            if post_match:
                content_id = post_match.group(1)
        elif "/tv/" in url:
            content_type = "Instagram TV (IGTV)"
            content_description = "Long-form video content on Instagram TV - unable to extract specific details due to platform restrictions."
            # Extract IGTV ID
            tv_match = re.search(r'/tv/([A-Za-z0-9_-]+)', url)
            if tv_match:
                content_id = tv_match.group(1)
        elif "/stories/" in url:
            content_type = "Instagram Story"
            content_description = "Temporary Instagram story content - unable to extract specific details due to platform restrictions."
        else:
            content_type = "Instagram Content"
            content_description = "Instagram content - unable to extract specific details due to platform restrictions."
        
        # Try to extract username from URL
        username_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)/', url)
        if username_match:
            potential_username = username_match.group(1)
            # Filter out non-username parts
            if potential_username not in ['p', 'reel', 'tv', 'stories', 'explore', 'accounts']:
                username = potential_username
        
        # Create title based on content type and available info
        if content_id and username:
            title = f"{content_type} by @{username} (ID: {content_id})"
        elif content_id:
            title = f"{content_type} (ID: {content_id})"
        elif username:
            title = f"{content_type} by @{username}"
        else:
            title = content_type
        
        # Create comprehensive description
        full_description = content_description
        if username:
            full_description += f" Posted by @{username}."
        
        # Add helpful note
        helpful_note = "Note: Instagram restricts automated content extraction. To view the actual content, please click the link to open in Instagram."
        
        # Create detailed text
        text = f"Title: {title}\n"
        text += f"Content Type: {content_type}\n"
        text += f"Description: {full_description}\n"
        if content_id:
            text += f"Content ID: {content_id}\n"
        if username:
            text += f"Creator: @{username}\n"
        text += f"Platform: Instagram\n"
        text += f"URL: {url}\n"
        text += f"{helpful_note}\n"
        
        return {
            "title": title,
            "text": text,
            "description": full_description,
            "meta_description": full_description,
            "uploader": username,
            "uploader_url": f"https://www.instagram.com/{username}/" if username else "",
            "creator": username,
            "images": [],
            "url": url,
            "platform": "Instagram",
            "duration": None,
            "view_count": None,
            "like_count": None,
            "is_fallback_extraction": True,  # Flag to indicate this is a fallback
            "extraction_note": helpful_note,
            "raw_metadata": {
                "extraction_method": "url_pattern_analysis",
                "content_type": content_type,
                "content_id": content_id,
                "username": username,
                "note": "Instagram content extraction limited due to platform restrictions"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Instagram URL analysis: {str(e)}")
        return None