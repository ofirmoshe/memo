# 🚨 Quick Fix Guide - Get Memora Running with Google Auth

## The Problem
Your app is crashing because `@react-native-google-signin/google-signin` requires native code that doesn't work with Expo Go.

## ✅ Solution: Use Expo's Built-in Auth (Already Implemented)

I've already created an alternative Google auth service using Expo's built-in packages that works with Expo Go.

## 🔧 Quick Setup Steps

### 1. Get Google Cloud Console Credentials

**Bundle ID for Google Cloud Console:**
- Use: `com.memora.assistant` (or customize it)
- This should match what's in your `app.json`

**Required Credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 Client ID for **Web application**
3. Add these redirect URIs:
   - `https://auth.expo.io/@your-expo-username/memora`
   - `https://your-app-domain.com/auth/callback`
4. Copy the **Client ID** and **Client Secret**

### 2. Update Configuration

Open `src/config/expoGoogle.ts` and replace:

```typescript
export const EXPO_GOOGLE_CONFIG = {
  webClientId: 'YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com',
  clientSecret: 'YOUR_ACTUAL_CLIENT_SECRET',
  scheme: 'memora',
  redirectPath: 'auth/callback',
};
```

### 3. Test the App

```bash
cd MemoraTest
npm start
```

The app should now:
- ✅ Start without crashing
- ✅ Show the login screen
- ✅ Allow Google Sign-In (opens in browser)
- ✅ Work with Expo Go

## 🔄 How It Works Now

1. **Expo Go Compatible**: Uses `expo-auth-session` instead of native modules
2. **Browser-based Auth**: Opens Google auth in a web browser
3. **Token Management**: Handles OAuth flow and token storage
4. **Same User Experience**: Users still sign in with Google accounts

## 🚀 For Production (Later)

When you're ready to publish to app stores:

1. **Create Development Build**: `npx eas build --profile development`
2. **Switch to Native Auth**: Use the original `@react-native-google-signin/google-signin`
3. **Update Bundle IDs**: Use your actual company/app identifiers

## 🆘 If You Still Have Issues

1. **Check Console**: Look for specific error messages
2. **Verify Credentials**: Ensure Client ID and Secret are correct
3. **Check Redirect URIs**: Make sure they match in Google Cloud Console
4. **Clear Cache**: `npx expo start --clear`

## 📱 Testing

- **Expo Go**: Works immediately with this setup
- **Physical Device**: Should work with Expo Go
- **Simulator**: May have some limitations with Google auth

---

**The app should work now!** 🎉

Try running it and let me know if you encounter any other issues. 