# 🚀 Development Build Guide - Test Memora with Real Google Auth

## 🎯 **What We're Doing**

Instead of using Expo Go (which has limitations), we're creating a **development build** that:
- ✅ **Works with native Google Sign-In**
- ✅ **Installs directly on your device**
- ✅ **Has full functionality**
- ✅ **Is production-ready**

## 🔧 **Setup Steps**

### **Step 1: Install EAS CLI**
```bash
cd MemoraTest
npm install -g @expo/eas-cli
```

### **Step 2: Create Expo Account & Login**
```bash
eas login
```
- If you don't have an account, it will create one
- Use your email to sign up

### **Step 3: Configure EAS Build**
```bash
eas build:configure
```
- This creates the `eas.json` file (already done)

### **Step 4: Build for Android (Easier to test)**
```bash
eas build --platform android --profile development
```

**What happens:**
1. **EAS uploads your code** to Google Cloud
2. **Builds your app** in the cloud
3. **Creates an .apk file** (Android app)
4. **Gives you a download link** when done

## 📱 **Testing Process**

### **1. Download the App**
- **Wait for build to complete** (usually 10-20 minutes)
- **Click the download link** from EAS
- **Download the .apk file** to your phone

### **2. Install on Your Phone**
- **Enable "Install from unknown sources"** in Android settings
- **Tap the .apk file** to install
- **Grant necessary permissions**

### **3. Test Google Sign-In**
- **Open the app**
- **Tap "Continue with Google"**
- **Sign in with your Google account**
- **Test all features**

## 🔑 **Google Auth Setup**

### **Current Configuration:**
- ✅ **Bundle ID**: `com.memora.assistant`
- ✅ **iOS Client ID**: `31069252414-qhrnt2t347aoong29otng5gr236c5bio.apps.googleusercontent.com`
- ✅ **No Client Secret needed** (iOS clients don't have secrets)

### **What You Need to Do:**
1. **Keep your current iOS Client ID** (it's perfect!)
2. **No need for Client Secret** (iOS clients don't have them)
3. **No need for redirect URIs** (iOS handles this automatically)

## 🚨 **Important Notes**

### **For Android Testing:**
- **Create an Android Client ID** in Google Cloud Console
- **Bundle ID**: `com.memora.assistant`
- **Package name**: `com.memora.assistant`

### **For iOS Testing:**
- **Your current iOS Client ID is perfect**
- **No additional setup needed**

## 🎉 **Benefits of This Approach**

1. **Real App Experience** - Same as what users will download
2. **Full Google Auth** - Native implementation
3. **Production Ready** - Can publish directly from this build
4. **Better Performance** - No Expo Go overhead
5. **Real Device Testing** - Test on actual hardware

## 🔄 **Build Commands**

### **Development Build (for testing):**
```bash
eas build --platform android --profile development
eas build --platform ios --profile development
```

### **Preview Build (for beta testing):**
```bash
eas build --platform android --profile preview
eas build --platform ios --profile preview
```

### **Production Build (for app stores):**
```bash
eas build --platform android --profile production
eas build --platform ios --profile production
```

## 🆘 **Troubleshooting**

### **Build Fails:**
- Check that all dependencies are installed
- Ensure your code compiles locally
- Check EAS build logs for specific errors

### **Google Auth Doesn't Work:**
- Verify your Client ID is correct
- Ensure bundle ID matches in Google Cloud Console
- Check that Google Sign-In API is enabled

### **App Won't Install:**
- Enable "Install from unknown sources"
- Check Android version compatibility
- Try downloading the .apk again

---

## 🎯 **Next Steps**

1. **Run the build command** above
2. **Wait for build to complete**
3. **Download and install the app**
4. **Test Google Sign-In**
5. **Let me know how it works!**

**This approach is much better than Expo Go and will give you a real app to test with!** 🚀 