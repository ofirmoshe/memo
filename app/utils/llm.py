import os
import logging
from typing import Dict, List, Any
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_content_with_llm(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to analyze and summarize content.
    
    Args:
        content: Dictionary containing extracted content
        
    Returns:
        Dictionary with description and tags
    """
    logger.info("Analyzing content with LLM")
    
    # Build prompt for LLM
    title = content.get("title", "Untitled")
    text = content.get("text", "")
    
    # Truncate text if it's too long
    if len(text) > 8000:
        text = text[:8000] + "..."
    
    prompt = f"""
Given the following content, please generate:
1. A short description (2-3 sentences) that summarizes the content
2. A list of relevant tags or categories (e.g., "recipe", "technology", "news", "tutorial")

Title: {title}

Content:
{text}

Please respond in the following JSON format:
{{
  "description": "your summary here",
  "tags": ["tag1", "tag2", "tag3", ...]
}}
"""
    
    try:
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes web content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract and parse response
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
            
            # Ensure description and tags exist
            if "description" not in result:
                result["description"] = "No description available."
            
            if "tags" not in result or not isinstance(result["tags"], list):
                result["tags"] = ["uncategorized"]
            
            return result
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            logger.warning("Failed to parse LLM response as JSON, using fallback parsing")
            
            # Extract description (assume it's in the first few lines)
            lines = response_text.split("\n")
            description = ""
            for line in lines:
                if "description" in line.lower() and ":" in line:
                    description = line.split(":", 1)[1].strip().strip('"')
                    break
            
            # Extract tags
            tags = []
            for line in lines:
                if "tags" in line.lower() and ":" in line:
                    tags_text = line.split(":", 1)[1].strip()
                    # Try to extract tags from a list-like format
                    tags = [tag.strip().strip('"').strip("'") for tag in 
                           tags_text.strip("[]").split(",")]
                    break
            
            return {
                "description": description or "No description available.",
                "tags": tags or ["uncategorized"]
            }
    
    except Exception as e:
        logger.error(f"Error calling LLM API: {str(e)}")
        # Return a default response
        return {
            "description": "Failed to generate description due to an error.",
            "tags": ["uncategorized"]
        }

def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a text.
    
    Args:
        text: Text to generate embedding for
        
    Returns:
        List of floats representing the embedding
    """
    logger.info("Generating embedding")
    
    try:
        # Call OpenAI API
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        # Extract embedding
        embedding = response.data[0].embedding
        return embedding
    
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        # Return a default embedding (zeros)
        return [0.0] * 1536  # Default size for OpenAI embedding 