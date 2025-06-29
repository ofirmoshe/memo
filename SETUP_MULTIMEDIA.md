# Memora Multi-Media Setup Guide

This guide covers setting up Memora with enhanced multi-media support including text notes, images with AI vision analysis, and document processing.

## 🚀 New Features

### Multi-Media Content Support
- **Text Notes**: Direct text input and storage
- **Images**: AI-powered vision analysis (receipts, documents, screenshots, photos)
- **Documents**: PDF, Word, and text file processing
- **URLs with Context**: Enhanced URL saving with user-provided context

### AI-Powered Analysis
- **GPT-4o-mini**: Advanced multimodal AI for direct image analysis (no OCR needed!)
- **Semantic Search**: Find content using natural language queries
- **Smart Tagging**: Automatic categorization and tagging
- **Context Integration**: User context incorporated into AI analysis

## 🛠️ Installation

### 1. System Dependencies

**No longer needed**: Tesseract OCR is not required as we use multimodal AI vision!

### 2. Python Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `openai>=1.3.8` - For GPT-4o-mini multimodal AI
- `PyPDF2>=3.0.1` - PDF text extraction
- `python-docx>=1.1.0` - Word document processing
- `Pillow>=10.1.0` - Image processing and validation
- `fastapi>=0.104.1` - Web framework
- `python-telegram-bot>=20.7` - Telegram bot integration

### 3. Environment Variables

Update your `.env` file:

```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=sqlite:///./memora.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/memora

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BACKEND_URL=http://localhost:8000

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

### 4. Database Setup

Run database migrations:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create migration for multi-media support
alembic revision --autogenerate -m "Add multimedia support"

# Apply migrations
alembic upgrade head
```

## 🎯 Usage Examples

### 1. Text Notes

**API:**
```bash
curl -X POST "http://localhost:8000/save-text" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "text_content": "Remember to buy groceries: milk, bread, eggs",
    "user_context": "Shopping list for this week"
  }'
```

**Telegram Bot:**
```
Remember to buy groceries: milk, bread, eggs
```

### 2. Images with AI Vision

**Telegram Bot:**
- Send any image (photo, screenshot, receipt, document)
- Add caption for context: "Receipt from grocery shopping"
- AI will analyze the image and extract text automatically

**Features:**
- ✅ Direct AI vision analysis (no blurry OCR!)
- ✅ Text extraction from images
- ✅ Visual content description
- ✅ Smart categorization (receipt, document, screenshot, etc.)
- ✅ Context-aware analysis

### 3. Documents

**Telegram Bot:**
- Send PDF, Word, or text files
- Add caption: "Contract for new apartment"
- System will extract and analyze content

**Supported formats:**
- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text files (`.txt`, `.csv`)

### 4. URLs with Context

**Telegram Bot:**
```
https://github.com/example/awesome-python This is a great resource for Python development
```

**API:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "url": "https://example.com/article",
    "user_context": "Research for my project on AI"
  }'
```

## 🔍 Search and Retrieval

### Semantic Search
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "query": "grocery shopping receipts",
    "media_type": "image",
    "limit": 10
  }'
```

### Filter by Media Type
- `text` - Text notes
- `image` - Photos and images
- `document` - PDF, Word, text files
- `url` - Web content

## 📊 API Endpoints

### Core Endpoints
- `POST /save-text` - Save text notes
- `POST /upload-file` - Upload and process files
- `POST /extract` - Process URLs with context
- `POST /search` - Semantic search across all content

### User Management
- `GET /user/{user_id}/items` - Get user's items with pagination
- `GET /user/{user_id}/stats` - Get user statistics by media type
- `DELETE /user/{user_id}/items/{item_id}` - Delete specific item

## 🎨 Telegram Bot Features

### Smart Message Routing
- **Plain text** → Saved as text note
- **URL + text** → URL processed with context
- **Images** → AI vision analysis
- **Documents** → File processing and analysis

### Commands
- `/start` - Welcome message and instructions
- `/search <query>` - Search your saved content
- `/stats` - View your content statistics
- `/help` - Show available commands

## 🔧 Configuration

### File Processing Limits
- **Maximum file size**: 50MB
- **Supported image formats**: JPEG, PNG, GIF, BMP, WebP
- **Supported document formats**: PDF, DOCX, DOC, TXT, CSV

### AI Model Configuration
- **Model**: GPT-4o-mini (multimodal)
- **Image analysis**: Direct vision processing
- **Text analysis**: Advanced content understanding
- **Embedding model**: text-embedding-3-small

## 🚨 Troubleshooting

### Common Issues

**1. OpenAI API Errors**
```
Error: OpenAI API key not found
```
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Verify your OpenAI account has sufficient credits

**2. File Upload Issues**
```
Error: Unsupported file type
```
- Check supported file formats above
- Ensure file size is under 50MB

**3. Image Analysis Issues**
```
Error: Could not analyze image
```
- Verify image is not corrupted
- Check OpenAI API status
- Ensure image is in supported format

**4. Database Issues**
```
Error: Database connection failed
```
- Run database migrations: `alembic upgrade head`
- Check database URL in `.env` file

### Performance Tips

1. **Image Quality**: Higher quality images provide better AI analysis
2. **Context**: Provide meaningful context for better categorization
3. **File Size**: Smaller files process faster
4. **API Limits**: Monitor OpenAI API usage for cost management

## 🔐 Security Considerations

- Files are stored locally in `uploads/` directory
- User-specific folders prevent cross-user access
- File size limits prevent abuse
- MIME type validation for security
- No executable files are processed

## 📈 Monitoring

### Check System Status
```bash
curl http://localhost:8000/health
```

### View Statistics
- Use `/stats` command in Telegram bot
- Check API endpoint `/user/{user_id}/stats`

## 🎉 What's New

### Multimodal AI Vision
- **No more OCR**: Direct AI vision analysis of images
- **Better accuracy**: GPT-4o-mini provides superior text extraction
- **Visual understanding**: AI understands both text and visual content
- **Context awareness**: Integrates user context with visual analysis

### Enhanced Features
- Improved error handling and user feedback
- Better file processing pipeline
- Enhanced search capabilities
- Comprehensive API documentation
- Updated Telegram bot with modern UX

---

## 🚀 Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set up environment**: Copy `.env.example` to `.env` and configure
3. **Run migrations**: `alembic upgrade head`
4. **Start server**: `python -m app.main`
5. **Start Telegram bot**: `python telegram_bot.py`

Your Memora instance with advanced AI vision capabilities is now ready! 🎯 