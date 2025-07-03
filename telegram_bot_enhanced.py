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

# User Profile imports
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import TelegramUserData, AuthProvider

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

# Enhanced user management with profiles
async def get_or_create_user_profile(update: Update) -> str:
    """Get or create user profile from Telegram update data."""
    try:
        user = update.effective_user
        user_id = str(user.id)
        
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
        return str(update.effective_user.id)

async def track_user_activity(user_id: str, activity_type: str, activity_data: dict = None):
    """Track user activity with the profile service."""
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

# Enhanced start command with profile integration
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = await get_or_create_user_profile(update)
    
    # Track the start command usage
    await track_user_activity(user_id, "start_command", {
        "command": "/start",
        "is_new_user": True  # This could be determined by checking if profile was just created
    })
    
    # Get user profile for personalization
    try:
        with UserProfileService() as service:
            profile = service.get_profile(user_id)
            display_name = profile.display_name if profile else update.effective_user.first_name
    except:
        display_name = update.effective_user.first_name
    
    welcome_message = f"""
🧠 **Welcome to Memora, {display_name}!**
*Your AI-Powered Memory Assistant*

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
• `/profile` - View your profile information

## **✨ SMART FEATURES**
• **Intelligent Intent Detection**: I automatically understand if you want to save or search
• **AI Vision**: Advanced image analysis without blurry OCR
• **Context-Aware**: Add descriptions to your content for better organization
• **Natural Language**: Talk to me normally - no complex commands needed
• **Personal Profile**: Track your usage and preferences

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

# Enhanced message handler with profile integration
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle different types of messages (text, URLs, files)."""
    user_id = await get_or_create_user_profile(update)
    message = update.message
    
    try:
        # Track general message activity
        await track_user_activity(user_id, "message_received", {
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

# Enhanced search function with activity tracking
async def perform_search(user_id: str, query: str, message) -> None:
    """Perform search and send results to user."""
    try:
        # Track search activity
        await track_user_activity(user_id, "search", {
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
            await track_user_activity(user_id, "search_results", {
                "query": query,
                "results_count": len(results),
                "has_results": len(results) > 0
            })
            
            # Filter results by similarity threshold (0.35 minimum)
            filtered_results = [result for result in results if result.get('similarity_score', 0) >= 0.35]
            
            if not filtered_results:
                await message.reply_text(f"🔍 No relevant results found for: {query}\n💡 Try using different keywords or be more specific.")
                return
            
            # Display search results (similar to original implementation)
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
                    item_id = result.get('id')

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
            
            # Send text notes as separate messages
            text_notes_sent = 0
            for i, result in enumerate(filtered_results, 1):
                if result.get('media_type') == 'text' and result.get('content_data'):
                    if text_notes_sent < 10:
                        title = result.get('title', 'Text Note')
                        content_data = result.get('content_data', '')
                        tags = result.get('tags', [])
                        item_id = result.get('id')
                        
                        copy_text = f"📝 **{title}**\n\n{content_data}"
                        if tags:
                            copy_text += f"\n\n🏷️ Tags: {', '.join(tags[:3])}"
                        
                        if item_id:
                            keyboard = InlineKeyboardMarkup([
                                [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{item_id}")]
                            ])
                            await message.reply_text(copy_text, parse_mode='Markdown', reply_markup=keyboard)
                        else:
                            await message.reply_text(copy_text, parse_mode='Markdown')
                        
                        text_notes_sent += 1
                        await asyncio.sleep(0.3)
                    else:
                        break
            
        else:
            await message.reply_text(f"❌ Search failed: {response.text}")
    except requests.exceptions.Timeout:
        await message.reply_text("⏰ Search timed out. Please try again.")
    except Exception as e:
        logger.error(f"Error performing search for user {user_id}: {str(e)}")
        await message.reply_text("❌ Search error. Please try again.")

# Enhanced save function with activity tracking
async def save_text_content(message, user_id: str, text: str) -> None:
    """Helper function to save text content."""
    await message.reply_text("💾 Saving your content...")
    
    try:
        # Track save activity
        await track_user_activity(user_id, "save_text", {
            "content_length": len(text),
            "timestamp": message.date.isoformat() if message.date else None
        })
        
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
            
            # Track successful save
            await track_user_activity(user_id, "save_success", {
                "item_id": result.get('id'),
                "content_type": "text",
                "tags_count": len(result.get('tags', []))
            })
            
            title = result.get('title', 'N/A')
            description = result.get('description', 'N/A')
            tags = result.get('tags', [])
            item_id = result.get('id')
            original_text = result.get('original_text', '')
            
            if len(title) > 100:
                title = title[:97] + "..."
            
            reply_text = "✅ Content Saved Successfully!\n\n"
            reply_text += f"📌 Title: {title}\n"
            
            if original_text:
                text_preview = original_text[:100] + "..." if len(original_text) > 100 else original_text
                reply_text += f"📝 Preview: {text_preview}\n"
            else:
                if len(description) > 300:
                    description = description[:297] + "..."
                reply_text += f"📝 Description: {description}\n"
                
            reply_text += f"🏷️ Tags: {', '.join(tags[:5]) if tags else 'None'}"
            
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

# New profile command
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile information."""
    user_id = await get_or_create_user_profile(update)
    
    try:
        with UserProfileService() as service:
            profile = service.get_profile(user_id)
            
            if profile:
                reply_text = f"👤 **Your Profile**\n\n"
                reply_text += f"**Name:** {profile.display_name or 'Not set'}\n"
                reply_text += f"**Username:** @{profile.username or 'Not set'}\n"
                reply_text += f"**Language:** {profile.primary_language.upper()}\n"
                reply_text += f"**Country:** {profile.country_code or 'Not set'}\n"
                reply_text += f"**Member since:** {profile.created_at.strftime('%B %Y')}\n"
                reply_text += f"**Last active:** {profile.last_active_at.strftime('%B %d, %Y') if profile.last_active_at else 'Today'}\n\n"
                
                reply_text += f"📊 **Statistics:**\n"
                reply_text += f"• **Total items saved:** {profile.total_items}\n"
                reply_text += f"• **Searches performed:** {profile.total_searches}\n"
                reply_text += f"• **Days active:** {profile.days_active}\n"
                
                if profile.is_premium:
                    reply_text += f"\n⭐ **Premium Member**"
                
                # Show connected auth providers
                if profile.auth_providers:
                    reply_text += f"\n\n🔗 **Connected Accounts:**\n"
                    for auth_provider in profile.auth_providers:
                        icon = "📱" if auth_provider.provider == "telegram" else "🔗"
                        status = " (Primary)" if auth_provider.is_primary else ""
                        reply_text += f"• {icon} {auth_provider.provider.title()}{status}\n"
                
                await update.message.reply_text(reply_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not retrieve profile information.")
                
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {str(e)}")
        await update.message.reply_text("❌ Error retrieving profile information.")

# Enhanced stats with profile integration
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show enhanced user statistics."""
    user_id = await get_or_create_user_profile(update)
    
    try:
        # Get stats from both the API and profile service
        response = requests.get(
            f"{BACKEND_URL}/user/{user_id}/stats",
            timeout=10
        )
        
        with UserProfileService() as service:
            profile_stats = service.get_user_stats(user_id)
        
        if response.status_code == 200:
            api_stats = response.json()
            
            reply_text = f"📊 **Your Memora Statistics**\n\n"
            reply_text += f"📝 **Content Overview:**\n"
            reply_text += f"• **Total Items:** {api_stats.get('total_items', 0)}\n"
            reply_text += f"• **URLs:** {api_stats.get('urls', 0)}\n"
            reply_text += f"• **Text Notes:** {api_stats.get('texts', 0)}\n"
            reply_text += f"• **Images:** {api_stats.get('images', 0)}\n"
            reply_text += f"• **Documents:** {api_stats.get('documents', 0)}\n\n"
            
            reply_text += f"🔍 **Activity Stats:**\n"
            reply_text += f"• **Searches:** {profile_stats.get('total_searches', 0)}\n"
            reply_text += f"• **Days Active:** {profile_stats.get('days_active', 0)}\n"
            
            if profile_stats.get('last_active'):
                reply_text += f"• **Last Active:** {profile_stats['last_active'].strftime('%B %d, %Y')}\n"
            
            if api_stats.get('top_tags'):
                reply_text += f"\n🏷️ **Popular Tags:**\n"
                for tag, count in api_stats['top_tags'][:5]:  # Show top 5
                    reply_text += f"  • {tag} ({count})\n"
            
            await update.message.reply_text(reply_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Could not retrieve statistics.")
            
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {str(e)}")
        await update.message.reply_text("❌ Error retrieving statistics.")

# Search command handler
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search command."""
    user_id = await get_or_create_user_profile(update)
    
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
    
    await perform_search(user_id, query, update.message)

# Delete callback handler
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
                await track_user_activity(user_id, "delete_item", {
                    "item_id": item_id,
                    "method": "inline_button"
                })
            else:
                await query.edit_message_text(f"❌ Failed to delete item: {response.text}")
        except Exception as e:
            await query.edit_message_text(f"❌ Error deleting item: {str(e)}")

# Delete all command
async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all items for the user."""
    user_id = await get_or_create_user_profile(update)
    
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
            await track_user_activity(user_id, "delete_all_items", {
                "method": "command"
            })
        else:
            await update.message.reply_text(f"❌ Failed to delete all items: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting all items: {str(e)}")

# Enhanced message handling functions (add missing text handling)
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Handle text messages with profile integration."""
    text = update.message.text
    message = update.message

    # Basic greeting handling
    greeting_patterns = [
        r'^(hi|hello|hey|yo|sup|hiya|howdy)[!,. ]*$',
        r'^(good morning|good afternoon|good evening|good night)[!,. ]*$',
        r'^(thanks|thank you|thx|ty|appreciate it)[!,. ]*$',
        r'^(bye|goodbye|see you|cya|later|take care)[!,. ]*$',
    ]

    clean_text = text.strip().lower()
    for pattern in greeting_patterns[:2]:  # Greetings
        if re.match(pattern, clean_text):
            await message.reply_text("👋 Hi there! How can I help you today?")
            return
    for pattern in greeting_patterns[2:3]:  # Thanks
        if re.match(pattern, clean_text):
            await message.reply_text("🙏 You're welcome! If you need anything else, just ask.")
            return
    for pattern in greeting_patterns[3:]:  # Farewells
        if re.match(pattern, clean_text):
            await message.reply_text("👋 Goodbye! Have a great day!")
            return

    # Use LLM for intent detection
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

# Handle document uploads
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
        await track_user_activity(user_id, "upload_document", {
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
            await track_user_activity(user_id, "save_success", {
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

# Handle photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Handle photo uploads using multimodal AI vision."""
    photo = update.message.photo[-1]
    message = update.message
    caption = message.caption or ""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if photo.file_size > MAX_FILE_SIZE:
        size_mb = photo.file_size / (1024 * 1024)
        await message.reply_text(f"❌ Image too large ({size_mb:.1f}MB). Maximum size is 50MB.")
        return
    
    await message.reply_text("📸 Analyzing image with AI vision...")
    
    try:
        # Track image upload
        await track_user_activity(user_id, "upload_image", {
            "file_size": photo.file_size,
            "has_caption": bool(caption)
        })
        
        file = await context.bot.get_file(photo.file_id)
        file_data = await file.download_as_bytearray()
        
        filename = f"photo_{photo.file_id}.jpg"
        files = {'file': (filename, bytes(file_data), 'image/jpeg')}
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
            await track_user_activity(user_id, "save_success", {
                "item_id": result.get('id'),
                "content_type": "image"
            })
            
            title = result.get('title', 'N/A')
            description = result.get('description', 'N/A')
            tags = result.get('tags', [])
            
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

def main() -> None:
    """Start the enhanced bot with profile integration."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("profile", profile))  # New profile command
    application.add_handler(CommandHandler("deleteall", delete_all))
    application.add_handler(CallbackQueryHandler(handle_delete_callback))
    
    # Handle all types of messages
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL, 
        handle_message
    ))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting enhanced Telegram bot with user profiles...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 