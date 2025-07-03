import os
import logging
import re
import asyncio
from telegram import Update, File, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import json
from urllib.parse import urlparse
from app.utils.file_processor import FileProcessor
from io import BytesIO
from app.utils.llm import detect_intent_and_translate

# User Profile imports (optional)
try:
    from app.services.user_profile_service import UserProfileService
    from app.models.user_profile import TelegramUserData, AuthProvider, UpdateUserProfileRequest
    PROFILES_AVAILABLE = True
except ImportError:
    PROFILES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Log profile system availability after logger is configured
if not PROFILES_AVAILABLE:
    logger.warning("User profile system not available - running in basic mode")

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7918946951:AAGZRHNAn-bhzMYQ_QetQelM_9B5AoHxNPg")

# Dynamic backend URL detection for different environments
def get_backend_url():
    """Get the appropriate backend URL based on the environment."""
    # Check if we're running on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        # On Railway, use localhost since both services run in the same container
        return "http://localhost:" + os.getenv("PORT", "8001")
    
    # Check if BACKEND_URL is explicitly set (for other cloud providers or custom setups)
    if os.getenv("BACKEND_URL"):
        return os.getenv("BACKEND_URL")
    
    # Check if we're running in Docker (docker-compose)
    if os.getenv("DATABASE_URL") and "postgres" in os.getenv("DATABASE_URL", ""):
        return "http://memora:8001"  # Docker service name
    
    # Default to localhost for local development
    return "http://localhost:8001"

BACKEND_URL = get_backend_url()
logger.info(f"Using backend URL: {BACKEND_URL}")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Initialize file processor
file_processor = FileProcessor()

# Enhanced user management with profiles (with fallback)
async def get_user_id_with_profile(update: Update) -> str:
    """Get user ID and optionally create/update user profile."""
    user_id = str(update.effective_user.id)
    
    if not PROFILES_AVAILABLE:
        return user_id
    
    try:
        user = update.effective_user
        
        # Create Telegram user data
        telegram_data = TelegramUserData(
            telegram_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            language_code=user.language_code,
            is_bot=user.is_bot,
            is_premium=getattr(user, 'is_premium', False)
        )
        
        # Create or update user profile via service
        with UserProfileService() as service:
            profile = service.create_from_telegram(telegram_data)
            logger.info(f"User profile ready for {profile.display_name or user_id}")
            
        return user_id
        
    except Exception as e:
        logger.error(f"Error managing user profile: {str(e)}")
        # Fallback to basic user ID for compatibility
        return user_id

async def track_activity(user_id: str, activity_type: str, activity_data: dict = None):
    """Track user activity with the profile service (optional)."""
    if not PROFILES_AVAILABLE:
        return
        
    try:
        with UserProfileService() as service:
            service.update_activity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                source_platform="telegram"
            )
    except Exception as e:
        logger.error(f"Error tracking activity for user {user_id}: {str(e)}")
        # Don't fail the main operation if activity tracking fails

