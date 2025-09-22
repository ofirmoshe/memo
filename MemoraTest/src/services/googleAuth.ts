import Constants from 'expo-constants';

// Conditionally import Google Sign-in only if not in Expo Go
let GoogleSignin: any = null;
let statusCodes: any = null;

const isExpoGo = Constants.appOwnership === 'expo';

if (!isExpoGo) {
  try {
    const GoogleSigninModule = require('@react-native-google-signin/google-signin');
    GoogleSignin = GoogleSigninModule.GoogleSignin;
    statusCodes = GoogleSigninModule.statusCodes;
  } catch (error) {
    console.warn('Google Sign-in module not available:', error);
  }
}

// Only configure if GoogleSignin is available
if (GoogleSignin && !isExpoGo) {
  try {
    const { GOOGLE_CONFIG } = require('../config/google');
    GoogleSignin.configure({
      iosClientId: GOOGLE_CONFIG.iosClientId,
      webClientId: GOOGLE_CONFIG.webClientId,
      offlineAccess: GOOGLE_CONFIG.offlineAccess,
      forceCodeForRefreshToken: GOOGLE_CONFIG.forceCodeForRefreshToken,
      hostedDomain: GOOGLE_CONFIG.hostedDomain,
    });
  } catch (error) {
    console.warn('Failed to configure Google Sign-in:', error);
  }
}

export interface GoogleAuthUser {
  id: string;
  email: string;
  name: string;
  givenName?: string;
  familyName?: string;
  picture?: string;
  accessToken: string;
  idToken: string;
}

export class GoogleAuthService {
  static async signIn(): Promise<GoogleAuthUser> {
    if (isExpoGo || !GoogleSignin) {
      throw new Error('Google Sign-in not available in Expo Go');
    }

    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      const tokens = await GoogleSignin.getTokens();

      if (!userInfo || !tokens.accessToken || !tokens.idToken) {
        throw new Error('Failed to get user information or tokens');
      }

      // Extract user data from the correct structure: userInfo.data.user
      const profile = (userInfo as any).data?.user;
      
      if (!profile || !profile.id || !profile.name) {
        throw new Error('Google profile data is incomplete');
      }

      const user: GoogleAuthUser = {
        id: profile.id,
        email: profile.email || '',
        name: profile.name,
        givenName: profile.givenName || '',
        familyName: profile.familyName || '',
        picture: profile.photo || '',
        accessToken: tokens.accessToken,
        idToken: tokens.idToken,
      };

      return user;
    } catch (error: any) {
      if (error.code === statusCodes?.SIGN_IN_CANCELLED) {
        throw new Error('Google Sign-in was cancelled');
      } else if (error.code === statusCodes?.IN_PROGRESS) {
        throw new Error('Google Sign-in already in progress');
      } else if (error.code === statusCodes?.PLAY_SERVICES_NOT_AVAILABLE) {
        throw new Error('Google Play Services not available');
      } else {
        console.error('Google Sign-in error:', error);
        throw new Error(`Google Sign-in failed: ${error.message}`);
      }
    }
  }

  static async signOut(): Promise<void> {
    if (isExpoGo || !GoogleSignin) {
      return; // No-op in Expo Go
    }

    try {
      await GoogleSignin.signOut();
    } catch (error) {
      console.error('Google Sign-out error:', error);
      throw error;
    }
  }

  static async revokeAccess(): Promise<void> {
    if (isExpoGo || !GoogleSignin) {
      return; // No-op in Expo Go
    }

    try {
      await GoogleSignin.revokeAccess();
    } catch (error) {
      console.error('Google revoke access error:', error);
      throw error;
    }
  }

  static async isSignedIn(): Promise<boolean> {
    if (isExpoGo || !GoogleSignin) {
      return false;
    }

    try {
      return await GoogleSignin.isSignedIn();
    } catch (error) {
      console.error('Google isSignedIn check error:', error);
      return false;
    }
  }

  static async getCurrentUser(): Promise<GoogleAuthUser | null> {
    if (isExpoGo || !GoogleSignin) {
      return null;
    }

    try {
      const userInfo = await GoogleSignin.getCurrentUser();
      if (!userInfo) return null;

      const profile = (userInfo as any).data?.user;
      if (!profile) return null;

      return {
        id: profile.id,
        email: profile.email || '',
        name: profile.name,
        givenName: profile.givenName || '',
        familyName: profile.familyName || '',
        picture: profile.photo || '',
        accessToken: '', // Would need to get fresh tokens
        idToken: '',
      };
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }
} 