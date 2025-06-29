import os
import logging
import re
import asyncio
from telegram import Update, File
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
from urllib.parse import urlparse
from app.utils.file_processor import FileProcessor

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def escape_markdown(text: str) -> str:
    """Escape special Markdown characters to prevent parsing errors."""
    if not text:
        return text
    
    # Escape special Markdown characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

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
        search_single_keywords = ['posts', 'articles', 'videos', 'images', 'content', 'decor', 'recipes', 'tutorials', 'programming', 'cooking', 'travel', 'fitness']
        if clean_text in search_single_keywords:
            return 'search'
        else:
            # Short messages are likely greetings or unclear
            return 'greeting'

async def perform_search(user_id: str, query: str, message) -> None:
    """Perform search and send results to user."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={
                "user_id": user_id,
                "query": query,
                "top_k": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            
            if not results:
                await message.reply_text(f"🔍 No results found for: *{escape_markdown(query)}*", parse_mode='Markdown')
                return
            
            reply_text = f"🔍 **Search Results for:** {escape_markdown(query)}\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Untitled')
                description = result.get('description', '')
                tags = result.get('tags', [])
                similarity = result.get('similarity_score', 0)
                url = result.get('url', '')
                media_type = result.get('media_type', 'url')
                
                reply_text += f"**{i}\\. {escape_markdown(title)}**\n"
                
                if description:
                    # Truncate long descriptions
                    desc_preview = description[:150] + "..." if len(description) > 150 else description
                    reply_text += f"📝 {escape_markdown(desc_preview)}\n"
                
                if tags:
                    reply_text += f"🏷️ {escape_markdown(', '.join(tags[:3]))}\n"
                
                # Add media type indicator
                if media_type == 'url' and url:
                    reply_text += f"🔗 {escape_markdown(url)}\n"
                elif media_type == 'text':
                    reply_text += "📝 Text Note\n"
                elif media_type == 'image':
                    reply_text += "📸 Image\n"
                elif media_type == 'document':
                    reply_text += "📄 Document\n"
                
                reply_text += f"📊 Relevance: {similarity:.2f}\n\n"
            
            # Split message if too long
            if len(reply_text) > 4000:
                # Send first part
                await message.reply_text(reply_text[:4000] + "...", parse_mode='Markdown')
                # Send remaining results
                remaining_text = f"🔍 **More Results:**\n\n" + reply_text[4000:]
                if len(remaining_text) > 4000:
                    remaining_text = remaining_text[:4000] + "..."
                await message.reply_text(remaining_text, parse_mode='Markdown')
            else:
                await message.reply_text(reply_text, parse_mode='Markdown')
        else:
            await message.reply_text(f"❌ Search error: {response.text}")
            
    except Exception as e:
        logger.error(f"Error performing search for user {user_id}: {str(e)}")
        await message.reply_text("❌ Error performing search. Please try again.")

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
    welcome_message = """
🧠 **Welcome to Memora - Your AI-Powered Memory Assistant!**

I can help you **save** and **search** different types of content:

## **💾 SAVING CONTENT**
📝 **Text Notes**: Send me meaningful text and I'll save it
🔗 **URLs**: Send links with optional context: "https://example.com this is for my project"
📸 **Images**: Upload photos, receipts, documents - I'll analyze them with AI vision
📄 **Documents**: Send PDF, Word docs, or text files for processing

## **🔍 SEARCHING CONTENT**
Just ask me naturally! I can understand search requests like:
• "Find posts about home decor"
• "Show me articles on Python programming"
• "Do you have any videos about cooking?"
• "Look for content related to AI"
• "What did I save about travel?"

## **📋 COMMANDS**
• `/search [query]` - Explicit search command
• `/stats` - View your saved content statistics

## **✨ SMART FEATURES**
• **Intelligent Intent Detection**: I automatically understand if you want to save or search
• **AI Vision**: Advanced image analysis without blurry OCR
• **Context-Aware**: Add descriptions to your content for better organization
• **Natural Language**: Talk to me normally - no complex commands needed

## **💡 EXAMPLES**
**Saving:**
• "Remember to buy groceries tomorrow"
• "https://github.com/example/repo useful Python library"
• [Upload a receipt photo]

**Searching:**
• "home decor posts"
• "find my Python tutorials"
• "show me cooking videos"