def detect_user_intent(text: str) -> str:
    """
    Detect user intent from message text.
        
    Returns:
        'search' - User wants to search for content
        'save' - User wants to save content
        'greeting' - Casual greeting/conversation
        'url' - Contains URL (handled separately)
    """
    # Remove extra whitespace and convert to lowercase for analysis
    clean_text = text.strip().lower()
    
    # First check for URLs (highest priority)
    if re.search(r'https?://', text):
        return 'url'
    
    # Check for explicit search intent patterns
    search_patterns = [
        # Direct search requests
        r'^(find|search|look for|show me|get me|where is|do you have)',
        r'^(what.*saved|what.*remember|what.*stored)',
        r'(find|search|look for|show me|get me).*\b(post|article|video|image|document|note|content|item)',
        
        # Question patterns that indicate search
        r'^(what|where|when|how|which).*\?',
        r'^(do you have|is there|are there|can you find)',
        r'^(show|display|list).*\b(all|my|the)',
        
        # Content-specific search patterns
        r'\b(posts?|articles?|videos?|images?|documents?|notes?|content|items?)\b.*\b(about|on|related to|regarding)',
        r'\b(anything|something|content|items?)\b.*(about|on|related to|regarding)',
        
        # Memory/recall patterns - but NOT when starting with "remember to"
        r'^(recall|what was|remind me)',
        r'\b(saved|stored|remembered)\b.*\b(about|on|related to|regarding)',
    ]
    
    for pattern in search_patterns:
        if re.search(pattern, clean_text):
            return 'search'
    
    # Check for casual/greeting patterns
    greeting_patterns = [
        r'^(hi|hello|hey|yo|sup|hiya|howdy)$',
        r'^(good morning|good afternoon|good evening|good night)$',
        r'^(morning|afternoon|evening|night)$',
        r'^(ok|okay|yes|no|yeah|yep|nope|sure|thanks|thank you|thx)$',
        r'^(cool|nice|great|awesome|perfect|sounds good)$',
        r'^(test|testing|hello world)$',
        r'^(what|why|how|when|where|who)$',
        r'^[😀-🙏🏻]+$',  # Just emojis
        r'^(lol|lmao|haha|hehe|hmm|uhh|umm)$',
    ]
    
    for pattern in greeting_patterns:
        if re.search(pattern, clean_text):
            return 'greeting'
    
    # Check for save intent patterns
    save_patterns = [
        # Explicit save requests - including "remember to"
        r'^(save|remember|store|keep|note)',
        r'^(i want to|i need to|let me).*(save|remember|store|keep|note)',
        
        # Imperative statements that suggest saving
        r'^(this is|here is|check this)',
        r'^(important|reminder|todo|task)',
        
        # Personal notes/thoughts
        r'^(i think|i believe|my opinion|my thought)',
        r'^(idea:|thought:|note:|reminder:)',
        
        # Content sharing with context
        r'\b(for later|for reference|worth remembering|important)',
        r'\b(project|work|study|research)',
    ]
    
    for pattern in save_patterns:
        if re.search(pattern, clean_text):
            return 'save'
    
    # Heuristic: Longer, descriptive messages are likely to be content worth saving
    # But shorter queries might be searches
    if len(clean_text) > 50:
        # Long messages are more likely to be content to save
        return 'save'
    elif len(clean_text) > 10:
        # Medium messages - check for search-like keywords
        search_keywords = ['posts', 'find', 'search', 'look for', 'show me', 'get me', 'where is', 'do you have', 'articles', 'videos', 'images', 'content', 'about', 'related', 'decor', 'recipes', 'tutorials']
        if any(keyword in clean_text for keyword in search_keywords):
            return 'search'
        else:
            return 'save'
    else:
        # Short messages - check if they're search-like single keywords
        search_single_keywords = ['find', 'search', 'look for','posts', 'articles', 'videos', 'images', 'content', 'decor', 'recipes', 'tutorials', 'programming', 'cooking', 'travel', 'fitness']
        if clean_text in search_single_keywords:
            return 'search'
        else:
            # Short messages are likely greetings or unclear
            return 'greeting'

