# iOS & Android Share Intent Setup with expo-share-intent

## ✅ What's Installed

We've successfully set up **expo-share-intent** which provides native share functionality for both iOS and Android!

### Package Installed
- `expo-share-intent@5.0.1` - Latest version with full iOS and Android support

### What This Gives You

**iOS:**
- Memora appears in the iOS share sheet
- Users can share URLs and text from Safari, Instagram, TikTok, YouTube, etc.
- Native iOS integration - no Podfile errors!

**Android:**
- Memora appears in the Android share sheet
- Same functionality as iOS

## Configuration

### app.json

The plugin is configured with activation rules for iOS:

```json
"plugins": [
  [
    "expo-share-intent",
    {
      "iosActivationRules": {
        "NSExtensionActivationSupportsWebURLWithMaxCount": 10,
        "NSExtensionActivationSupportsText": true
      }
    }
  ]
]
```

**What this means:**
- `NSExtensionActivationSupportsWebURLWithMaxCount: 10` - Can share up to 10 URLs at once
- `NSExtensionActivationSupportsText: true` - Can share plain text

### App.tsx

The `useShareIntent` hook is integrated:

```typescript
const { hasShareIntent, shareIntent, resetShareIntent, error } = useShareIntent({
  debug: true,
  resetOnBackground: true,
});
```

**How it works:**
1. User shares content from another app
2. Selects "Memora" from share sheet
3. `hasShareIntent` becomes true
4. App extracts `webUrl`, `text`, or `files` from `shareIntent`
5. Sets it as `sharedUrl` which gets passed to ChatScreen
6. ChatScreen pre-fills the input with the shared content

## How It Works

### User Flow:

1. **User is in Safari** (or Instagram, TikTok, YouTube, etc.)
2. **Taps Share button** (square with up arrow)
3. **Scrolls and taps "Memora"** in the share sheet
4. **Memora app opens** directly on the Chat screen
5. **Shared URL is pre-filled** in the chat input
6. **User reviews and taps Send** to save to their memory

### Technical Flow:

```
Share from app → iOS/Android Share Sheet → User selects Memora →
expo-share-intent captures data → useShareIntent hook triggered →
Extract webUrl/text/files → setSharedUrl() → Navigate to Chat →
ChatScreen receives sharedUrl → Pre-fill input → User sends
```

## Building & Testing

### Build for iOS

```bash
eas build --platform ios --profile development
```

**Important:** This requires a **development build** - it won't work in Expo Go because it uses native code.

### Build for Android

```bash
eas build --platform android --profile development
```

### Testing on iPhone

1. Build completes on EAS
2. Download IPA and install via QR code or TestFlight
3. Open Safari and go to any website (e.g., https://github.com)
4. Tap the Share button
5. Scroll down and find "Memora"
6. Tap it - Memora should open with the URL pre-filled!

### Testing on Android

1. Build completes on EAS
2. Download APK and install
3. Open Chrome or any app
4. Tap Share
5. Select "Memora"
6. App should open with content pre-filled!

## Troubleshooting

### "Memora doesn't appear in share sheet"

**Causes:**
- App not installed from development/production build (Expo Go won't work)
- Need to restart device after installing
- iOS caches share sheet targets

**Solutions:**
1. Make sure you installed a development build (not Expo Go)
2. Restart your device
3. Try sharing from different apps (Safari usually works first)

### "App opens but URL is not pre-filled"

**Check:**
1. Console logs: Look for "Share intent received:" in logs
2. The `shareIntent` object should have `webUrl`, `text`, or `files`
3. Make sure `sharedUrl` is being set

**Debug:**
```typescript
console.log('hasShareIntent:', hasShareIntent);
console.log('shareIntent:', JSON.stringify(shareIntent, null, 2));
console.log('sharedUrl state:', sharedUrl);
```

### "Build fails with provisioning profile error"

This is different from the Podfile error we had before. EAS will create the share extension provisioning profile automatically, but you might need to:

1. Make sure your Apple Developer account is properly linked
2. Check that your bundle ID is unique
3. The share extension bundle ID will be: `com.memora.assistant.ShareExtension`

## What's Different from expo-share-extension

### expo-share-intent (Current Solution) ✅
- **Pros:**
  - No Podfile errors
  - Actively maintained (last updated 14 days ago)
  - Works with Expo SDK 54
  - Same behavior on iOS and Android
  - Direct app opening (no custom modal)
  - Simple hook-based API

- **Cons:**
  - No custom share extension UI
  - App opens directly (can't preview/edit before opening)

### expo-share-extension (Previous Attempt) ❌
- **Pros:**
  - Custom share extension UI (Pinterest-style modal)
  - Can preview/edit before opening main app

- **Cons:**
  - Podfile generation bug
  - Doesn't work with current Expo SDK
  - More complex setup

## User Experience

### What users see:

**iOS:**
1. Tap share in Safari
2. See Memora icon in share sheet
3. Tap it → Memora opens instantly
4. URL is already in the input box
5. Tap Send to save

**Android:**
1. Tap share in Chrome
2. See Memora in share menu
3. Tap it → Memora opens
4. URL is pre-filled
5. Tap Send

### UX Benefits:
- **Fast**: Direct app open, no intermediate screens
- **Simple**: One tap from share sheet to app
- **Familiar**: Standard iOS/Android share pattern
- **Reliable**: No custom modals that could crash

## Advanced Configuration

### Support Images & Videos

If you want users to share images and videos:

```json
"iosActivationRules": {
  "NSExtensionActivationSupportsWebURLWithMaxCount": 10,
  "NSExtensionActivationSupportsText": true,
  "NSExtensionActivationSupportsImageWithMaxCount": 5,
  "NSExtensionActivationSupportsMovieWithMaxCount": 1
}
```

Then handle files in App.tsx:
```typescript
if (shareIntent.files && shareIntent.files.length > 0) {
  const file = shareIntent.files[0];
  // file.path - path to the file
  // file.mimeType - file MIME type
  // Upload to your backend or handle locally
}
```

### Disable During Development

If you want to test without share intent:

```typescript
const { hasShareIntent, shareIntent } = useShareIntent({
  disabled: true, // Disable the native module
});
```

## Next Steps

1. **Build the app**: `eas build --platform ios --profile development`
2. **Install on your iPhone**
3. **Test sharing from Safari, Instagram, TikTok**
4. **Celebrate** - you now have native iOS share integration! 🎉

## Resources

- [expo-share-intent GitHub](https://github.com/achorein/expo-share-intent)
- [expo-share-intent Demo App](https://github.com/achorein/expo-share-intent-demo)
- [iOS Share Extension Docs](https://developer.apple.com/design/human-interface-guidelines/share-extensions)
