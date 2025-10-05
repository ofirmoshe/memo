# Manual App Group Setup Required

## ⚠️ Why The Build Is Still Failing

EAS Build **cannot automatically create App Groups** through the Apple Developer API. App Groups require manual registration in the Apple Developer Portal.

The error you're seeing:
```
Provisioning profile doesn't support the group.com.memora.assistant App Group
```

This means the App Group `group.com.memora.assistant` doesn't exist yet in your Apple Developer account.

## ✅ Solution: Manual Setup (5 minutes)

### Step 1: Register the App Group

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list)
2. Click **Identifiers** in the sidebar
3. Click the **+** button (top left)
4. Select **App Groups** → Click **Continue**
5. Fill in:
   - **Description**: `Memora App Group`
   - **Identifier**: `group.com.memora.assistant`
6. Click **Continue** → Click **Register**

### Step 2: Enable App Groups for Main App

1. In Identifiers, find and click your main app: `com.memora.assistant`
2. Scroll down to **App Groups** capability
3. Check the checkbox next to **App Groups**
4. Click **Configure**
5. Select `group.com.memora.assistant` from the list
6. Click **Continue**
7. Click **Save**
8. Click **Confirm** when prompted

### Step 3: Enable App Groups for Share Extension

1. In Identifiers, find and click: `com.memora.assistant.share-extension`
   - **If it doesn't exist yet**: EAS will create it on the next build
   - **If it exists**: Follow these steps:
2. Scroll down to **App Groups** capability
3. Check the checkbox next to **App Groups**
4. Click **Configure**
5. Select `group.com.memora.assistant` from the list
6. Click **Continue**
7. Click **Save**
8. Click **Confirm**

### Step 4: Delete Old Provisioning Profiles (Important!)

Since we modified capabilities, old provisioning profiles are now invalid.

1. Go to [Provisioning Profiles](https://developer.apple.com/account/resources/profiles/list)
2. Find and **delete** any profiles for:
   - `com.memora.assistant`
   - `com.memora.assistant.share-extension`
3. EAS will create fresh ones on the next build

### Step 5: Run EAS Build Again

```bash
eas build --platform ios --profile development --clear-cache
```

EAS will now:
1. ✅ Find the App Group you created
2. ✅ Create new provisioning profiles with App Group capability
3. ✅ Build successfully!

## Alternative: Let EAS Create Share Extension First

If you don't want to manually configure the share extension:

**Option A: Two-build approach**

1. **First build**: Remove the share extension temporarily
   ```json
   "plugins": []
   ```

2. Run build - it will succeed and create `com.memora.assistant.share-extension` identifier

3. **Then**: Add App Groups capability to the share extension identifier in Apple Developer Portal

4. **Second build**: Add the plugin back and build again

**Option B: Just do manual setup (recommended)**

It's faster to just do the manual setup above - takes 5 minutes total.

## Verification

After manual setup, you should see in Apple Developer Portal:

**App Groups:**
- ✅ `group.com.memora.assistant`

**Identifiers:**
- ✅ `com.memora.assistant` - with App Groups enabled
- ✅ `com.memora.assistant.share-extension` - with App Groups enabled

**Provisioning Profiles:**
- All old profiles deleted (EAS will create fresh ones)

## Why This Is Necessary

From Apple's documentation:
> App Groups require manual configuration because they involve sharing data between apps/extensions. The App Store Connect API doesn't support automatic App Group assignment.

This is a one-time setup. Once the App Group exists, future builds will work automatically!

## Next Steps

1. Do the manual setup above (5 minutes)
2. Run `eas build --platform ios --profile development --clear-cache`
3. Build should succeed!
4. Test the share extension on your iPhone

## Troubleshooting

### "I don't see com.memora.assistant.share-extension in Identifiers"

That's OK! EAS hasn't created it yet. Do this:

1. Register App Group only (Step 1)
2. Enable App Groups for main app only (Step 2)
3. Run EAS build
4. After build creates the identifier, enable App Groups for it
5. Run EAS build again

### "Build still fails after manual setup"

1. Make sure you **deleted old provisioning profiles**
2. Use `--clear-cache` flag when building
3. Double-check the App Group identifier is exactly: `group.com.memora.assistant`
4. Verify both identifiers have App Groups capability enabled

## Summary

**What you need to do:**
1. Register `group.com.memora.assistant` in Apple Developer Portal
2. Enable App Groups capability for `com.memora.assistant`
3. Delete old provisioning profiles
4. Run `eas build` again

**Time needed:** ~5 minutes

**One-time only:** Yes, after this it's automatic

Let me know once you've done the manual setup and I'll help with any issues!
