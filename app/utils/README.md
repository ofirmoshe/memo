# Content Detection System

The Memora content detection system is designed to intelligently identify the type of content from URLs, allowing the application to use the appropriate scraping strategy based on content type.

## Core Components

### ContentDetector

Located in `content_detector.py`, this class analyzes URLs to determine content type such as:

- Social Media (with platform-specific detection)
- News Articles
- Blog Posts
- Documentation
- E-commerce
- Videos/Images
- Unknown/General websites

### Detection Strategies

The system uses a multi-layered approach to detection:

1. **Domain-based recognition** - Checks for known domains (e.g., tiktok.com, youtube.com)
2. **URL patterns** - Analyzes URL path patterns that are specific to certain platforms
3. **URL shortener handling** - Follows redirects when shortened URLs are detected
4. **Content-Type headers** - Optionally makes HTTP HEAD requests to determine content type
5. **File extension analysis** - Checks for media file extensions

## Usage

```python
from app.utils.content_detector import content_detector, ContentType

# Detect content type from a URL
content_type, subtype = content_detector.detect_content_type(url)

if content_type == ContentType.SOCIAL_MEDIA:
    # Handle social media content
    platform = subtype  # e.g., "youtube", "tiktok", etc.
    # Use the social media scraper...
else:
    # Handle other content types
    # Use the web scraper...
```

## Extending the System

To add support for new content types or platforms:

1. Add new patterns to the appropriate lists in `ContentDetector.__init__()`
2. If needed, add new logic in the `detect_content_type()` method
3. Add new values to the `ContentType` enum if necessary

## Maintenance

When social media platforms change their URL structures, update the patterns in:
`self.social_media_patterns` within the `ContentDetector` class.

The system is designed to be adaptable with minimal changes required for new content types. 