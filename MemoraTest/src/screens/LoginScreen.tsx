import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Theme } from '../config/theme';

// Conditionally import GoogleAuthService
let GoogleAuthService: any = null;
try {
  GoogleAuthService = require('../services/googleAuth').GoogleAuthService;
} catch (error) {
  console.warn('GoogleAuthService not available:', error);
}

export const LoginScreen: React.FC = () => {
  const { theme } = useTheme();
  const { signIn, isExpoGo } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    try {
      if (isExpoGo) {
        // In Expo Go, skip Google auth and use device auth
        console.log('Running in Expo Go - using device auth instead of Google');
        await signIn('device', { name: 'User' });
        Alert.alert('Success', 'Signed in as guest user (Expo Go mode)');
      } else if (GoogleAuthService) {
        // Normal Google auth flow for standalone app
        const googleUser = await GoogleAuthService.signIn();
        
        await signIn('google', {
          name: googleUser.name,
          email: googleUser.email,
          avatarUrl: googleUser.picture,
        });
        
        Alert.alert('Success', `Welcome, ${googleUser.name}!`);
      } else {
        // Fallback if Google service not available
        console.log('Google Auth service not available - using device auth');
        await signIn('device', { name: 'User' });
        Alert.alert('Success', 'Signed in as guest user');
      }
    } catch (error: any) {
      console.error('Google sign in error:', error);
      
      // If Google auth fails, try device auth as fallback
      if (!isExpoGo && error.message?.includes('Google')) {
        try {
          console.log('Google auth failed, falling back to device auth');
          await signIn('device', { name: 'User' });
          Alert.alert('Success', 'Signed in as guest user');
        } catch (fallbackError: any) {
          console.error('Fallback auth error:', fallbackError);
          Alert.alert('Sign In Failed', 'Unable to sign in. Please try again.');
        }
      } else {
        const errorMessage = error.message || 'Unknown error occurred';
        Alert.alert('Sign In Failed', errorMessage);
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleDeviceSignIn = async () => {
    setIsLoading(true);
    try {
      await signIn('device', { name: 'User' });
      Alert.alert('Success', 'Signed in as guest user');
    } catch (error: any) {
      console.error('Device sign in error:', error);
      Alert.alert('Sign In Failed', error.message || 'Failed to sign in');
    } finally {
      setIsLoading(false);
    }
  };

  const styles = getStyles(theme);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo and Title */}
        <View style={styles.header}>
          <Logo size={80} color={theme.colors.primary} />
          <Text style={styles.title}>Memora</Text>
          <Text style={styles.subtitle}>Your AI-Powered Memory Assistant</Text>
          
          {/* Show Expo Go status */}
          {isExpoGo && (
            <View style={styles.expoStatus}>
              <Text style={styles.expoStatusText}>Running in Expo Go</Text>
            </View>
          )}
        </View>

        {/* Sign In Options */}
        <View style={styles.signInContainer}>
          <Text style={styles.signInTitle}>Sign In to Continue</Text>
          
          {/* Google Sign In Button */}
          <TouchableOpacity
            style={[styles.googleButton, googleLoading && styles.buttonDisabled]}
            onPress={handleGoogleSignIn}
            disabled={googleLoading}
            activeOpacity={0.8}
          >
            {googleLoading ? (
              <ActivityIndicator color={theme.colors.text} size="small" />
            ) : (
              <>
                <Text style={styles.googleButtonText}>
                  {isExpoGo ? 'Continue as Guest (Expo Go)' : 'Continue with Google'}
                </Text>
              </>
            )}
          </TouchableOpacity>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Device Sign In Button */}
          <TouchableOpacity
            style={[styles.deviceButton, isLoading && styles.buttonDisabled]}
            onPress={handleDeviceSignIn}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color={theme.colors.background} size="small" />
            ) : (
              <Text style={styles.deviceButtonText}>Continue as Guest</Text>
            )}
          </TouchableOpacity>

          {/* Info Text */}
          <Text style={styles.infoText}>
            {isExpoGo 
              ? 'Running in Expo Go development mode. Google authentication is disabled.'
              : 'Guest mode allows you to use the app locally. Sign in with Google to sync your data across devices.'
            }
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  expoStatus: {
    backgroundColor: theme.colors.primary + '20',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginTop: 12,
  },
  expoStatusText: {
    fontSize: 12,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  signInContainer: {
    width: '100%',
  },
  signInTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: theme.colors.text,
    textAlign: 'center',
    marginBottom: 24,
  },
  googleButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  googleButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  deviceButton: {
    backgroundColor: theme.colors.primary,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  deviceButtonText: {
    color: theme.colors.background,
    fontSize: 16,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: theme.colors.border,
  },
  dividerText: {
    marginHorizontal: 16,
    color: theme.colors.textTertiary,
    fontSize: 14,
  },
  infoText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 16,
  },
}); 