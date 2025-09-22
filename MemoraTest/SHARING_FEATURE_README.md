# Memora Sharing Feature

## Overview

The Memora app now supports sharing content directly from other apps using the native OS share functionality. When you share content (like an Instagram post, TikTok video, or any URL) to Memora, the app will automatically open on the Chat screen with the shared content pre-filled and ready to save.

## How It Works

### 1. Share from Any App
- Open any app that supports sharing (Instagram, TikTok, Safari, Chrome, etc.)
- Find content you want to save to Memora
- Tap the share button (usually a square with an arrow pointing up)
- Look for "Memora" in the share sheet/app chooser
- Select Memora to share the content

### 2. Automatic Processing
- Memora will open automatically
- The app navigates to the Chat screen
- The shared URL or text is pre-filled in the input field
- You can add additional context if needed
- Tap the send button to save the content

### 3. AI-Powered Analysis
- Memora's AI analyzes the shared content
- Generates a title, description, and relevant tags
- Saves the content with semantic search capabilities
- Content is immediately available for future searches

## Supported Content Types

### URLs & Links
- **Social Media**: Instagram posts, TikTok videos, YouTube videos, Facebook posts
- **Web Content**: Articles, blog posts, news stories, product pages
- **Media**: Images, videos, documents shared via links

### Text Content
- **Notes**: Text copied from other apps
- **Messages**: Content shared from messaging apps
- **Documents**: Text content from various sources

### Files
- **Images**: Photos from camera roll or other apps
- **Documents**: PDFs, Word docs, text files
- **Media**: Audio files, video files

## Technical Implementation

### Deep Linking
The app uses custom URL schemes (`memora://`) to handle shared content:

```
memora://share?url=https://instagram.com/p/example&title=Shared%20Post
```

### Platform Support
- **iOS**: Native share extension support
- **Android**: Intent-based sharing
- **Cross-platform**: Consistent behavior on both platforms

### URL Handling
- Automatically detects content type (URL, text, file)
- Parses shared data from various formats
- Handles both direct links and Memora-specific deep links

## Configuration

### App.json Updates
The app configuration has been updated to support deep linking:

```json
{
  "expo": {
    "scheme": "memora",
    "ios": {
      "infoPlist": {
        "CFBundleURLTypes": [
          {
            "CFBundleURLName": "memora",
            "CFBundleURLSchemes": ["memora"]
          }
        ]
      }
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [
            {
              "scheme": "memora"
            }
          ],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

### Dependencies
- `expo-linking`: Handles deep linking and URL parsing
- React Navigation: Manages navigation with shared content
- Async state management: Tracks shared content across app lifecycle

## User Experience Flow

```
1. User finds content in another app
2. Taps share button
3. Selects Memora from share sheet
4. Memora opens automatically
5. Navigates to Chat screen
6. Shared content is pre-filled
7. User can add context
8. Taps send to save
9. AI processes and saves content
10. Content is available in Browse screen
```

## Testing the Feature

### Development Testing
1. Start the Expo development server
2. Open Memora on your device/emulator
3. In another app, try to share content to Memora
4. Verify the app opens and content is pre-filled

### Production Testing
1. Build and install the production APK/IPA
2. Test sharing from various apps:
   - Instagram
   - TikTok
   - Safari/Chrome
   - WhatsApp/Telegram
   - Camera app
3. Verify deep linking works correctly

## Troubleshooting

### Common Issues

#### App Doesn't Appear in Share Sheet
- Ensure the app is properly installed
- Check that deep linking is configured correctly
- Verify the app scheme is registered

#### Shared Content Not Pre-filled
- Check the console for parsing errors
- Verify the share data format
- Ensure the navigation is working correctly

#### Deep Links Not Working
- Check app.json configuration
- Verify the URL scheme is correct
- Test with the exact format: `memora://share?url=...`

### Debug Steps
1. Check console logs for parsing errors
2. Verify the shared URL format
3. Test deep linking manually
4. Check navigation state management

## Future Enhancements

### Planned Features
- **Batch sharing**: Share multiple items at once
- **Smart categorization**: Auto-organize shared content
- **Share templates**: Pre-defined sharing formats
- **Cross-device sync**: Share between devices

### Advanced Sharing
- **Rich previews**: Show content previews in share sheet
- **Quick actions**: Save with one tap
- **Context suggestions**: AI-powered context recommendations
- **Tag suggestions**: Auto-suggest relevant tags

## Security Considerations

### Data Privacy
- Shared content is processed locally when possible
- User data is isolated per user account
- No shared content is stored without user consent

### URL Validation
- All shared URLs are validated before processing
- Malicious URLs are filtered out
- Content is scanned for safety

## Performance Optimization

### Efficient Processing
- Lazy loading of shared content
- Background processing for large files
- Optimized deep link parsing
- Minimal memory footprint

### User Experience
- Fast app opening from share
- Smooth navigation transitions
- Responsive input handling
- Immediate feedback on actions

---

## Summary

The sharing feature transforms Memora from a manual content saving app into a seamless content capture tool. Users can now save interesting content from anywhere on their device with just a few taps, making Memora truly integrated into their daily digital workflow.

The implementation is robust, cross-platform compatible, and provides an intuitive user experience that feels native to both iOS and Android. 