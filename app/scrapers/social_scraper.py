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
        Dictionary with extracted content
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
                version_process = subprocess.run(version_cmd, capture_output=True, text=True)
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
            process = subprocess.run(base_cmd, capture_output=True, text=True)
            
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
                process = subprocess.run(fallback_cmd, capture_output=True, text=True)
                
                # Second fallback: Try with cookies if available
                if process.returncode != 0 or not os.listdir(temp_dir):
                    logger.info("Trying second fallback with cookies")
                    
                    # Try to use browser cookies if available
                    browsers = ["chrome", "firefox", "edge", "safari", "opera"]
                    for browser in browsers:
                        try:
                            cookies_cmd = fallback_cmd.copy()
                            cookies_cmd.insert(-1, "--cookies-from-browser")
                            cookies_cmd.insert(-1, browser)
                            
                            logger.info(f"Trying with {browser} cookies: {' '.join(cookies_cmd)}")
                            process = subprocess.run(cookies_cmd, capture_output=True, text=True)
                            
                            if process.returncode == 0 and os.listdir(temp_dir):
                                logger.info(f"Successfully extracted with {browser} cookies")
                                break
                        except Exception as e:
                            logger.warning(f"Error trying {browser} cookies: {str(e)}")
                
                # Third fallback: Try with additional options for specific platforms
                if process.returncode != 0 or not os.listdir(temp_dir):
                    logger.info("Trying third fallback with platform-specific options")
                    
                    platform_cmd = fallback_cmd.copy()
                    
                    if platform == "YouTube":
                        platform_cmd.insert(-1, "--extractor-args")
                        platform_cmd.insert(-1, "youtube:player_client=web")
                        platform_cmd.insert(-1, "--extractor-args")
                        platform_cmd.insert(-1, "youtube:player_skip=webpage")
                    elif platform == "TikTok":
                        platform_cmd.insert(-1, "--extractor-args")
                        platform_cmd.insert(-1, "tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com")
                        platform_cmd.insert(-1, "--extractor-args")
                        platform_cmd.insert(-1, "tiktok:app_version=v2020.1.0")
                    
                    logger.info(f"Running platform-specific command: {' '.join(platform_cmd)}")
                    process = subprocess.run(platform_cmd, capture_output=True, text=True)
            
            # Find the JSON file in the temp directory
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
            
            if not json_files:
                logger.error("No metadata JSON file was created by yt-dlp")
                
                # For YouTube, try one more specialized approach
                if platform == "YouTube":
                    result = extract_youtube_content(url, temp_dir, force_alternative=True)
                    if result:
                        return result
                
                raise Exception("Failed to extract metadata from social media URL")
            
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
    
    except Exception as e:
        logger.error(f"Error scraping social media URL {url}: {str(e)}")
        # Return minimal information on failure
        return {
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