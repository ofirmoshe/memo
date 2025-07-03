import os
import logging
from typing import Dict, List, Any, Optional
import json
import openai
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
import re

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image to base64: {str(e)}")
        raise

def get_llm_response(prompt: str, image_path: str = None) -> str:
    """
    Get response from OpenAI LLM with optional image input.
    
    Args:
        prompt: The prompt to send to the LLM
        image_path: Optional path to image file for multimodal analysis
        
    Returns:
        The LLM's response as a string
    """
    logger.info("Getting LLM response")
    
    try:
        # Prepare messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant that analyzes content and extracts descriptions and tags."}
        ]
        
        if image_path:
            # Multimodal request with image
            base64_image = encode_image_to_base64(image_path)
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            })
        else:
            # Text-only request
            messages.append({"role": "user", "content": prompt})
        
        # Call OpenAI API with GPT-4o-mini
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract response text
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        raise

def analyze_image_with_llm(image_path: str, user_context: str = None) -> Dict[str, Any]:
    """
    Analyze an image directly with multimodal LLM.
    
    Args:
        image_path: Path to the image file
        user_context: Optional user-provided context
        
    Returns:
        Analysis results including extracted text and content analysis
    """
    logger.info(f"Analyzing image with multimodal LLM: {image_path}")
    
    # Create prompt for image analysis
    prompt = f"""Analyze this image and extract the following information:

1. **Text Content**: Extract all visible text from the image (OCR functionality)
2. **Image Description**: Describe what you see in the image
3. **Content Type**: Identify the type of content (receipt, document, screenshot, photo, etc.)
4. **Key Information**: Extract the most important information from the image
5. **Tags**: Generate relevant tags for categorization and search

{f"User Context: {user_context}" if user_context else ""}

Please provide a comprehensive analysis that would be useful for a personal knowledge management system.

IMPORTANT: You must respond with ONLY valid JSON. Do not include any text before or after the JSON object.

Format your response as a single JSON object:
{{
    "extracted_text": "All text visible in the image",
    "image_description": "Description of what's shown in the image", 
    "title": "Descriptive title for this content",
    "description": "Comprehensive summary of the content",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "content_type": "receipt/document/screenshot/photo/etc",
    "platform": "personal",
    "key_information": ["key point 1", "key point 2", "etc"]
}}

Remember: Respond with ONLY the JSON object, no additional text."""
    
    try:
        response = get_llm_response(prompt, image_path)
        
        # Log the raw response for debugging
        logger.info(f"Raw LLM response for image analysis: {response[:200]}...")
        
        # Try to extract JSON from the response if it's embedded in text
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
            
        result = json.loads(json_str)
        
        # Validate required fields
        required_fields = ["extracted_text", "title", "description", "tags"]
        for field in required_fields:
            if field not in result:
                result[field] = ""
        
        # Ensure tags is a list
        if not isinstance(result.get("tags"), list):
            result["tags"] = []
            
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response was: {response}")
        
        # Try to extract basic information from non-JSON response
        fallback_title = "Image Content"
        fallback_description = response[:500] if response else "Could not analyze image"
        fallback_tags = ["image", "uploaded"]
        
        # Try to extract some basic info from the response text
        if response:
            # Look for common patterns in the response
            if "receipt" in response.lower():
                fallback_tags.append("receipt")
                fallback_title = "Receipt"
            elif "document" in response.lower():
                fallback_tags.append("document")
                fallback_title = "Document"
            elif "screenshot" in response.lower():
                fallback_tags.append("screenshot")
                fallback_title = "Screenshot"
        
        # Fallback analysis
        return {
            "extracted_text": response[:200] if response else "Could not extract text",
            "image_description": fallback_description,
            "title": fallback_title,
            "description": fallback_description,
            "tags": fallback_tags,
            "content_type": "image",
            "platform": "personal",
            "key_information": []
        }
    except Exception as e:
        logger.error(f"Error analyzing image with LLM: {str(e)}")
        raise

