import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { EXPO_GOOGLE_CONFIG } from '../config/expoGoogle';

// Configure WebBrowser for auth
WebBrowser.maybeCompleteAuthSession();

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

export class ExpoGoogleAuthService {
  private static readonly GOOGLE_AUTH_URL = 'https://accounts.google.com/oauth/authorize';
  private static readonly GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token';
  private static readonly GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo';

  // Use configuration from config file
  private static readonly CLIENT_ID = EXPO_GOOGLE_CONFIG.webClientId;
  private static readonly CLIENT_SECRET = EXPO_GOOGLE_CONFIG.clientSecret;
  
  // Use the Expo Go redirect URI for development
  private static readonly REDIRECT_URI = EXPO_GOOGLE_CONFIG.expoRedirectUri;

  static async signIn(): Promise<GoogleAuthUser> {
    try {
      // Create auth request with proper configuration for Expo Go
      const request = new AuthSession.AuthRequest({
        clientId: this.CLIENT_ID,
        scopes: ['openid', 'profile', 'email'],
        redirectUri: this.REDIRECT_URI,
        responseType: AuthSession.ResponseType.Code,
        extraParams: {
          access_type: 'offline',
        },
      });

      // Perform auth with proper configuration
      const result = await request.promptAsync({
        authorizationEndpoint: this.GOOGLE_AUTH_URL,
      });

      if (result.type === 'success' && result.params.code) {
        // Exchange code for tokens
        const tokens = await this.exchangeCodeForTokens(result.params.code);
        
        // Get user info
        const userInfo = await this.getUserInfo(tokens.access_token);
        
        // Create user object
        const user: GoogleAuthUser = {
          id: userInfo.id,
          email: userInfo.email,
          name: userInfo.name,
          givenName: userInfo.given_name,
          familyName: userInfo.family_name,
          picture: userInfo.picture,
          accessToken: tokens.access_token,
          idToken: tokens.id_token || '',
        };

        // Store tokens
        await this.storeTokens(tokens);
        
        return user;
      } else {
        throw new Error('Authentication was cancelled or failed');
      }
    } catch (error: any) {
      console.error('Google sign in error:', error);
      throw new Error(`Sign in failed: ${error.message}`);
    }
  }

  private static async exchangeCodeForTokens(code: string): Promise<{
    access_token: string;
    id_token?: string;
    refresh_token?: string;
  }> {
    const response = await fetch(this.GOOGLE_TOKEN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        code,
        client_id: this.CLIENT_ID,
        client_secret: this.CLIENT_SECRET,
        redirect_uri: this.REDIRECT_URI,
        grant_type: 'authorization_code',
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Token exchange failed: ${error}`);
    }

    return response.json();
  }

  private static async getUserInfo(accessToken: string): Promise<{
    id: string;
    email: string;
    name: string;
    given_name?: string;
    family_name?: string;
    picture?: string;
  }> {
    const response = await fetch(this.GOOGLE_USER_INFO_URL, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  static async signOut(): Promise<void> {
    try {
      // Clear stored tokens
      await this.clearTokens();
      
      // Revoke Google access (optional)
      const tokens = await this.getStoredTokens();
      if (tokens.accessToken) {
        try {
          await fetch(`https://oauth2.googleapis.com/revoke?token=${tokens.accessToken}`, {
            method: 'POST',
          });
        } catch (error) {
          console.warn('Failed to revoke Google token:', error);
        }
      }
    } catch (error) {
      console.error('Sign out error:', error);
      // Still clear local tokens even if revocation fails
      await this.clearTokens();
    }
  }

  static async isSignedIn(): Promise<boolean> {
    try {
      const tokens = await this.getStoredTokens();
      return !!(tokens.accessToken && tokens.idToken);
    } catch (error) {
      return false;
    }
  }

  static async getCurrentUser(): Promise<GoogleAuthUser | null> {
    try {
      const tokens = await this.getStoredTokens();
      if (!tokens.accessToken) return null;

      const userInfo = await this.getUserInfo(tokens.accessToken);
      return {
        id: userInfo.id,
        email: userInfo.email,
        name: userInfo.name,
        givenName: userInfo.given_name,
        familyName: userInfo.family_name,
        picture: userInfo.picture,
        accessToken: tokens.accessToken,
        idToken: tokens.idToken || '',
      };
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  static async refreshToken(): Promise<string | null> {
    try {
      const tokens = await this.getStoredTokens();
      if (!tokens.refreshToken) return null;

      const response = await fetch(this.GOOGLE_TOKEN_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          refresh_token: tokens.refreshToken,
          client_id: this.CLIENT_ID,
          client_secret: this.CLIENT_SECRET,
          grant_type: 'refresh_token',
        }),
      });

      if (!response.ok) return null;

      const newTokens = await response.json();
      await this.storeTokens(newTokens);
      return newTokens.access_token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      return null;
    }
  }

  private static async storeTokens(tokens: any): Promise<void> {
    try {
      await AsyncStorage.multiSet([
        ['google_access_token', tokens.access_token],
        ['google_id_token', tokens.id_token || ''],
        ['google_refresh_token', tokens.refresh_token || ''],
      ]);
    } catch (error) {
      console.error('Error storing tokens:', error);
    }
  }

  private static async clearTokens(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        'google_access_token',
        'google_id_token',
        'google_refresh_token',
      ]);
    } catch (error) {
      console.error('Error clearing tokens:', error);
    }
  }

  static async getStoredTokens(): Promise<{
    accessToken: string | null;
    idToken: string | null;
    refreshToken: string | null;
  }> {
    try {
      const [accessToken, idToken, refreshToken] = await AsyncStorage.multiGet([
        'google_access_token',
        'google_id_token',
        'google_refresh_token',
      ]);
      return {
        accessToken: accessToken[1],
        idToken: idToken[1],
        refreshToken: refreshToken[1],
      };
    } catch (error) {
      console.error('Error getting stored tokens:', error);
      return { accessToken: null, idToken: null, refreshToken: null };
    }
  }
} 