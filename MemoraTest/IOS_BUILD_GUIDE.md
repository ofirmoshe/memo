# 📱 iOS Build Guide for Memora

## Prerequisites

### 1. Apple Developer Account Setup
- ✅ Apple Developer account (already registered)
- 💻 Access to a Mac (for App Store deployment) or use EAS Build
- 📱 iPhone for testing

### 2. Required Tools
```bash
# Install EAS CLI globally
npm install -g @expo/cli
npm install -g eas-cli

# Login to your Expo account
eas login
```

## 🔑 Apple Developer Configuration

### Step 1: Create App Identifier
1. Go to [Apple Developer Portal](https://developer.apple.com/account/)
2. Navigate to **Certificates, Identifiers & Profiles** → **Identifiers**
3. Click **+** to create a new App ID
4. Configure:
   - **Bundle ID**: `com.memora.assistant` (must match app.json)
   - **App Services**: Enable:
     - Associated Domains (for share extensions)
     - Push Notifications (if needed later)
     - Sign in with Apple (optional)

### Step 2: Create Certificates and Provisioning Profiles
EAS Build will handle this automatically, but you can create them manually:

1. **Development Certificate**: For testing on your device
2. **Distribution Certificate**: For App Store submission
3. **Provisioning Profiles**: For development and distribution

## 🛠️ Build Configurations

### Development Build (Testing on Device)
```bash
# Build for iOS device testing
eas build --platform ios --profile development

# Build for iOS simulator (if you have access to Mac with Xcode)
eas build --platform ios --profile development --local
```

### Preview Build (Beta Testing)
```bash
# Build for internal testing/TestFlight
eas build --platform ios --profile preview
```

### Production Build (App Store)
```bash
# Build for App Store submission
eas build --platform ios --profile production
```

## 📲 Installation Options

### Option 1: Direct Device Installation (Development Builds)

1. **Build the app**:
   ```bash
   eas build --platform ios --profile development
   ```

2. **Register your device** (first time only):
   ```bash
   eas device:create
   ```
   Or register via the EAS CLI when prompted during build.

3. **Install via QR code**: 
   - EAS will provide a QR code after build completion
   - Scan with your iPhone camera
   - Follow the installation prompts

4. **Trust the certificate**:
   - Go to **Settings** → **General** → **VPN & Device Management**
   - Find your Apple Developer account
   - Tap **Trust** → **Trust**

### Option 2: TestFlight (Beta Testing)

1. **Build preview version**:
   ```bash
   eas build --platform ios --profile preview
   ```

2. **Submit to TestFlight**:
   ```bash
   eas submit --platform ios
   ```

3. **Invite testers**:
   - Go to [App Store Connect](https://appstoreconnect.apple.com/)
   - Navigate to your app → TestFlight
   - Add internal/external testers
   - Testers will receive an invitation email

### Option 3: App Store Release

1. **Build production version**:
   ```bash
   eas build --platform ios --profile production
   ```

2. **Submit to App Store**:
   ```bash
   eas submit --platform ios
   ```

3. **App Store Review**:
   - Go to [App Store Connect](https://appstoreconnect.apple.com/)
   - Fill in app metadata, screenshots, description
   - Submit for review (usually takes 24-48 hours)

## 🔧 Troubleshooting

### Common Issues

#### 1. Bundle Identifier Mismatch
**Error**: Bundle identifier doesn't match
**Solution**: Ensure `bundleIdentifier` in `app.json` matches your Apple Developer App ID

#### 2. Provisioning Profile Issues
**Error**: No matching provisioning profile
**Solution**: 
```bash
# Clear and rebuild
eas credentials --platform ios
# Select "Remove all credentials" and rebuild
```

#### 3. Google Sign-In Issues
**Error**: Google authentication not working
**Solution**: 
- Verify `GoogleService-Info.plist` is correct
- Check bundle identifier matches Google Cloud Console
- Ensure URL schemes are properly configured

#### 4. Share Extension Not Working
**Error**: App doesn't appear in share sheet
**Solution**:
- Ensure Associated Domains are enabled in Apple Developer
- Verify `CFBundleDocumentTypes` in app.json
- Test with development build first

### Build Logs
```bash
# View build logs
eas build:list

# View specific build details
eas build:view [BUILD_ID]
```

## 🎯 Step-by-Step First Build

### 1. Prepare for Build
```bash
cd MemoraTest

# Ensure you're logged in
eas login

# Initialize EAS (if not done)
eas build:configure
```

### 2. Convert SVG Icons to PNG
Since you have SVG icons generated, convert them to PNG:

**Option A**: Online converter
- Upload each SVG file to [SVGtoPNG.com](https://svgtopng.com/)
- Download and replace the PNG files in `/assets/`

**Option B**: Using ImageMagick (if installed)
```bash
# If you have ImageMagick installed
magick convert assets/icon.svg assets/icon.png
magick convert assets/adaptive-icon.svg assets/adaptive-icon.png
magick convert assets/splash-icon.svg assets/splash-icon.png
magick convert assets/favicon.svg assets/favicon.png
```

### 3. Build Development Version
```bash
# First build - will prompt for Apple Developer credentials
eas build --platform ios --profile development

# Register your iPhone when prompted
# Or manually: eas device:create
```

### 4. Install on iPhone
1. Wait for build to complete (15-30 minutes)
2. Scan QR code with iPhone camera
3. Follow installation prompts
4. Trust developer certificate in Settings

## 📋 Checklist Before Building

- ✅ Apple Developer account active
- ✅ Bundle identifier configured: `com.memora.assistant`
- ✅ Google authentication configured for iOS
- ✅ App icons converted from SVG to PNG
- ✅ Share extension configured in app.json
- ✅ EAS CLI installed and logged in
- ✅ iPhone registered for development (will be prompted)

## 🚀 Quick Start Commands

```bash
# Full setup and build process
cd MemoraTest
eas login
eas build --platform ios --profile development

# Check build status
eas build:list

# For App Store submission later
eas build --platform ios --profile production
eas submit --platform ios
```

## 💡 Pro Tips

1. **Start with development builds** to test functionality
2. **Use preview builds** for beta testing with others
3. **Production builds** only when ready for App Store
4. **Keep your Apple Developer subscription active** (expires annually)
5. **Test share functionality thoroughly** on development builds
6. **Monitor build times** - iOS builds typically take 15-30 minutes

## 🆘 Need Help?

- **EAS Build docs**: https://docs.expo.dev/build/introduction/
- **iOS deployment**: https://docs.expo.dev/build/setup/
- **Apple Developer Portal**: https://developer.apple.com/account/
- **TestFlight**: https://developer.apple.com/testflight/

---

Ready to build your first iOS version of Memora! 🎉 