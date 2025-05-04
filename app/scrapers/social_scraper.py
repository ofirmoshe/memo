import logging
import json
import os
import tempfile
import subprocess
from typing import Dict, Any, List
import re
from urllib.parse import urlparse

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
            # Determine platform-specific options
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Base yt-dlp command
            base_cmd = [
                "yt-dlp",
                "--skip-download",  # Don't download the actual video
                "--write-info-json",  # Write metadata to JSON
                "--no-warnings",  # Reduce output noise
                "-o", f"{temp_dir}/%(id)s",  # Output filename pattern
                url
            ]
            
            # Add platform-specific options
            if "tiktok.com" in domain:
                base_cmd.extend(["--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"])
            elif "instagram.com" in domain:
                base_cmd.extend(["--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"])
            
            # Execute yt-dlp
            logger.info(f"Running yt-dlp command: {' '.join(base_cmd)}")
            process = subprocess.run(base_cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"yt-dlp failed with error: {process.stderr}")
                raise Exception(f"yt-dlp failed: {process.stderr}")
            
            # Find the JSON file in the temp directory
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
            
            if not json_files:
                logger.error("No metadata JSON file was created by yt-dlp")
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
            if "tiktok.com" in domain:
                # For TikTok, include view count and like count if available
                view_count = metadata.get('view_count', 'Unknown')
                like_count = metadata.get('like_count', 'Unknown')
                text += f"Views: {view_count}\n"
                text += f"Likes: {like_count}\n"
            
            return {
                "title": title,
                "text": text,
                "meta_description": description,
                "uploader": uploader,
                "uploader_url": uploader_url,
                "images": thumbnails[:5],  # Limit to first 5 thumbnails
                "url": url,
                "platform": extract_platform_name(domain),
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
    elif "facebook.com" in domain:
        return "Facebook"
    elif "linkedin.com" in domain:
        return "LinkedIn"
    elif "pinterest.com" in domain:
        return "Pinterest"
    elif "twitter.com" in domain or "x.com" in domain:
        return "Twitter"
    else:
        return "Social Media" 