// Expo Google Auth Configuration
// You need to set up a project in Google Cloud Console and get these credentials

export const EXPO_GOOGLE_CONFIG = {
  // Web Client ID from Google Cloud Console (required)
  webClientId: '31069252414-ouoqc57621l0cicsd0otr7can4fr2qkf.apps.googleusercontent.com',
  
  // Client Secret from Google Cloud Console (required for web apps)
  clientSecret: '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',
  
  // App scheme for redirect URI
  scheme: 'memora',
  
  // Redirect path
  redirectPath: 'auth/callback',
  
  // Expo Go redirect URI (this is what Google Cloud Console needs)
  expoRedirectUri: 'https://auth.expo.io/@ofirmoshe/memora',
};

// Your current setup:
// - Bundle ID: com.memora.assistant
// - iOS Client ID: 31069252414-qhrnt2t347aoong29otng5gr236c5bio.apps.googleusercontent.com
// - Web Client ID: 31069252414-ouoqc57621l0cicsd0otr7can4fr2qkf.apps.googleusercontent.com
// - This will work with both Expo Go (web auth) and device builds (native auth) 