def analyze_content_with_llm(content: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze content with LLM to extract description and tags.
    
    Args:
        content: Content to analyze
        
    Returns:
        Analysis results
    """
    # Check if this is a fallback extraction (e.g., Facebook URL pattern analysis)
    is_fallback = content.get("is_fallback_extraction", False)
    platform = content.get("platform", "").lower()
    extraction_note = content.get("extraction_note", "")
    
    # For Facebook fallback extractions, provide a simpler, more honest description
    if is_fallback and platform == "facebook":
        title = content.get("title", "Facebook Content")
        content_type = content.get("raw_metadata", {}).get("content_type", "Facebook Content")
        content_id = content.get("raw_metadata", {}).get("content_id", "")
        
        # Create a straightforward description
        if "Video" in content_type:
            description = f"Facebook video content that requires direct access to view. {extraction_note}"
            tags = ["Facebook", "video", "social-media", "requires-access"]
        elif "Post" in content_type:
            description = f"Facebook post content that requires direct access to view. {extraction_note}"
            tags = ["Facebook", "post", "social-media", "requires-access"]
        elif "Reel" in content_type:
            description = f"Facebook Reel (short video) that requires direct access to view. {extraction_note}"
            tags = ["Facebook", "reel", "video", "social-media", "requires-access"]
        elif "Event" in content_type:
            description = f"Facebook event listing that requires direct access to view details. {extraction_note}"
            tags = ["Facebook", "event", "social-media", "requires-access"]
        elif "Photo" in content_type:
            description = f"Facebook photo content that requires direct access to view. {extraction_note}"
            tags = ["Facebook", "photo", "image", "social-media", "requires-access"]
        else:
            description = f"Facebook content that requires direct access to view. {extraction_note}"
            tags = ["Facebook", "social-media", "requires-access"]
        
        # Add content ID to tags if available
        if content_id:
            tags.append(f"id-{content_id}")
        
        return {
            "description": description,
            "tags": tags[:7]  # Limit to 7 tags
        }
    
    # Prepare content for analysis
    title = content.get("title", "")
    text = content.get("text", "")
    
    # Limit text length to avoid token limits
    max_text_length = 8000
    if len(text) > max_text_length:
        text = text[:max_text_length] + "..."
    
    # Create prompt for LLM
    prompt = f"""
    You are a helpful assistant that analyzes content and extracts descriptions and tags.
    
    Title: {title}
    
    Content: {text}
    
    Please provide:
    1. A concise description (max 150 words) summarizing the main points of the content.
        - Your description should be as descriptive as possible, and should include the most important details of the content.
        - This description will be later used for natural language search, so it should be as detailed yet concise as possible, and should include the most important details of the content.
    2. A list of 3-7 relevant tags that categorize this content.
    
        - When generating tags, prioritize these standard categories if they apply:
        ```technology, programming, science, health, business, finance, education, entertainment,
        sports, travel, food, fashion, art, design, politics, news, environment, history,
        philosophy, psychology, productivity, self-improvement, career```
    
        - Try to use the most specific tags possible.
        - Maximum 7 tags.
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

def get_content_analysis_prompt(content: str, url: str = None, content_type: str = None, 
                              user_context: str = None, media_type: str = "url", 
                              extracted_text: str = None, metadata: dict = None) -> str:
    """
    Generate a prompt for analyzing content and extracting relevant information.
    
    Args:
        content: The main content to analyze
        url: URL of the content (if applicable)
        content_type: Type of content (social_media, news_article, etc.)
        user_context: User-provided context about the content
        media_type: Type of media (url, text, image, document)
        extracted_text: Text extracted from files (for images/documents)
        metadata: Additional metadata about the content
    """
    
    base_prompt = """You are an AI assistant specialized in analyzing and categorizing various types of content for a personal knowledge management system called Memora.

Your task is to analyze the provided content and extract:
1. A clear, descriptive title (max 100 characters)
2. A comprehensive summary/description (max 500 characters)
3. Relevant tags (5-10 tags that would help with searching and categorization)
4. Content type classification
5. Platform identification (if applicable)

Guidelines:
- Be concise but informative
- Focus on the most important and searchable aspects
- Use tags that are specific and useful for retrieval
- Consider the user's context when provided
- For personal documents, be respectful of privacy"""

    # Add media-specific instructions
    if media_type == "text":
        base_prompt += """

CONTENT TYPE: Direct Text Input
This is text content directly provided by the user. Focus on:
- Main topics and themes
- Key information or insights
- Actionable items or important details
- Context clues about purpose or relevance"""
        
    elif media_type == "image":
        base_prompt += """

CONTENT TYPE: Image/Photo
This content was extracted from an image using multimodal AI analysis. Consider:
- The image might contain text, documents, screenshots, or visual information
- Focus on both visual elements and any text content
- Look for document types (ID, passport, receipt, etc.)
- Consider both the extracted text and the visual context"""
        
    elif media_type == "document":
        base_prompt += """

CONTENT TYPE: Document File
This content was extracted from a document file. Focus on:
- Document type and purpose
- Key sections and main points
- Important data or information
- Professional or personal context"""
        
    elif media_type == "url":
        base_prompt += """

CONTENT TYPE: Web Content
This content was extracted from a URL. Consider:
- Source credibility and type
- Main topic and key points
- Actionable information
- Relevance and context"""

    # Add user context if provided
    if user_context:
        base_prompt += f"""

USER CONTEXT: The user provided this context about the content: "{user_context}"
Please incorporate this context into your analysis and tagging."""

    # Add metadata information if available
    if metadata:
        base_prompt += f"""

ADDITIONAL METADATA: {metadata}
Use this information to enhance your analysis."""

    # Add the actual content
    content_section = f"""

CONTENT TO ANALYZE:
{content}"""
    
    # Add extracted text if different from main content
    if extracted_text and extracted_text != content:
        content_section += f"""

EXTRACTED TEXT (from file):
{extracted_text}"""

    # Add URL if provided
    if url:
        content_section += f"""

SOURCE URL: {url}"""

    format_instructions = """

Please respond in the following JSON format:
{
    "title": "Clear, descriptive title",
    "description": "Comprehensive summary",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "content_type": "specific_content_type",
    "platform": "platform_name_if_applicable"
}

Content types can be: personal_note, news_article, social_media, tutorial, recipe, research, document, image_text, receipt, identification, etc.
Platform can be: youtube, tiktok, twitter, instagram, linkedin, personal, etc. (use "personal" for user-generated content)"""

    return base_prompt + content_section + format_instructions

def get_text_analysis_prompt(text_content: str, user_context: str = None, title: str = None) -> str:
    """Generate a prompt for analyzing text content."""
    return get_content_analysis_prompt(
        content=text_content,
        user_context=user_context,
        media_type="text"
    )

def get_file_analysis_prompt(extracted_text: str, file_path: str, mime_type: str, 
                           metadata: dict, user_context: str = None) -> str:
    """Generate a prompt for analyzing file content."""
    media_type = "image" if mime_type.startswith("image/") else "document"
    
    return get_content_analysis_prompt(
        content=extracted_text,
        user_context=user_context,
        media_type=media_type,
        extracted_text=extracted_text,
        metadata=metadata
    )

def get_image_analysis_prompt(user_context: str = None) -> str:
    """Generate a prompt specifically for direct image analysis with multimodal LLM."""
    return f"""Analyze this image comprehensively for a personal knowledge management system.

Extract and provide:
1. **All visible text** (OCR functionality)
2. **Visual description** of what's shown in the image
3. **Content classification** (receipt, document, screenshot, photo, etc.)
4. **Key information** that would be useful for searching and retrieval
5. **Relevant tags** for categorization

{f"User Context: {user_context}" if user_context else ""}

Focus on making this content searchable and useful for future retrieval.

Respond in JSON format:
{{
    "extracted_text": "All text visible in the image",
    "image_description": "What's shown in the image",
    "title": "Descriptive title",
    "description": "Comprehensive summary combining text and visual elements",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "content_type": "receipt/document/screenshot/photo/etc",
    "platform": "personal",
    "key_information": ["important detail 1", "important detail 2"]
}}"""

def detect_intent_and_translate(text: str) -> dict:
    """
    Use LLM to detect user intent (search, save, general), translate to English, and provide a structured response.
    Returns a dict: {"intent": ..., "english_text": ..., "answer": ...}
    """
    prompt = '''
You are an AI assistant for a personal memory bot. Your job is to:
1. Detect the user's intent: "search", "save", or "general".
2. If the message is not in English, translate it to English.
3. For "search", return the English query.
4. For "save", return the English content.
5. For "general", return a suitable English answer.

**Instructions for distinguishing between 'search' and 'save':**
- If the message is a short noun phrase or a single concept (like "shopping list", "bank code", "my address"), it is likely a search: the user is trying to retrieve something they previously saved.
- If the message contains actual data, a list, details, or new information (e.g., "shopping list: cucumber, tomato, bread", "bank code 8483", "my address is 123 Main St"), it is a save: the user is providing new content to remember.
- If the message is ambiguous, prefer 'search' for short noun phrases and 'save' for messages with data or details.
- If you are not sure, use 'general' and suggest the user to add "find ..." or "save ..." to clarify their intent.

Always respond in this JSON format:
{
  "intent": "search|save|general",
  "english_text": "...",   // The translated or original English text
  "answer": "..."          // Only for 'general' intent, otherwise empty string
}

Guardrails:
- Only use the intents: "search", "save", or "general".
- If you are not sure, use "general" and suggest the user to add "find ..." or "save ..." to clarify their intent.
- Always output valid JSON and nothing else.
- If unsure, default to "general" with a helpful answer.

Examples:
User: "Find articles about AI"
Response: {"intent": "search", "english_text": "Find articles about AI", "answer": ""}

User: "רשימת קניות"
Response: {"intent": "search", "english_text": "shopping list", "answer": ""}

User: "רשימת קניות: מלפפון, עגבניה, מלח, לחם וחלב"
Response: {"intent": "save", "english_text": "shopping list: cucumber, tomato, salt, bread and milk", "answer": ""}

User: "bank code"
Response: {"intent": "search", "english_text": "bank code", "answer": ""}

User: "bank code 8483"
Response: {"intent": "save", "english_text": "bank code 8483", "answer": ""}

User: "open hours of Vibe gym"
Response: {"intent": "search", "english_text": "open hours of Vibe gym", "answer": ""}

User: "humous recipe with tofu and red beans"
Response: {"intent": "search", "english_text": "humous recipe with tofu and red beans", "answer": ""}

User: "my address"
Response: {"intent": "search", "english_text": "my address", "answer": ""}

User: "my address is 123 Main St, Springfield"
Response: {"intent": "save", "english_text": "my address is 123 Main St, Springfield", "answer": ""}

User: "project notes"
Response: {"intent": "search", "english_text": "project notes", "answer": ""}

User: "project notes: finish the report by Friday"
Response: {"intent": "save", "english_text": "project notes: finish the report by Friday", "answer": ""}

User: "test"
Response: {"intent": "general", "english_text": "test", "answer": "Hi! Please send me something to save or search."}
'''
    try:
        response = get_llm_response(prompt + f"\nUser: {text}\nResponse:")
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
        result = json.loads(json_str)
        # Validate required fields
        for field in ["intent", "english_text", "answer"]:
            if field not in result:
                result[field] = ""
        return result
    except Exception as e:
        logger.error(f"Error in detect_intent_and_translate: {str(e)} | Raw response: {response}")
        # Fallback: treat as general
        return {"intent": "general", "english_text": text, "answer": "Sorry, I couldn't understand your request. Please use 'find ...' or 'save ...' to clarify your intent."} 