Just start typing - I'm smart enough to know what you want! 🚀
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle different types of messages (text, URLs, files)."""
    user_id = str(update.effective_user.id)
    message = update.message
    
    try:
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
    """Handle text messages (URLs, search queries, or content to save)."""
    text = update.message.text
    message = update.message
    
    # Detect user intent
    intent = detect_user_intent(text)
    
    if intent == 'url':
        # Handle URL with context
        url, user_context = extract_url_and_context(text)
        
        if url and is_valid_url(url):
            await message.reply_text("🔗 Processing URL...")
            
            try:
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
                    reply_text = f"✅ **Saved URL Successfully!**\n\n"
                    reply_text += f"📌 **Title:** {result.get('title', 'N/A')}\n"
                    reply_text += f"📝 **Description:** {result.get('description', 'N/A')}\n"
                    reply_text += f"🏷️ **Tags:** {', '.join(result.get('tags', []))}\n"
                    if user_context:
                        reply_text += f"💭 **Your Context:** {user_context}"
                    
                    await message.reply_text(reply_text, parse_mode='Markdown')
                else:
                    await message.reply_text(f"❌ Error processing URL: {response.text}")
                    
            except requests.exceptions.Timeout:
                await message.reply_text("⏰ Request timed out. The URL might be taking too long to process.")
            except Exception as e:
                logger.error(f"Error processing URL for user {user_id}: {str(e)}")
                await message.reply_text("❌ Error processing URL. Please try again.")
        else:
            await message.reply_text("❌ Invalid URL format. Please send a valid URL.")
    
    elif intent == 'search':
        # Handle search query
        await perform_search(user_id, text, message)
    
    elif intent == 'save':
        # Handle text content to save
        await message.reply_text("💾 Saving your content...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/save-text",
                json={
                    "user_id": user_id,
                    "text_content": text,
                    "user_context": None
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                reply_text = f"✅ **Content Saved Successfully!**\n\n"
                reply_text += f"📌 **Title:** {result.get('title', 'N/A')}\n"
                reply_text += f"📝 **Description:** {result.get('description', 'N/A')}\n"
                reply_text += f"🏷️ **Tags:** {', '.join(result.get('tags', []))}"
                
                await message.reply_text(reply_text, parse_mode='Markdown')
            else:
                await message.reply_text(f"❌ Error saving content: {response.text}")
                
        except requests.exceptions.Timeout:
            await message.reply_text("⏰ Request timed out while saving content.")
        except Exception as e:
            logger.error(f"Error saving text for user {user_id}: {str(e)}")
            await message.reply_text("❌ Error saving content. Please try again.")
    
    else:  # intent == 'greeting'
        # Handle casual messages - provide helpful response without saving
        casual_responses = [
            "👋 Hi there! Send me content you'd like to save, or use /search to find something!",
            "🤖 Hello! I'm here to help you save and organize content. Try sharing a URL or some text!",
            "✨ Hey! I can help you save articles, videos, notes, and more. What would you like to do?",
            "🧠 Hi! I'm your memory assistant. Share something interesting or search your saved content!"
        ]
        
        import random
        response = random.choice(casual_responses)
        await message.reply_text(response)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Handle document uploads."""
    document = update.message.document
    message = update.message
    caption = message.caption or ""
    
    # Check file size (50MB limit)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if document.file_size > MAX_FILE_SIZE:
        size_mb = document.file_size / (1024 * 1024)
        await message.reply_text(f"❌ File too large ({size_mb:.1f}MB). Maximum size is 50MB.")
        return
    
    # Check if file type is supported
    supported_types = {
        'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword', 'text/plain', 'text/csv'
    }
    
    if document.mime_type not in supported_types:
        await message.reply_text(f"❌ Unsupported file type: {document.mime_type}")
        return
    
    await message.reply_text("📄 Processing document...")
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()
        
        # Send to backend for processing
        files = {'file': (document.file_name, bytes(file_data), document.mime_type)}
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
            reply_text = f"✅ **Document Saved Successfully!**\n\n"
            reply_text += f"📁 **File:** {document.file_name}\n"
            reply_text += f"📌 **Title:** {result.get('title', 'N/A')}\n"
            reply_text += f"📝 **Description:** {result.get('description', 'N/A')}\n"
            reply_text += f"🏷️ **Tags:** {', '.join(result.get('tags', []))}\n"
            if caption:
                reply_text += f"💭 **Your Context:** {caption}"
            
            await message.reply_text(reply_text, parse_mode='Markdown')
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
            reply_text = f"✅ **Image Analyzed Successfully!**\n\n"
            reply_text += f"📌 **Title:** {result.get('title', 'N/A')}\n"
            reply_text += f"📝 **Description:** {result.get('description', 'N/A')}\n"
            reply_text += f"🏷️ **Tags:** {', '.join(result.get('tags', []))}\n"
            
            # Show extracted text preview if available
            extracted_text = result.get('extracted_text_preview', '')
            if extracted_text:
                reply_text += f"📋 **Extracted Text:** {extracted_text}\n"
            
            if caption:
                reply_text += f"💭 **Your Context:** {caption}"
            
            await message.reply_text(reply_text, parse_mode='Markdown')
        else:
            await message.reply_text(f"❌ Error processing image: {response.text}")
            
    except Exception as e:
        logger.error(f"Error processing photo for user {user_id}: {str(e)}")
        await message.reply_text("❌ Error processing image. Please try again.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search command."""
    user_id = str(update.effective_user.id)
    
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
    user_id = str(update.effective_user.id)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/user/{user_id}/stats",
            timeout=10
        )
        
        if response.status_code == 200:
            stats_data = response.json()
            
            reply_text = f"📊 **Your Memora Statistics**\n\n"
            reply_text += f"📝 **Total Items:** {stats_data.get('total_items', 0)}\n"
            reply_text += f"🔗 **URLs:** {stats_data.get('urls', 0)}\n"
            reply_text += f"📝 **Text Notes:** {stats_data.get('texts', 0)}\n"
            reply_text += f"📸 **Images:** {stats_data.get('images', 0)}\n"
            reply_text += f"📄 **Documents:** {stats_data.get('documents', 0)}\n\n"
            
            if stats_data.get('top_tags'):
                reply_text += f"🏷️ **Top Tags:**\n"
                for tag, count in stats_data['top_tags']:
                    reply_text += f"  • {tag} ({count})\n"
            
            await update.message.reply_text(reply_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not retrieve statistics.")
            
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {str(e)}")
        await update.message.reply_text("❌ Error retrieving statistics.")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stats", stats))
    
    # Handle all types of messages
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL, 
        handle_message
    ))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 