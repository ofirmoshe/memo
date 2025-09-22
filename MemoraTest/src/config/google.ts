// Google OAuth Configuration
// You need to set up a project in Google Cloud Console and get these credentials

export const GOOGLE_CONFIG = {
  // iOS Client ID from Google Cloud Console (for iOS builds)
  iosClientId: '31069252414-qhrnt2t347aoong29otng5gr236c5bio.apps.googleusercontent.com',

  // Android Client ID from Google Cloud Console (for Android builds)
  androidClientId: '31069252414-p511d7rdcdbve387db5c2gk4vmftfqf2.apps.googleusercontent.com',

  // Web Client ID - YOU NEED TO CREATE THIS in Google Cloud Console
  // Go to Credentials → Create Credentials → OAuth 2.0 Client IDs → Web application
  webClientId: '31069252414-ouoqc57621l0cicsd0otr7can4fr2qkf.apps.googleusercontent.com',

  // Offline access for refresh tokens
  offlineAccess: true,

  // Force code for refresh token
  forceCodeForRefreshToken: true,

  // Hosted domain (leave empty for any domain)
  hostedDomain: '',
};

// Your current setup:
// - Bundle ID: com.memora.assistant
// - iOS Client ID: 31069252414-qhrnt2t347aoong29otng5gr236c5bio.apps.googleusercontent.com
// - Android Client ID: 31069252414-p511d7rdcdbve387db5c2gk4vmftfqf2.apps.googleusercontent.com
// - This will work with development builds and production apps 