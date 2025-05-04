import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import re

# Configure logging
logger = logging.getLogger(__name__)

def scrape_website(url: str) -> Dict[str, Any]:
    """
    Scrape a website and extract content.
    
    Args:
        url: URL to scrape
        
    Returns:
        Dictionary with extracted content
    """
    logger.info(f"Scraping website: {url}")
    
    try:
        # Make request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text() if title_tag else "Untitled"
        
        # Extract meta description
        meta_desc_tag = soup.find("meta", {"name": "description"})
        meta_description = meta_desc_tag.get("content", "") if meta_desc_tag else ""
        
        # Extract main content
        # Try different strategies to get the main content
        main_content = soup.find("main") or soup.find("article") or soup.find("div", {"id": "content"}) or soup.find("div", {"class": "content"})
        
        if main_content:
            # Remove script and style tags
            for tag in main_content(["script", "style"]):
                tag.decompose()
            
            # Get text
            text = main_content.get_text(separator=" ", strip=True)
        else:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        # Extract images
        images = []
        img_tags = soup.find_all("img", src=True)
        for img in img_tags:
            src = img.get("src", "")
            if src and src.startswith(("http://", "https://")):
                images.append(src)
        
        # Clean up text
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return {
            "title": title,
            "text": text,
            "meta_description": meta_description,
            "images": images[:5],  # Limit to first 5 images
            "url": url
        }
    
    except Exception as e:
        logger.error(f"Error scraping website {url}: {str(e)}")
        # Return minimal information
        return {
            "title": "Failed to extract",
            "text": f"Failed to extract content from {url}. Error: {str(e)}",
            "meta_description": "",
            "images": [],
            "url": url
        } 