async def send_file_to_user(message, item_data: dict, user_id: str) -> bool:
    """
    Send a file from search results back to the user.
    
    Args:
        message: Telegram message object
        item_data: Item data from search results
        user_id: User ID
        
    Returns:
        True if file was sent successfully, False otherwise
    """
    try:
        if not item_data.get('file_path') or not item_data.get('id'):
            logger.warning(f"Missing file_path or id in item_data: {item_data}")
            return False
            
        item_id = item_data['id']
        file_path = item_data['file_path']
        logger.info(f"Attempting to send file for item {item_id} with path: {file_path}")
        
        # Get file from backend
        file_url = f"{BACKEND_URL}/file/{item_id}"
        params = {"user_id": user_id}
        
        logger.info(f"Making request to: {file_url} with params: {params}")
        
        response = requests.get(
            file_url,
            params=params,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get file from backend: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            
            # Try debug endpoint to understand the issue
            try:
                debug_response = requests.get(
                    f"{BACKEND_URL}/debug/file/{item_id}",
                    params={"user_id": user_id},
                    timeout=10
                )
                if debug_response.status_code == 200:
                    debug_info = debug_response.json()
                    logger.error(f"Debug info: {debug_info}")
                else:
                    logger.error(f"Debug endpoint also failed: {debug_response.status_code}")
            except Exception as debug_e:
                logger.error(f"Could not get debug info: {debug_e}")
            
            return False
        
        # Create BytesIO object from response content
        file_data = BytesIO(response.content)
        file_data.name = item_data.get('title', 'file')
        
        media_type = item_data.get('media_type', '')
        mime_type = item_data.get('mime_type', '')
        
        logger.info(f"Successfully downloaded file, size: {len(response.content)} bytes")
        logger.info(f"Media type: {media_type}, MIME type: {mime_type}")
        
        # Send based on media type
        if media_type == 'image' or mime_type.startswith('image/'):
            await message.reply_photo(
                photo=file_data,
                caption=f"📸 {item_data.get('title', 'Image')}\n📝 {item_data.get('description', '')[:100]}..."
            )
            logger.info("Sent file as photo")
        else:
            # Send as document
            await message.reply_document(
                document=file_data,
                caption=f"📄 {item_data.get('title', 'Document')}\n📝 {item_data.get('description', '')[:100]}..."
            )
            logger.info("Sent file as document")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending file to user: {str(e)}")
        return False

async def perform_search(user_id: str, query: str, message) -> None:
    """Perform search and send results to user."""
    try:
        # Track search activity
        await track_activity(user_id, "search", {
            "query": query,
            "query_length": len(query),
            "timestamp": message.date.isoformat() if message.date else None
        })
        
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={
                "user_id": user_id,
                "query": query,
                "top_k": 20
            },
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            
            # Track search results
            await track_activity(user_id, "search_results", {
                "query": query,
                "results_count": len(results),
                "has_results": len(results) > 0
            })
            
            # Filter results by similarity threshold (0.35 minimum)
            filtered_results = [result for result in results if result.get('similarity_score', 0) >= 0.35]
            
            if not filtered_results:
                await message.reply_text(f"🔍 No relevant results found for: {query}\n💡 Try using different keywords or be more specific.")
                return
            
            # Check if there are any non-text items to show in summary
            non_text_results = [result for result in filtered_results if result.get('media_type') != 'text']
            
            if non_text_results:
                reply_text = f"🔍 Search Results for: {query}\n\n"
                for i, result in enumerate(filtered_results, 1):
                    title = result.get('title', 'Untitled')
                    description = result.get('description', '')
                    tags = result.get('tags', [])
                    similarity = result.get('similarity_score', 0)
                    url = result.get('url', '')
                    media_type = result.get('media_type', 'url')
                    content_data = result.get('content_data', '')
                    item_id = result.get('id')

                    # Only show non-text items in the main results
                    if media_type != 'text':
                        result_text = f"{i}. {title}\n"
                        if description:
                            desc_preview = description[:150] + "..." if len(description) > 150 else description
                            result_text += f"📝 {desc_preview}\n"
                        if tags:
                            result_text += f"🏷️ {', '.join(tags[:3])}\n"
                        if media_type == 'url' and url:
                            result_text += f"🔗 {url}\n"
                        elif media_type == 'document':
                            result_text += "📄 Document\n"
                        elif media_type == 'image':
                            result_text += "🖼️ Image\n"
                        result_text += f"📊 Relevance: {similarity:.2f}\n"

                        # Inline delete button
                        if item_id:
                            keyboard = InlineKeyboardMarkup([
                                [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{item_id}")]
                            ])
                            await message.reply_text(result_text, reply_markup=keyboard)
                        else:
                            await message.reply_text(result_text)

            # Now send files for results that have them (images and documents)
            files_sent = 0
            for result in filtered_results:
                if result.get('media_type') in ['image', 'document'] and result.get('file_path'):
                    if files_sent < 3:  # Limit to 3 files to avoid spam
                        success = await send_file_to_user(message, result, user_id)
                        if success:
                            files_sent += 1
                        await asyncio.sleep(0.5)
                    else:
                        break
            if files_sent > 0:
                await message.reply_text(f"📎 Sent {files_sent} file(s) from your search results!")
            
            # Send text notes as separate copy-able messages
            text_notes_sent = 0
            for i, result in enumerate(filtered_results, 1):
                if result.get('media_type') == 'text' and result.get('content_data'):
                    if text_notes_sent < 10:  # Limit to 10 text notes to avoid spam
                        title = result.get('title', 'Text Note')
                        content_data = result.get('content_data', '')
                        tags = result.get('tags', [])
                        item_id = result.get('id')
                        
                        # Send as a separate message for easy copying
                        copy_text = f"📝 **{title}**\n\n{content_data}"
                        if tags:
                            copy_text += f"\n\n🏷️ Tags: {', '.join(tags[:3])}"
                        
                        # Add delete button for text notes too
                        if item_id:
                            keyboard = InlineKeyboardMarkup([
                                [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{item_id}")]
                            ])
                            await message.reply_text(copy_text, parse_mode='Markdown', reply_markup=keyboard)
                        else:
                            await message.reply_text(copy_text, parse_mode='Markdown')
                        
                        text_notes_sent += 1
                        await asyncio.sleep(0.3)  # Small delay between messages
                    else:
                        break
            
        else:
            await message.reply_text(f"❌ Search failed: {response.text}")
    except requests.exceptions.Timeout:
        await message.reply_text("⏰ Search timed out. Please try again.")
    except Exception as e:
        logger.error(f"Error performing search for user {user_id}: {str(e)}")
        await message.reply_text("❌ Search error. Please try again.")

def extract_url_and_context(text: str) -> tuple[str, str]:
    """
    Extract URL and user context from a message.
    
    Args:
        text: The message text
        
    Returns:
        Tuple of (url, user_context) where user_context is the remaining text
    """
    # URL pattern - more comprehensive
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    if urls:
        # Use the first URL found
        url = urls[0]
        # Remove the URL from text to get context
        user_context = text.replace(url, '').strip()
        return url, user_context
    
    return None, text

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = await get_user_id_with_profile(update)
    
    # Track the start command usage
    await track_activity(user_id, "start_command", {
        "command": "/start",
        "is_new_user": True
    })
    
    # Get user profile for personalization
    display_name = update.effective_user.first_name
    if PROFILES_AVAILABLE:
        try:
            with UserProfileService() as service:
                profile = service.get_profile(user_id)
                if profile:
                    display_name = profile.display_name or display_name
        except:
            pass  # Use default name if profile fetch fails
    
    # Build the welcome message dynamically
    profile_cmd = "\n• /profile - View your profile information" if PROFILES_AVAILABLE else ""
    profile_feature = "\n• Personal Profile: Track your usage and preferences" if PROFILES_AVAILABLE else ""
    
    welcome_message = f"""
🧠 Welcome to Memora{f', {display_name}' if display_name else ''}!
Your AI-Powered Memory Assistant

I can help you save and search different types of content:

💾 SAVING CONTENT
📝 Text Notes: Send me meaningful text and I'll save it
🔗 URLs: Send links with optional context: "https://example.com this is for my project"
📸 Images: Upload photos, receipts, documents - I'll analyze them with AI vision
📄 Documents: Send PDF, Word docs, or text files for processing

🔍 SEARCHING CONTENT
Just ask me naturally! I can understand search requests like:
• "Find posts about home decor"
• "Show me articles on Python programming"
• "Do you have any videos about cooking?"
• "Look for content related to AI"
• "What did I save about travel?"

📋 COMMANDS
• /search [query] - Explicit search command
• /stats - View your saved content statistics{profile_cmd}

✨ SMART FEATURES
• Intelligent Intent Detection: I automatically understand if you want to save or search
• AI Vision: Advanced image analysis without blurry OCR
• Context-Aware: Add descriptions to your content for better organization
• Natural Language: Talk to me normally - no complex commands needed{profile_feature}

💡 EXAMPLES
Saving:
• "Remember to buy groceries tomorrow"
• "https://github.com/example/repo useful Python library"
• [Upload a receipt photo]

Searching:
• "home decor posts"
• "find my Python tutorials"
• "show me cooking videos"

Just start typing - I'm smart enough to know what you want! 🚀
    """
    
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle different types of messages (text, URLs, files)."""
    user_id = await get_user_id_with_profile(update)
    message = update.message
    
    try:
        # Track general message activity
        await track_activity(user_id, "message_received", {
            "message_type": "text" if message.text else "media",
            "has_caption": bool(message.caption),
            "message_length": len(message.text) if message.text else 0
        })
        
        # Handle different message types
        if message.document:
            await handle_document(update, context, user_id)
        elif message.photo:
            await handle_photo(update, context, user_id)
        elif message.text:
            await handle_text_message(update, context, user_id)
        else:
            await message.reply_text("❌ Sorry, I can only process text, images, and documents right now.")
            
    except Exception as e:
        logger.error(f"Error handling message from user {user_id}: {str(e)}")
        await message.reply_text("❌ Sorry, there was an error processing your message. Please try again.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    text = update.message.text
    message = update.message

    # Handle greetings, thanks, farewells with regex and predefined answers
    greeting_patterns = [
        r'^(hi|hello|hey|yo|sup|hiya|howdy)[!,. ]*$',
        r'^(good morning|good afternoon|good evening|good night)[!,. ]*$',
        r'^(morning|afternoon|evening|night)[!,. ]*$',
    ]
    thanks_patterns = [
        r'^(thanks|thank you|thx|ty|appreciate it)[!,. ]*$',
    ]
    farewell_patterns = [
        r'^(bye|goodbye|see you|cya|later|take care)[!,. ]*$',
    ]

    clean_text = text.strip().lower()
    for pattern in greeting_patterns:
        if re.match(pattern, clean_text):
            await message.reply_text("👋 Hi there! How can I help you today?")
            return
    for pattern in thanks_patterns:
        if re.match(pattern, clean_text):
            await message.reply_text("🙏 You're welcome! If you need anything else, just ask.")
            return
    for pattern in farewell_patterns:
        if re.match(pattern, clean_text):
            await message.reply_text("👋 Goodbye! Have a great day!")
            return

    # Detect user intent for URLs first (keep existing logic with fallback)
    if re.search(r'https?://', text):
        url, user_context = extract_url_and_context(text)
        if url and is_valid_url(url):
            await message.reply_text("🔗 Processing URL...")
            try:
                # Track URL processing
                await track_activity(user_id, "save_url", {
                    "url": url,
                    "has_context": bool(user_context),
                    "context_length": len(user_context) if user_context else 0
                })
                
                response = requests.post(
                    f"{BACKEND_URL}/extract",
                    json={
                        "user_id": user_id,
                        "url": url,
                        "user_context": user_context if user_context else None
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    
                    # Track successful URL save
                    await track_activity(user_id, "save_success", {
                        "item_id": result.get('id'),
                        "content_type": "url",
                        "url": url
                    })
                    
                    title = result.get('title', 'N/A')
                    description = result.get('description', 'N/A')
                    tags = result.get('tags', [])
                    if len(title) > 100:
                        title = title[:97] + "..."
                    if len(description) > 300:
                        description = description[:297] + "..."
                    reply_text = "✅ Saved URL Successfully!\n\n"
                    reply_text += f"📌 Title: {title}\n"
                    reply_text += f"📝 Description: {description}\n"
                    reply_text += f"🏷️ Tags: {', '.join(tags[:5]) if tags else 'None'}\n"
                    if user_context:
                        context_text = user_context[:150] + "..." if len(user_context) > 150 else user_context
                        reply_text += f"💭 Your Context: {context_text}"
                    await message.reply_text(reply_text)
                    return  # Successfully processed URL, exit function
                else:
                    # URL extraction failed - fall back to saving as text note
                    logger.warning(f"URL extraction failed for {url}: {response.text}")
                    await message.reply_text("⚠️ URL extraction failed, saving as text note instead...")
                    # Continue to save as text note (fall through to text saving logic)
            except requests.exceptions.Timeout:
                # Timeout - fall back to saving as text note
                logger.warning(f"URL extraction timed out for {url}")
                await message.reply_text("⏰ URL extraction timed out, saving as text note instead...")
                # Continue to save as text note (fall through to text saving logic)
            except Exception as e:
                # Other errors - fall back to saving as text note
                logger.error(f"Error processing URL {url}: {str(e)}")
                await message.reply_text("❌ URL extraction error, saving as text note instead...")
                # Continue to save as text note (fall through to text saving logic)
        else:
            # Invalid URL format - save as text note
            await message.reply_text("❌ Invalid URL format, saving as text note instead...")
            # Continue to save as text note (fall through to text saving logic)
        
        # If we reach here, URL processing failed - save the entire message as text
        await save_text_content(message, user_id, text)
        return

    # Use LLM router for all other text messages
    try:
        llm_result = detect_intent_and_translate(text)
        intent = llm_result.get("intent", "general")
        english_text = llm_result.get("english_text", text)
        answer = llm_result.get("answer", "")
    except Exception as e:
        logger.error(f"LLM router error: {str(e)}")
        await message.reply_text("❌ Sorry, there was an error understanding your message. Please try again.")
        return

    if intent == 'search':
        await perform_search(user_id, english_text, message)
    elif intent == 'save':
        await save_text_content(message, user_id, text)
    else:  # intent == 'general'
        if answer:
            await message.reply_text(answer)
        else:
            await message.reply_text("🤖 I'm not sure what you want to do. Please use 'find ...' to search or 'save ...' to save content.")

async def save_text_content(message, user_id: str, text: str) -> None:
    """Helper function to save text content."""
    await message.reply_text("💾 Saving your content...")
    
    try:
        # Track save activity
        await track_activity(user_id, "save_text", {
            "content_length": len(text),
            "timestamp": message.date.isoformat() if message.date else None
        })
        
        response = requests.post(
            f"{BACKEND_URL}/save-text",
            json={
                "user_id": user_id,
                "text_content": text,  # Use original text instead of english_text
                "user_context": None
            },
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            
            # Track successful save
            await track_activity(user_id, "save_success", {
                "item_id": result.get('id'),
                "content_type": "text",
                "tags_count": len(result.get('tags', []))
            })
            
            title = result.get('title', 'N/A')
            description = result.get('description', 'N/A')
            tags = result.get('tags', [])
            item_id = result.get('id')
            original_text = result.get('original_text', '')
            
            # Use original text for display instead of LLM description
            if len(title) > 100:
                title = title[:97] + "..."
            
            reply_text = "✅ Content Saved Successfully!\n\n"
            reply_text += f"📌 Title: {title}\n"
            
            # Show brief confirmation instead of full text
            if original_text:
                text_preview = original_text[:100] + "..." if len(original_text) > 100 else original_text
                reply_text += f"📝 Preview: {text_preview}\n"
            else:
                # Fallback to description if original text not available
                if len(description) > 300:
                    description = description[:297] + "..."
                reply_text += f"📝 Description: {description}\n"
                
            reply_text += f"🏷️ Tags: {', '.join(tags[:5]) if tags else 'None'}"
            # Inline delete button for saved item
            if item_id:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{item_id}")]
                ])
                await message.reply_text(reply_text, reply_markup=keyboard)
            else:
                await message.reply_text(reply_text)
        else:
            await message.reply_text(f"❌ Error saving content: {response.text}")
    except requests.exceptions.Timeout:
        await message.reply_text("⏰ Request timed out while saving content.")
    except Exception as e:
        logger.error(f"Error saving text for user {user_id}: {str(e)}")
        await message.reply_text("❌ Error saving content. Please try again.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Handle document uploads."""
    document = update.message.document
    message = update.message
    caption = message.caption or ""
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if document.file_size > MAX_FILE_SIZE:
        size_mb = document.file_size / (1024 * 1024)
        await message.reply_text(f"❌ File too large ({size_mb:.1f}MB). Maximum size is 50MB.")
        return
    supported_types = {
        'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword', 'text/plain', 'text/csv'
    }
    if document.mime_type not in supported_types:
        await message.reply_text(f"❌ Unsupported file type: {document.mime_type}")
        return
    await message.reply_text("📄 Processing document...")
    try:
        # Track document upload
        await track_activity(user_id, "upload_document", {
            "filename": document.file_name,
            "mime_type": document.mime_type,
            "file_size": document.file_size
        })
        
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()
        files = {'file': (document.file_name, bytes(file_data), document.mime_type)}
        data = {
            'user_id': user_id,
            'user_context': caption if caption else None
        }
        response = requests.post(
            f"{BACKEND_URL}/upload-file",
            files=files,
            data=data,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            
            # Track successful upload
            await track_activity(user_id, "save_success", {
                "item_id": result.get('id'),
                "content_type": "document",
                "filename": document.file_name
            })
            
            filename = document.file_name
            title = result.get('title', 'N/A')
            description = result.get('description', 'N/A')
            tags = result.get('tags', [])
            if len(filename) > 50:
                filename = filename[:47] + "..."
            if len(title) > 100:
                title = title[:97] + "..."
            if len(description) > 300:
                description = description[:297] + "..."
            reply_text = "✅ Document Saved Successfully!\n\n"
            reply_text += f"📁 File: {filename}\n"
            reply_text += f"📌 Title: {title}\n"
            reply_text += f"📝 Description: {description}\n"
            reply_text += f"🏷️ Tags: {', '.join(tags[:5]) if tags else 'None'}\n"
            if caption:
                context_text = caption[:150] + "..." if len(caption) > 150 else caption
                reply_text += f"💭 Your Context: {context_text}"
            await message.reply_text(reply_text)
        else:
            await message.reply_text(f"❌ Error processing document: {response.text}")
    except Exception as e:
        logger.error(f"Error processing document for user {user_id}: {str(e)}")
        await message.reply_text("❌ Error processing document. Please try again.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Handle photo uploads using multimodal AI vision."""
    # Get the largest photo size
    photo = update.message.photo[-1]
    message = update.message
    caption = message.caption or ""
    
    # Check file size
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if photo.file_size > MAX_FILE_SIZE:
        size_mb = photo.file_size / (1024 * 1024)
        await message.reply_text(f"❌ Image too large ({size_mb:.1f}MB). Maximum size is 50MB.")
        return
    
    await message.reply_text("📸 Analyzing image with AI vision...")
    
    try:
        # Track image upload
        await track_activity(user_id, "upload_image", {
            "file_size": photo.file_size,
            "has_caption": bool(caption)
        })
        
        # Download photo
        file = await context.bot.get_file(photo.file_id)
        file_data = await file.download_as_bytearray()
        
        # Generate filename
        filename = f"photo_{photo.file_id}.jpg"
        
        # Send to backend for processing
        files = {'file': (filename, bytes(file_data), 'image/jpeg')}
        data = {
            'user_id': user_id,
            'user_context': caption if caption else None
        }
        
        # Use requests to upload file
        response = requests.post(
            f"{BACKEND_URL}/upload-file",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Track successful upload
            await track_activity(user_id, "save_success", {
                "item_id": result.get('id'),
                "content_type": "image"
            })
            
            # Use plain text formatting to avoid escape character issues
            title = result.get('title', 'N/A')
            description = result.get('description', 'N/A')
            tags = result.get('tags', [])
            
            # Truncate long content
            if len(title) > 100:
                title = title[:97] + "..."
            if len(description) > 300:
                description = description[:297] + "..."
            
            reply_text = "✅ Image Analyzed Successfully!\n\n"
            reply_text += f"📌 Title: {title}\n"
            reply_text += f"📝 Description: {description}\n"
            reply_text += f"🏷️ Tags: {', '.join(tags[:5]) if tags else 'None'}\n"
            
            if caption:
                context_text = caption[:150] + "..." if len(caption) > 150 else caption
                reply_text += f"💭 Your Context: {context_text}"
            
            await message.reply_text(reply_text)
        else:
            await message.reply_text(f"❌ Error processing image: {response.text}")
            
    except Exception as e:
        logger.error(f"Error processing photo for user {user_id}: {str(e)}")
        await message.reply_text("❌ Error processing image. Please try again.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search command."""
    user_id = await get_user_id_with_profile(update)
    
    # Get search query from command arguments
    query = ' '.join(context.args)
    
    if not query:
        await update.message.reply_text(
            "🔍 Please provide a search query.\n\n"
            "**Examples:**\n"
            "• `/search python tutorial`\n"
            "• `/search home decor posts`\n"
            "• `/search cooking videos`\n\n"
            "💡 **Tip:** You can also just type your search naturally without the `/search` command!", 
            parse_mode='Markdown'
        )
        return
    
    # Use the same search function as natural language search
    await perform_search(user_id, query, update.message)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    user_id = await get_user_id_with_profile(update)
    
    try:
        # Get stats from the API
        response = requests.get(
            f"{BACKEND_URL}/user/{user_id}/stats",
            timeout=10
        )
        
        if response.status_code == 200:
            api_stats = response.json()
            
            reply_text = f"📊 Your Memora Statistics\n\n"
            reply_text += f"📝 Content Overview:\n"
            reply_text += f"• Total Items: {api_stats.get('total_items', 0)}\n"
            reply_text += f"• URLs: {api_stats.get('urls', 0)}\n"
            reply_text += f"• Text Notes: {api_stats.get('texts', 0)}\n"
            reply_text += f"• Images: {api_stats.get('images', 0)}\n"
            reply_text += f"• Documents: {api_stats.get('documents', 0)}\n"
            
            # Add profile stats if available
            if PROFILES_AVAILABLE:
                try:
                    with UserProfileService() as service:
                        profile_stats = service.get_user_stats(user_id)
                        
                    reply_text += f"\n🔍 Activity Stats:\n"
                    reply_text += f"• Searches: {profile_stats.get('total_searches', 0)}\n"
                    reply_text += f"• Days Active: {profile_stats.get('days_active', 0)}\n"
                    
                    if profile_stats.get('last_active'):
                        reply_text += f"• Last Active: {profile_stats['last_active'].strftime('%B %d, %Y')}\n"
                except Exception as e:
                    logger.warning(f"Could not get profile stats: {e}")
            
            if api_stats.get('top_tags'):
                reply_text += f"\n🏷️ Top Tags:\n"
                for tag, count in api_stats['top_tags']:
                    # Escape special characters that might cause Markdown issues
                    safe_tag = str(tag).replace('*', '').replace('_', '').replace('[', '').replace(']', '')
                    reply_text += f"  • {safe_tag} ({count})\n"
            
            # Send without Markdown parsing to avoid errors
            await update.message.reply_text(reply_text)
        else:
            await update.message.reply_text("❌ Could not retrieve statistics.")
            
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {str(e)}")
        await update.message.reply_text("❌ Error retrieving statistics.")

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline delete button callback."""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data
    if data.startswith("delete:"):
        item_id = data.split(":", 1)[1]
        try:
            response = requests.post(
                f"{BACKEND_URL}/delete-item",
                json={"user_id": user_id, "item_id": item_id},
                timeout=10
            )
            if response.status_code == 200:
                await query.edit_message_text("🗑️ Item deleted!")
                # Track deletion activity
                await track_activity(user_id, "delete_item", {
                    "item_id": item_id,
                    "method": "inline_button"
                })
            else:
                await query.edit_message_text(f"❌ Failed to delete item: {response.text}")
        except Exception as e:
            await query.edit_message_text(f"❌ Error deleting item: {str(e)}")

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all items for the user."""
    user_id = await get_user_id_with_profile(update)
    try:
        response = requests.post(
            f"{BACKEND_URL}/delete-all-items",
            json={"user_id": user_id},
            timeout=20
        )
        if response.status_code == 200:
            result = response.json()
            await update.message.reply_text(f"🗑️ {result.get('message', 'All items deleted!')}")
            # Track mass deletion
            await track_activity(user_id, "delete_all_items", {
                "method": "command"
            })
        else:
            await update.message.reply_text(f"❌ Failed to delete all items: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting all items: {str(e)}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile information."""
    if not PROFILES_AVAILABLE:
        await update.message.reply_text("❌ Profile system not available.")
        return
        
    user_id = await get_user_id_with_profile(update)
    
    try:
        with UserProfileService() as service:
            profile = service.get_profile(user_id)
            
            if profile:
                # Debug: Check what data we have from Telegram
                telegram_user = update.effective_user
                logger.info(f"Telegram user data: ID={telegram_user.id}, username={telegram_user.username}, first_name={telegram_user.first_name}, last_name={telegram_user.last_name}")
                
                reply_text = f"👤 Your Profile\n\n"
                
                # Track what needs to be updated
                updates_needed = {}
                
                # Handle display name (first name)
                if profile.first_name:
                    reply_text += f"Name: {profile.first_name}"
                    if profile.last_name:
                        reply_text += f" {profile.last_name}"
                    reply_text += "\n"
                elif telegram_user.first_name:
                    reply_text += f"Name: {telegram_user.first_name}"
                    if telegram_user.last_name:
                        reply_text += f" {telegram_user.last_name}"
                    reply_text += " (updating...)\n"
                    updates_needed['first_name'] = telegram_user.first_name
                    if telegram_user.last_name:
                        updates_needed['last_name'] = telegram_user.last_name
                else:
                    reply_text += f"Name: Not set\n"
                
                # Handle missing last name even if first name exists
                if profile.first_name and not profile.last_name and telegram_user.last_name:
                    updates_needed['last_name'] = telegram_user.last_name
                    reply_text = reply_text.replace("Name: " + profile.first_name + "\n", 
                                                    f"Name: {profile.first_name} {telegram_user.last_name} (updating...)\n")
                
                # Handle missing first name if we have it from Telegram
                if not profile.first_name and telegram_user.first_name:
                    updates_needed['first_name'] = telegram_user.first_name
                
                # Better username handling
                if profile.username:
                    reply_text += f"Username: @{profile.username}\n"
                elif telegram_user.username:
                    reply_text += f"Username: @{telegram_user.username} (updating...)\n"
                    updates_needed['username'] = telegram_user.username
                else:
                    reply_text += f"Username: Not set (no @username in Telegram)\n"
                
                # Apply any needed updates
                if updates_needed:
                    try:
                        service.update_profile(user_id, UpdateUserProfileRequest(**updates_needed))
                        logger.info(f"Updated profile for user {user_id} with: {updates_needed}")
                    except Exception as e:
                        logger.error(f"Failed to update profile: {e}")
                
                reply_text += f"Language: {profile.primary_language.upper()}\n"
                reply_text += f"Country: {profile.country_code or 'Not set'}\n"
                reply_text += f"Member since: {profile.created_at.strftime('%B %Y')}\n"
                reply_text += f"Last active: {profile.last_active_at.strftime('%B %d, %Y') if profile.last_active_at else 'Today'}\n\n"
                
                reply_text += f"📊 Statistics:\n"
                reply_text += f"• Total items saved: {profile.total_items}\n"
                reply_text += f"• Searches performed: {profile.total_searches}\n"
                reply_text += f"• Days active: {profile.days_active}\n"
                
                if profile.is_premium:
                    reply_text += f"\n⭐ Premium Member"
                
                # Show connected auth providers
                if profile.auth_providers:
                    reply_text += f"\n\n🔗 Connected Accounts:\n"
                    for auth_provider in profile.auth_providers:
                        icon = "📱" if auth_provider.provider == "telegram" else "🔗"
                        status = " (Primary)" if auth_provider.is_primary else ""
                        reply_text += f"• {icon} {auth_provider.provider.title()}{status}\n"
                
                await update.message.reply_text(reply_text)
            else:
                await update.message.reply_text("❌ Could not retrieve profile information.")
                
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {str(e)}")
        await update.message.reply_text("❌ Error retrieving profile information.")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("deleteall", delete_all))
    if PROFILES_AVAILABLE:
        application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CallbackQueryHandler(handle_delete_callback))
    
    # Handle all types of messages
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL, 
        handle_message
    ))

    # Run the bot until the user presses Ctrl-C
    logger.info(f"Starting {'enhanced ' if PROFILES_AVAILABLE else ''}Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 