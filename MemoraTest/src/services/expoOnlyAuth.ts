import { ExpoGoogleAuthService } from './expoGoogleAuth';

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

export class ExpoOnlyAuthService {
  /**
   * Uses only Expo Google auth (safe for Expo Go)
   */
  static async signIn(): Promise<GoogleAuthUser> {
    try {
      console.log('🔍 Using Expo Go auth (web-based)');
      return await ExpoGoogleAuthService.signIn();
    } catch (error: any) {
      console.error('Google auth error:', error);
      throw new Error(`Sign in failed: ${error.message}`);
    }
  }

  static async signOut(): Promise<void> {
    try {
      await ExpoGoogleAuthService.signOut();
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  static async isSignedIn(): Promise<boolean> {
    try {
      return await ExpoGoogleAuthService.isSignedIn();
    } catch (error) {
      console.error('Error checking sign in status:', error);
      return false;
    }
  }

  static async getCurrentUser(): Promise<GoogleAuthUser | null> {
    try {
      return await ExpoGoogleAuthService.getCurrentUser();
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  static async refreshToken(): Promise<string | null> {
    try {
      return await ExpoGoogleAuthService.refreshToken();
    } catch (error) {
      console.error('Error refreshing token:', error);
      return null;
    }
  }
} 