import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

interface User {
  id: string;
  name?: string;
  email?: string;
  avatar?: string;
  authProvider: 'device' | 'google' | 'apple';
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signIn: (provider: 'device' | 'google' | 'apple', userData?: Partial<User>) => Promise<void>;
  signOut: () => Promise<void>;
  updateUser: (userData: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      } else {
        // Create a device-based user ID if none exists
        await createDeviceUser();
      }
    } catch (error) {
      console.error('Error loading user:', error);
      // Fallback to device user
      await createDeviceUser();
    } finally {
      setIsLoading(false);
    }
  };

  const createDeviceUser = async () => {
    try {
      // Check if we already have a device ID stored securely
      let deviceId = await SecureStore.getItemAsync('deviceUserId');
      
      if (!deviceId) {
        // Generate a unique device-based user ID
        deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await SecureStore.setItemAsync('deviceUserId', deviceId);
      }

      const deviceUser: User = {
        id: deviceId,
        name: 'Anonymous User',
        authProvider: 'device',
      };

      setUser(deviceUser);
      await AsyncStorage.setItem('user', JSON.stringify(deviceUser));
    } catch (error) {
      console.error('Error creating device user:', error);
    }
  };

  const signIn = async (provider: 'device' | 'google' | 'apple', userData?: Partial<User>) => {
    try {
      let newUser: User;

      switch (provider) {
        case 'device':
          await createDeviceUser();
          return;

        case 'google':
          // TODO: Implement Google Sign-In
          // For now, create a placeholder
          newUser = {
            id: `google_${userData?.id || Date.now()}`,
            name: userData?.name || 'Google User',
            email: userData?.email,
            avatar: userData?.avatar,
            authProvider: 'google',
          };
          break;

        case 'apple':
          // TODO: Implement Apple Sign-In
          // For now, create a placeholder
          newUser = {
            id: `apple_${userData?.id || Date.now()}`,
            name: userData?.name || 'Apple User',
            email: userData?.email,
            avatar: userData?.avatar,
            authProvider: 'apple',
          };
          break;

        default:
          throw new Error('Unsupported authentication provider');
      }

      setUser(newUser);
      await AsyncStorage.setItem('user', JSON.stringify(newUser));
    } catch (error) {
      console.error('Error signing in:', error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      setUser(null);
      await AsyncStorage.removeItem('user');
      // Don't remove the device ID, we might want to use it again
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };

  const updateUser = async (userData: Partial<User>) => {
    try {
      if (!user) return;

      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
    } catch (error) {
      console.error('Error updating user:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    signIn,
    signOut,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 