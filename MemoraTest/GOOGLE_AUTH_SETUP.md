# 🔐 Google Sign-In Setup Guide for Memora

## 📋 Prerequisites

- Google Cloud Console account
- Expo project set up
- React Native development environment

## 🚀 Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sign-In API

### 2. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type
3. Fill in app information:
   - App name: Memora
   - User support email: your-email@domain.com
   - Developer contact information: your-email@domain.com

### 3. Create OAuth 2.0 Client ID

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `https://auth.expo.io/@your-expo-username/memora`
   - `https://your-domain.com/auth/callback` (for production)

### 4. Download Configuration

1. Download the `google-services.json` file
2. Place it in your project root
3. Update your app configuration

## 🔧 Configuration Files

### app.json
```json
{
  "expo": {
    "name": "Memora",
    "scheme": "memora",
    "ios": {
      "bundleIdentifier": "com.memora.assistant",
      "googleServicesFile": "./GoogleService-Info.plist"
    },
    "android": {
      "package": "com.memora.assistant",
      "googleServicesFile": "./google-services.json"
    }
  }
}
```

### src/config/google.ts
```typescript
export const GOOGLE_CONFIG = {
  webClientId: 'YOUR_WEB_CLIENT_ID.apps.googleusercontent.com',
  iosClientId: 'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com',
  androidClientId: 'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com',
  offlineAccess: true,
  forceCodeForRefreshToken: true,
  hostedDomain: '',
};
```

## 📱 Testing

### Expo Go
1. Run `npm start`
2. Scan QR code with Expo Go
3. Test Google Sign-In button

### Development Build
1. Run `eas build --platform ios --profile development`
2. Install the build on your device
3. Test Google Sign-In functionality

## 🚨 Common Issues

### 404 Error
- Check redirect URI matches exactly
- Ensure Google Sign-In API is enabled
- Verify OAuth client ID is correct

### Native Module Error
- Use development build instead of Expo Go
- Ensure native dependencies are linked
- Check bundle identifier matches

## 🔗 Useful Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [Expo Auth Session](https://docs.expo.dev/versions/latest/sdk/auth-session/)
- [Google Sign-In for React Native](https://github.com/react-native-google-signin/google-signin)

## 📞 Support

If you encounter issues:
1. Check the console logs
2. Verify all configuration steps
3. Ensure APIs are enabled
4. Test with development build 