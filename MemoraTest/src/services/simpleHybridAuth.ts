import { ExpoGoogleAuthService } from './expoGoogleAuth';
import { GoogleAuthService } from './googleAuth';

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

export class SimpleHybridAuthService {
  /**
   * Simple environment detection - defaults to Expo Go for safety
   */
  private static isExpoGo(): boolean {
    // For now, always use Expo Go auth to avoid crashes
    // When you build for real device, change this to false
    return true;
  }

  /**
   * Automatically detects the environment and uses the appropriate auth method
   */
  static async signIn(): Promise<GoogleAuthUser> {
    try {
      const isExpoGo = this.isExpoGo();
      
      if (isExpoGo) {
        console.log('🔍 Using Expo Go auth (web-based)');
        return await ExpoGoogleAuthService.signIn();
      } else {
        console.log('🔍 Using native auth (device build)');
        return await GoogleAuthService.signIn();
      }
    } catch (error: any) {
      console.error('Hybrid auth error:', error);
      throw new Error(`Sign in failed: ${error.message}`);
    }
  }

  static async signOut(): Promise<void> {
    try {
      const isExpoGo = this.isExpoGo();
      
      if (isExpoGo) {
        await ExpoGoogleAuthService.signOut();
      } else {
        await GoogleAuthService.signOut();
      }
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  static async isSignedIn(): Promise<boolean> {
    try {
      const isExpoGo = this.isExpoGo();
      
      if (isExpoGo) {
        return await ExpoGoogleAuthService.isSignedIn();
      } else {
        return await GoogleAuthService.isSignedIn();
      }
    } catch (error) {
      console.error('Error checking sign in status:', error);
      return false;
    }
  }

  static async getCurrentUser(): Promise<GoogleAuthUser | null> {
    try {
      const isExpoGo = this.isExpoGo();
      
      if (isExpoGo) {
        return await ExpoGoogleAuthService.getCurrentUser();
      } else {
        return await GoogleAuthService.getCurrentUser();
      }
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  static async refreshToken(): Promise<string | null> {
    try {
      const isExpoGo = this.isExpoGo();
      
      if (isExpoGo) {
        return await ExpoGoogleAuthService.refreshToken();
      } else {
        return await GoogleAuthService.refreshToken();
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      return null;
    }
  }
} 