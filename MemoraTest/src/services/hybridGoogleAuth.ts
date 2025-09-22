import { Platform } from 'react-native';
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

export class HybridGoogleAuthService {
  /**
   * Automatically detects the environment and uses the appropriate auth method
   */
  static async signIn(): Promise<GoogleAuthUser> {
    try {
      // Check if we're running in Expo Go or development build
      const isExpoGo = await this.isExpoGo();
      
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
      const isExpoGo = await this.isExpoGo();
      
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
      const isExpoGo = await this.isExpoGo();
      
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
      const isExpoGo = await this.isExpoGo();
      
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
      const isExpoGo = await this.isExpoGo();
      
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

  /**
   * Detects if we're running in Expo Go
   */
  private static async isExpoGo(): Promise<boolean> {
    try {
      // Method 1: Check if we're in Expo Go environment
      if (__DEV__ && typeof global.Expo !== 'undefined') {
        console.log('🔍 Detected Expo Go environment');
        return true;
      }

      // Method 2: Try to access native Google Sign-In (safer approach)
      const hasNativeGoogleSignIn = await this.checkNativeGoogleSignIn();
      
      const isExpoGo = !hasNativeGoogleSignIn;
      console.log(`🔍 Environment detection: ${isExpoGo ? 'Expo Go' : 'Native Build'}`);
      return isExpoGo;
    } catch (error) {
      console.log('🔍 Environment detection failed, defaulting to Expo Go');
      return true; // Default to Expo Go if detection fails
    }
  }

  /**
   * Checks if native Google Sign-In is available (safer version)
   */
  private static async checkNativeGoogleSignIn(): Promise<boolean> {
    try {
      // Try to access native Google Sign-In methods
      const googleSignIn = require('@react-native-google-signin/google-signin');
      
      // Check if the native module is properly linked
      if (googleSignIn && googleSignIn.GoogleSignin) {
        return true;
      }
      
      return false;
    } catch (error) {
      return false; // Native auth not available
    }
  }
} 