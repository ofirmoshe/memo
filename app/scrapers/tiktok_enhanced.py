"""
Enhanced TikTok scraper that supports both video and photo posts.
Addresses the limitations of yt-dlp for TikTok photo carousels.
"""

import logging
import requests
import json
import re
import time
import random
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
import subprocess
import tempfile
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class TikTokEnhancedScraper:
    """Enhanced TikTok scraper supporting both videos and photo posts."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
    
    def detect_content_type(self, url: str) -> str:
        """
        Detect if TikTok URL is a video or photo post.
        
        Args:
            url: TikTok URL
            
        Returns:
            'video', 'photo', or 'unknown'
        """
        try:
            # Follow redirects to get the actual TikTok URL
            response = self.session.head(url, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # Check URL patterns
            if '/photo/' in final_url:
                return 'photo'
            elif '/video/' in final_url:
                return 'video'
            else:
                # Try to determine from the page content
                try:
                    response = self.session.get(final_url, timeout=15)
                    if response.status_code == 200:
                        content = response.text
                        # Look for photo-specific indicators
                        if '"imagePost":' in content or '"photoMode":' in content:
                            return 'photo'
                        elif '"videoMeta":' in content or '"video":' in content:
                            return 'video'
                except:
                    pass
                
                return 'unknown'
        except Exception as e:
            logger.warning(f"Could not detect TikTok content type: {e}")
            return 'unknown'
    
    def extract_tiktok_id(self, url: str) -> Optional[str]:
        """Extract TikTok video/photo ID from URL."""
        try:
            # Common TikTok URL patterns
            patterns = [
                r'/video/(\d+)',
                r'/photo/(\d+)',
                r'@[\w.-]+/video/(\d+)',
                r'@[\w.-]+/photo/(\d+)',
                r'vm\.tiktok\.com/(\w+)',
                r'vt\.tiktok\.com/(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            logger.warning(f"Could not extract TikTok ID: {e}")
            return None
    
    def extract_photo_post(self, url: str) -> Dict[str, Any]:
        """
        Extract TikTok photo post content using web scraping.
        
        Args:
            url: TikTok photo post URL
            
        Returns:
            Dictionary with extracted content
        """
        try:
            logger.info(f"Extracting TikTok photo post: {url}")
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch TikTok page: {response.status_code}")
                return self._create_error_response(url, "Failed to fetch page")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data from various sources
            data = {}
            
            # Try to extract from JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        data.update(json_data)
                except:
                    continue
            
            # Try to extract from meta tags
            meta_data = self._extract_meta_tags(soup)
            data.update(meta_data)
            
            # Try to extract from page content
            content_data = self._extract_page_content(soup)
            data.update(content_data)
            
            # Try to extract from inline JSON
            inline_data = self._extract_inline_json(response.text)
            data.update(inline_data)
            
            return self._format_tiktok_response(data, url, 'photo')
            
        except Exception as e:
            logger.error(f"Error extracting TikTok photo post: {e}")
            return self._create_error_response(url, f"Extraction failed: {str(e)}")
    
    def extract_video_post(self, url: str) -> Dict[str, Any]:
        """
        Extract TikTok video post using yt-dlp first, then fallback methods.
        
        Args:
            url: TikTok video URL
            
        Returns:
            Dictionary with extracted content
        """
        try:
            logger.info(f"Extracting TikTok video: {url}")
            
            # First try yt-dlp for videos
            ytdlp_result = self._extract_with_ytdlp(url)
            if ytdlp_result['success']:
                return ytdlp_result
            
            # If yt-dlp fails, try web scraping
            logger.info("yt-dlp failed, trying web scraping for video")
            return self.extract_photo_post(url)  # Same method works for videos too
            
        except Exception as e:
            logger.error(f"Error extracting TikTok video: {e}")
            return self._create_error_response(url, f"Video extraction failed: {str(e)}")
    
    def _extract_with_ytdlp(self, url: str) -> Dict[str, Any]:
        """Extract TikTok content using yt-dlp."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = [
                    "yt-dlp",
                    "--skip-download",
                    "--write-info-json",
                    "--no-warnings",
                    "--ignore-errors",
                    "--socket-timeout", "20",
                    "--retries", "2",
                    "--add-header", "User-Agent:Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                    "-o", f"{temp_dir}/%(id)s",
                    url
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if process.returncode == 0:
                    json_files = [f for f in os.listdir(temp_dir) if f.endswith('.info.json')]
                    if json_files:
                        with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        return self._format_ytdlp_response(metadata, url)
                
                return {"success": False, "error": "yt-dlp extraction failed"}
                
        except Exception as e:
            logger.warning(f"yt-dlp extraction failed: {e}")
            return {"success": False, "error": f"yt-dlp failed: {str(e)}"}
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from meta tags."""
        data = {}
        
        # Open Graph tags
        og_tags = {
            'og:title': 'title',
            'og:description': 'description',
            'og:image': 'thumbnail',
            'og:url': 'url'
        }
        
        for og_property, key in og_tags.items():
            tag = soup.find('meta', property=og_property)
            if tag:
                data[key] = tag.get('content', '')
        
        # Twitter Card tags
        twitter_tags = {
            'twitter:title': 'title',
            'twitter:description': 'description',
            'twitter:image': 'thumbnail'
        }
        
        for twitter_name, key in twitter_tags.items():
            if key not in data:
                tag = soup.find('meta', attrs={'name': twitter_name})
                if tag:
                    data[key] = tag.get('content', '')
        
        return data
    
    def _extract_page_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from page content."""
        data = {}
        
        # Try to find title
        if 'title' not in data:
            title_tag = soup.find('title')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
        
        # Try to find description
        if 'description' not in data:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                data['description'] = desc_tag.get('content', '')
        
        return data
    
    def _extract_inline_json(self, html_content: str) -> Dict[str, Any]:
        """Extract data from inline JSON in the HTML."""
        data = {}
        
        try:
            # Look for common TikTok data patterns
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});',
                r'"props":\s*({.*?"pageProps".*?})',
                r'"videoDetails":\s*({.*?})',
                r'"itemInfo":\s*({.*?})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        json_data = json.loads(match)
                        if isinstance(json_data, dict):
                            data.update(self._flatten_json_data(json_data))
                    except:
                        continue
        
        except Exception as e:
            logger.warning(f"Failed to extract inline JSON: {e}")
        
        return data
    
    def _flatten_json_data(self, data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Flatten nested JSON data to extract useful fields."""
        flattened = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}_{key}" if prefix else key
                
                if isinstance(value, (dict, list)):
                    if key in ['author', 'music', 'stats', 'video', 'imagePost']:
                        flattened.update(self._flatten_json_data(value, new_key))
                elif isinstance(value, (str, int, float, bool)):
                    flattened[new_key] = value
        
        elif isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                flattened.update(self._flatten_json_data(data[0], prefix))
        
        return flattened
    
    def _format_tiktok_response(self, data: Dict[str, Any], url: str, content_type: str) -> Dict[str, Any]:
        """Format extracted data into standard response format."""
        try:
            # Extract basic information
            title = data.get('title', '')
            description = data.get('description', '')
            
            # Clean up title and description
            if title and ('TikTok' in title or 'tiktok' in title.lower()):
                # If title is generic TikTok title, use description as title
                if description and len(description) > len(title):
                    title = description[:100] + '...' if len(description) > 100 else description
            
            # Extract creator information
            creator = data.get('author_nickname', data.get('author_name', data.get('uploader', '')))
            creator_url = data.get('author_url', data.get('uploader_url', ''))
            
            # Extract media URLs
            images = []
            if 'thumbnail' in data:
                images.append(data['thumbnail'])
            
            # Look for additional images in photo posts
            for key, value in data.items():
                if 'image' in key.lower() and isinstance(value, str) and value.startswith('http'):
                    if value not in images:
                        images.append(value)
            
            # Extract engagement metrics
            view_count = data.get('view_count', data.get('playCount', data.get('stats_playCount')))
            like_count = data.get('like_count', data.get('diggCount', data.get('stats_diggCount')))
            comment_count = data.get('comment_count', data.get('commentCount', data.get('stats_commentCount')))
            share_count = data.get('share_count', data.get('shareCount', data.get('stats_shareCount')))
            
            # Format text content
            text_content = f"Title: {title}\n"
            if creator:
                text_content += f"Creator: {creator}\n"
            if description and description != title:
                text_content += f"Description: {description}\n"
            
            # Add metrics if available
            if view_count:
                text_content += f"Views: {view_count}\n"
            if like_count:
                text_content += f"Likes: {like_count}\n"
            if comment_count:
                text_content += f"Comments: {comment_count}\n"
            if share_count:
                text_content += f"Shares: {share_count}\n"
            
            return {
                "success": True,
                "title": title or "TikTok Content",
                "text": text_content,
                "description": description,
                "meta_description": description,
                "uploader": creator,
                "uploader_url": creator_url,
                "creator": creator,
                "images": images[:5],  # Limit to 5 images
                "url": url,
                "platform": "TikTok",
                "content_type": content_type,
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "share_count": share_count,
                "similarity_score": 1.0,
                "raw_metadata": {
                    "content_type": content_type,
                    "extraction_method": "enhanced_scraper",
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "share_count": share_count,
                    "raw_data": data
                }
            }
        
        except Exception as e:
            logger.error(f"Error formatting TikTok response: {e}")
            return self._create_error_response(url, f"Response formatting failed: {str(e)}")
    
    def _format_ytdlp_response(self, metadata: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Format yt-dlp metadata into standard response format."""
        try:
            title = metadata.get('title', 'TikTok Video')
            description = metadata.get('description', '')
            uploader = metadata.get('uploader', '')
            uploader_url = metadata.get('uploader_url', '')
            
            thumbnails = []
            if 'thumbnails' in metadata and isinstance(metadata['thumbnails'], list):
                thumbnails = [t.get('url', '') for t in metadata['thumbnails'] if 'url' in t]
            elif 'thumbnail' in metadata:
                thumbnails = [metadata['thumbnail']]
            
            text_content = f"Title: {title}\n"
            if uploader:
                text_content += f"Creator: {uploader}\n"
            if description:
                text_content += f"Description: {description}\n"
            
            # Add metrics
            view_count = metadata.get('view_count')
            like_count = metadata.get('like_count')
            if view_count:
                text_content += f"Views: {view_count}\n"
            if like_count:
                text_content += f"Likes: {like_count}\n"
            
            return {
                "success": True,
                "title": title,
                "text": text_content,
                "description": description,
                "meta_description": description,
                "uploader": uploader,
                "uploader_url": uploader_url,
                "creator": uploader,
                "images": thumbnails[:5],
                "url": url,
                "platform": "TikTok",
                "content_type": "video",
                "duration": metadata.get('duration'),
                "view_count": view_count,
                "like_count": like_count,
                "similarity_score": 1.0,
                "raw_metadata": {
                    "content_type": "video",
                    "extraction_method": "yt-dlp",
                    "tags": metadata.get('tags', []),
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": metadata.get('comment_count'),
                    "upload_date": metadata.get('upload_date')
                }
            }
        
        except Exception as e:
            logger.error(f"Error formatting yt-dlp response: {e}")
            return self._create_error_response(url, f"yt-dlp response formatting failed: {str(e)}")
    
    def _create_error_response(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "title": "TikTok Content Extraction Failed",
            "text": f"Failed to extract content from {url}: {error_message}",
            "meta_description": "",
            "uploader": "",
            "uploader_url": "",
            "creator": "",
            "images": [],
            "url": url,
            "platform": "TikTok",
            "content_type": "unknown",
            "raw_metadata": {
                "error": error_message,
                "extraction_method": "enhanced_scraper"
            }
        }
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main scraping method that handles both videos and photo posts.
        
        Args:
            url: TikTok URL to scrape
            
        Returns:
            Dictionary with extracted content
        """
        try:
            logger.info(f"Starting enhanced TikTok scraping for: {url}")
            
            # Detect content type
            content_type = self.detect_content_type(url)
            logger.info(f"Detected content type: {content_type}")
            
            if content_type == "photo":
                return self.extract_photo_post(url)
            elif content_type == "video":
                return self.extract_video_post(url)
            else:
                # Unknown type, try both methods
                logger.info("Unknown content type, trying photo extraction first")
                result = self.extract_photo_post(url)
                if result['success']:
                    return result
                
                logger.info("Photo extraction failed, trying video extraction")
                return self.extract_video_post(url)
        
        except Exception as e:
            logger.error(f"Enhanced TikTok scraping failed: {e}")
            return self._create_error_response(url, f"Scraping failed: {str(e)}")
    
    def __del__(self):
        """Clean up session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()


def extract_tiktok_enhanced(url: str) -> Dict[str, Any]:
    """
    Enhanced TikTok extraction function supporting both videos and photo posts.
    
    Args:
        url: TikTok URL to extract
        
    Returns:
        Dictionary with extracted content
    """
    scraper = TikTokEnhancedScraper()
    return scraper.scrape(url) 