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

# Configure logging
logger = logging.getLogger(__name__)

def scrape_social_media(url: str) -> Dict[str, Any]:
    """
    Extract content from a social media URL using yt-dlp.
    
    Args:
        url: Social media URL to scrape
        
    Returns:
        Dictionary with extracted content and success indicator
    """
    logger.info(f"Scraping social media URL: {url}")
    
    try:
        # Create a temporary directory for downloaded metadata
        with tempfile.TemporaryDirectory() as temp_dir:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            platform = extract_platform_name(domain)
            
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
            if platform == "YouTube":
                result = extract_youtube_content(url, temp_dir)
                if result:
                    result["success"] = True
                    return result
            
            # Try multiple approaches with different timeout and retry strategies
            success = False
            metadata = None
            
            # Approach 1: Basic yt-dlp command with shorter timeout
            if not success:
                try:
                    base_cmd = [
                        "yt-dlp",
                        "--skip-download",  # Don't download the actual video
                        "--write-info-json",  # Write metadata to JSON
                        "--no-warnings",  # Reduce output noise
                        "--ignore-errors",  # Continue on download errors
                        "--no-playlist",   # Only download the video, not the playlist
                        "--socket-timeout", "15",  # 15 second socket timeout
                        "--retries", "2",  # Only 2 retries
                        "-o", f"{temp_dir}/%(id)s",  # Output filename pattern
                        url
                    ]
                    
                    logger.info(f"Running basic yt-dlp command: {' '.join(base_cmd)}")
                    process = subprocess.run(base_cmd, capture_output=True, text=True, timeout=30)
                    
                    if process.returncode == 0:
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                        if json_files:
                            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            success = True
                            logger.info("Successfully extracted with basic command")
                    else:
                        logger.warning(f"Basic yt-dlp failed with code {process.returncode}: {process.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning("Basic yt-dlp command timed out")
                except Exception as e:
                    logger.warning(f"Basic yt-dlp command failed: {str(e)}")
            
            # Approach 2: With user agent and headers
            if not success:
                try:
                    # Clean up temp directory
                    for f in os.listdir(temp_dir):
                        if f.endswith('.info.json'):
                            os.remove(os.path.join(temp_dir, f))
                    
                    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    enhanced_cmd = [
                        "yt-dlp",
                        "--skip-download",
                        "--write-info-json",
                        "--no-warnings",
                        "--ignore-errors",
                        "--no-playlist",
                        "--socket-timeout", "10",
                        "--retries", "1",
                        "--add-header", f"User-Agent: {user_agent}",
                        "--add-header", "Accept-Language: en-US,en;q=0.9",
                        "-o", f"{temp_dir}/%(id)s",
                        url
                    ]
                    
                    logger.info(f"Running enhanced yt-dlp command with headers")
                    process = subprocess.run(enhanced_cmd, capture_output=True, text=True, timeout=25)
                    
                    if process.returncode == 0:
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                        if json_files:
                            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            success = True
                            logger.info("Successfully extracted with enhanced command")
                    else:
                        logger.warning(f"Enhanced yt-dlp failed: {process.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning("Enhanced yt-dlp command timed out")
                except Exception as e:
                    logger.warning(f"Enhanced yt-dlp command failed: {str(e)}")
            
            # Approach 3: Platform-specific optimizations
            if not success and platform in ["TikTok", "Instagram", "Facebook", "YouTube"]:
                try:
                    # Clean up temp directory
                    for f in os.listdir(temp_dir):
                        if f.endswith('.info.json'):
                            os.remove(os.path.join(temp_dir, f))
                    
                    platform_cmd = [
                        "yt-dlp",
                        "--skip-download",
                        "--write-info-json",
                        "--no-warnings",
                        "--ignore-errors",
                        "--no-playlist",
                        "--socket-timeout", "8",
                        "--retries", "1",
                    ]
                    
                    # Platform-specific user agents and configurations
                    if platform == "TikTok":
                        platform_cmd.extend([
                            "--add-header", "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                            "--extractor-args", "tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com"
                        ])
                    elif platform == "Instagram":
                        platform_cmd.extend([
                            "--add-header", "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                            "--extractor-args", "instagram:include_comments=false"
                        ])
                    elif platform == "Facebook":
                        platform_cmd.extend([
                            "--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "--add-header", "Accept-Language: en-US,en;q=0.9",
                            "--add-header", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "--extractor-args", "facebook:legacy_api=false",
                            "--extractor-args", "facebook:tab=timeline",
                        ])
                    elif platform == "YouTube":
                        platform_cmd.extend([
                            "--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "--youtube-skip-dash-manifest",
                            "--extractor-args", "youtube:player_client=web,mweb",
                            "--extractor-args", "youtube:player_skip=webpage,configs",
                            "--extractor-args", "youtube:skip=translated_subs",
                        ])
                    
                    platform_cmd.extend(["-o", f"{temp_dir}/%(id)s", url])
                    
                    logger.info(f"Running platform-specific command for {platform}")
                    process = subprocess.run(platform_cmd, capture_output=True, text=True, timeout=20)
                    
                    if process.returncode == 0:
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                        if json_files:
                            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            success = True
                            logger.info(f"Successfully extracted with {platform}-specific command")
                    else:
                        logger.warning(f"Platform-specific yt-dlp failed: {process.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning("Platform-specific yt-dlp command timed out")
                except Exception as e:
                    logger.warning(f"Platform-specific yt-dlp command failed: {str(e)}")
            
            # If all yt-dlp approaches failed, try alternative methods
            if not success:
                logger.info("All yt-dlp approaches failed, trying alternative extraction methods")
                
                # For YouTube, try oEmbed API
                if platform == "YouTube":
                    result = extract_youtube_content(url, temp_dir, force_alternative=True)
                    if result:
                        result["success"] = True
                        return result
                
                # For Facebook, try oEmbed API
                if platform == "Facebook":
                    result = extract_facebook_oembed(url)
                    if result:
                        result["success"] = True
                        return result
                    
                    # If oEmbed fails, try URL-based extraction as final fallback
                    result = extract_facebook_info_from_url(url)
                    if result:
                        result["success"] = True
                        return result
                
                # For other platforms, try basic web scraping
                alternative_result = try_alternative_extraction(url, platform)
                if alternative_result:
                    alternative_result["success"] = True
                    return alternative_result
                
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
            
            # Process the successfully extracted metadata
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
        
        # Platform-specific headers and approaches
        if platform == "Facebook":
            # Facebook-specific alternative extraction
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
                response = requests.get(mobile_url, headers=headers, timeout=15, allow_redirects=True)
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
                            if title:
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
                    
                    if title and title != "Facebook":
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
                            "raw_metadata": {}
                        }
            except Exception as fb_error:
                logger.warning(f"Facebook mobile extraction failed: {str(fb_error)}")
        
        # General approach for other platforms or as fallback
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
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
                    "raw_metadata": {}
                }
        
        return None
        
    except Exception as e:
        logger.warning(f"Alternative extraction failed: {str(e)}")
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
        }
        
        try:
            response = requests.get(oembed_url, headers=headers, timeout=10)
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
                        "oembed_data": oembed_data
                    }
                }
        except requests.exceptions.RequestException as e:
            logger.warning(f"Facebook oEmbed API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.warning(f"Facebook oEmbed API returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.warning(f"Error processing Facebook oEmbed response: {str(e)}")
        
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
        if "/share/r/" in url:
            # Share URL format
            title = "Facebook Shared Post"
            description = "A post shared on Facebook"
        elif "/posts/" in url:
            # Direct post URL
            title = "Facebook Post"
            description = "A Facebook post"
        elif "/watch/" in url or "/video/" in url:
            # Video URL
            title = "Facebook Video"
            description = "A video shared on Facebook"
        elif "/events/" in url:
            # Event URL
            title = "Facebook Event"
            description = "A Facebook event"
        elif "/photo/" in url or "/photos/" in url:
            # Photo URL
            title = "Facebook Photo"
            description = "A photo shared on Facebook"
        else:
            # Generic Facebook content
            title = "Facebook Content"
            description = "Content shared on Facebook"
        
        # Create basic response
        text = f"Title: {title}\n"
        text += f"Description: {description}\n"
        text += f"Note: Extracted from URL structure due to Facebook's anti-scraping measures\n"
        
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
                "extraction_method": "url_pattern_analysis",
                "note": "Limited data due to Facebook's privacy and anti-scraping measures"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Facebook URL analysis: {str(e)}")
        return None 