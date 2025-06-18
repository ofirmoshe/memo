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

def get_llm_response(prompt: str) -> str:
    """
    Get response from OpenAI LLM.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response as a string
    """
    logger.info("Getting LLM response")
    
    try:
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes content and extracts descriptions and tags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract response text
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        raise

def analyze_content_with_llm(content: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze content with LLM to extract description and tags.
    
    Args:
        content: Content to analyze
        
    Returns:
        Analysis results
    """
    # Prepare content for analysis
    title = content.get("title", "")
    text = content.get("text", "")
    
    # Limit text length to avoid token limits
    max_text_length = 8000
    if len(text) > max_text_length:
        text = text[:max_text_length] + "..."
    
    # Create prompt for LLM
    prompt = f"""
    Analyze the following content and extract a concise description and relevant tags.
    
    Title: {title}
    
    Content: {text}
    
    Please provide:
    1. A concise description (max 150 words) summarizing the main points of the content.
    2. A list of 3-7 relevant tags that categorize this content.
    
    When generating tags, prioritize these standard categories if they apply:
    ```technology, programming, science, health, business, finance, education, entertainment,
    sports, travel, food, fashion, art, design, politics, news, environment, history,
    philosophy, psychology, productivity, self-improvement, career```
    
    - Try to use the most specific tags possible.
    - Maximum 3 tags.
    - If the content doesn't match any of these categories, create appropriate specific tags.
    - Each tag should be a single word or short phrase (1-3 words maximum).
    
    Format your response as JSON:
    {{
      "description": "your concise description here",
      "tags": ["tag1", "tag2", "tag3"]
    }}
    """
    
    # Get response from LLM
    try:
        response = get_llm_response(prompt)
        
        # Parse JSON response
        result = json.loads(response)
        
        # Ensure we have description and tags
        if "description" not in result or "tags" not in result:
            raise ValueError("Missing description or tags in LLM response")
        
        # Ensure tags is a list of strings
        if not isinstance(result["tags"], list):
            result["tags"] = []
        
        # Limit description length
        if len(result["description"]) > 500:
            result["description"] = result["description"][:497] + "..."
            
        return result
    except Exception as e:
        logger.error(f"Error analyzing content with LLM: {str(e)}")
        # Fallback to simple analysis
        return {
            "description": title or "No description available",
            "tags": ["unclassified"]
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