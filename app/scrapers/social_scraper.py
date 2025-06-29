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

def check_yt_dlp_availability() -> bool:
    """Check if yt-dlp is available and executable."""
    try:
        result = subprocess.run(["yt-dlp", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"yt-dlp is available, version: {result.stdout.strip()}")
            return True
        else:
            logger.warning("yt-dlp returned non-zero exit code")
            return False
    except FileNotFoundError:
        logger.warning("yt-dlp not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp version check timed out")
        return False
    except Exception as e:
        logger.warning(f"Error checking yt-dlp availability: {str(e)}")
        return False

def scrape_social_media_fallback(url: str, platform: str) -> Dict[str, Any]:
    """
    Fallback method for social media scraping when yt-dlp is not available.
    
    Args:
        url: Social media URL to scrape
        platform: Detected platform name
        
    Returns:
        Dictionary with basic extracted content
    """
    logger.info(f"Using fallback method for {platform} URL: {url}")
    
    try:
        # For YouTube, try the oEmbed API
        if platform.lower() == "youtube":
            return scrape_youtube_fallback(url)
        
        # For other platforms, try basic web scraping with headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Try to extract basic info from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Try to get meta description
        description = ""
        meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        
        # Try to get thumbnail
        thumbnails = []
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image:
            thumbnails.append(og_image.get('content', ''))
        
        # If we couldn't get much info, provide basic info
        if not title:
            title = f"{platform} Content"
        if not description:
            description = f"Content from {platform} - {url}"
        
        return {
            "title": title,
            "text": f"Title: {title}\nDescription: {description}\nSource: {platform}",
            "meta_description": description,
            "uploader": "",
            "uploader_url": "",
            "images": thumbnails,
            "url": url,
            "platform": platform,
            "raw_metadata": {},
            "fallback_used": True
        }
        
    except Exception as e:
        logger.error(f"Fallback scraping failed for {url}: {str(e)}")
        return {
            "title": f"{platform} Content",
            "text": f"Content from {platform}. Unable to extract detailed information.\nURL: {url}",
            "meta_description": f"Content from {platform}",
            "uploader": "",
            "uploader_url": "",
            "images": [],
            "url": url,
            "platform": platform,
            "raw_metadata": {},
            "fallback_used": True,
            "error": str(e)
        }

def scrape_youtube_fallback(url: str) -> Dict[str, Any]:
    """
    Fallback method specifically for YouTube URLs using oEmbed API.
    
    Args:
        url: YouTube URL to scrape
        
    Returns:
        Dictionary with extracted content
    """
    try:
        # Extract video ID
        video_id = None
        if "youtube.com/watch" in url:
            from urllib.parse import parse_qs
            query = urlparse(url).query
            params = parse_qs(query)
            video_id = params.get('v', [None])[0]
        elif "youtu.be/" in url:
            video_id = urlparse(url).path.strip('/')
        
        if not video_id:
            raise Exception("Could not extract YouTube video ID")
        
        # Try YouTube oEmbed API
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        response = requests.get(oembed_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', 'YouTube Video')
            author = data.get('author_name', '')
            
            # Get thumbnail URL
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            
            text = f"Title: {title}\n"
            if author:
                text += f"Creator: {author}\n"
            text += f"YouTube Video ID: {video_id}\n"
            
            return {
                "title": title,
                "text": text,
                "meta_description": f"YouTube video by {author}",
                "uploader": author,
                "uploader_url": f"https://www.youtube.com/channel/{data.get('author_url', '').split('/')[-1] if data.get('author_url') else ''}",
                "images": [thumbnail_url],
                "url": url,
                "platform": "YouTube",
                "raw_metadata": {
                    "video_id": video_id,
                    "thumbnail_width": data.get('thumbnail_width'),
                    "thumbnail_height": data.get('thumbnail_height')
                },
                "fallback_used": True
            }
        else:
            raise Exception(f"YouTube oEmbed API returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"YouTube fallback failed: {str(e)}")
        return {
            "title": "YouTube Video",
            "text": f"YouTube video content.\nURL: {url}",
            "meta_description": "YouTube video",
            "uploader": "",
            "uploader_url": "",
            "images": [],
            "url": url,
            "platform": "YouTube",
            "raw_metadata": {},
            "fallback_used": True,
            "error": str(e)
        }

def scrape_social_media(url: str) -> Dict[str, Any]:
    """
    Extract content from a social media URL using yt-dlp or fallback methods.
    
    Args:
        url: Social media URL to scrape
        
    Returns:
        Dictionary with extracted content
    """
    logger.info(f"Scraping social media URL: {url}")
    
    # Extract platform info
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    platform = extract_platform_name(domain)
    
    # Check if yt-dlp is available
    if not check_yt_dlp_availability():
        logger.warning("yt-dlp not available, using fallback method")
        return scrape_social_media_fallback(url, platform)
    
    try:
        # Create a temporary directory for downloaded metadata
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Platform-specific handling
            if platform == "YouTube":
                result = extract_youtube_content(url, temp_dir)
                if result:
                    return result
            
            # Core yt-dlp command with essential options only
            base_cmd = [
                "yt-dlp",
                "--skip-download",  # Don't download the actual video
                "--write-info-json",  # Write metadata to JSON
                "--no-warnings",  # Reduce output noise
                "--ignore-errors",  # Continue on download errors
                "--no-playlist",   # Only download the video, not the playlist
                "-o", f"{temp_dir}/%(id)s",  # Output filename pattern
            ]
            
            # Add the URL at the end
            base_cmd.append(url)
            
            # Execute yt-dlp
            logger.info(f"Running yt-dlp command: {' '.join(base_cmd)}")
            process = subprocess.run(base_cmd, capture_output=True, text=True, timeout=30)
            
            # Check for errors and try fallback approaches if needed
            if process.returncode != 0 or not os.listdir(temp_dir):
                logger.warning(f"yt-dlp returned non-zero exit code: {process.returncode}")
                logger.warning(f"yt-dlp stderr: {process.stderr}")
                
                # First fallback: Add a modern user agent
                logger.info("Trying fallback method with user agent")
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                fallback_cmd = base_cmd.copy()
                fallback_cmd.insert(-1, "--add-header")
                fallback_cmd.insert(-1, f"User-Agent: {user_agent}")
                
                logger.info(f"Running fallback command: {' '.join(fallback_cmd)}")
                process = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=30)
                
                # If still failing, use our fallback method
                if process.returncode != 0 or not os.listdir(temp_dir):
                    logger.warning("yt-dlp failed, falling back to basic scraping")
                    return scrape_social_media_fallback(url, platform)
            
            # Find the JSON file in the temp directory
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
            
            if not json_files:
                logger.error("No metadata JSON file was created by yt-dlp")
                logger.warning("Falling back to basic scraping method")
                return scrape_social_media_fallback(url, platform)
            
            # Read the JSON metadata
            with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
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
                "title": title,
                "text": text,
                "meta_description": description,
                "uploader": uploader,
                "uploader_url": uploader_url,
                "images": thumbnails[:5],  # Limit to first 5 thumbnails
                "url": url,
                "platform": platform,
                "raw_metadata": {
                    "tags": metadata.get('tags', []),
                    "view_count": metadata.get('view_count'),
                    "like_count": metadata.get('like_count'),
                    "comment_count": metadata.get('comment_count'),
                    "upload_date": metadata.get('upload_date')
                }
            }
    
    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp timed out for URL {url}")
        return scrape_social_media_fallback(url, platform)
    except Exception as e:
        logger.error(f"Error scraping social media URL {url}: {str(e)}")
        # Use fallback method on any error
        return scrape_social_media_fallback(url, platform)

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