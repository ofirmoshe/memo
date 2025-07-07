import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

interface User {
  id: string;
  name: string;
  email?: string;
  provider: 'device' | 'google' | 'apple';
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signIn: (provider: 'device' | 'google' | 'apple', userData?: Partial<User>) => Promise<void>;
  signOut: () => Promise<void>;
  updateUser: (userData: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Fixed user ID for development
const FIXED_USER_ID = '831447258';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
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
    loadStoredUser();
  }, []);

  const loadStoredUser = async () => {
    try {
      const storedUser = await AsyncStorage.getItem('user');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        // Ensure we're using the fixed user ID
        parsedUser.id = FIXED_USER_ID;
        setUser(parsedUser);
        // Update storage with fixed ID
        await AsyncStorage.setItem('user', JSON.stringify(parsedUser));
      } else {
        // Auto-create device user if none exists
        await createDeviceUser();
      }
    } catch (error) {
      console.error('Error loading stored user:', error);
      await createDeviceUser();
    } finally {
      setIsLoading(false);
    }
  };

  const createDeviceUser = async () => {
    const deviceUser: User = {
      id: FIXED_USER_ID,
      name: 'User',
      provider: 'device',
    };
    await AsyncStorage.setItem('user', JSON.stringify(deviceUser));
    setUser(deviceUser);
  };

  const signIn = async (provider: 'device' | 'google' | 'apple', userData?: Partial<User>) => {
    try {
      let newUser: User;

      switch (provider) {
        case 'device':
          newUser = {
            id: FIXED_USER_ID,
            name: userData?.name || 'User',
            provider: 'device',
          };
          break;
        case 'google':
          // TODO: Implement Google Sign-In
          newUser = {
            id: FIXED_USER_ID,
            name: userData?.name || 'User',
            email: userData?.email,
            provider: 'google',
          };
          break;
        case 'apple':
          // TODO: Implement Apple Sign-In
          newUser = {
            id: FIXED_USER_ID,
            name: userData?.name || 'User',
            email: userData?.email,
            provider: 'apple',
          };
          break;
        default:
          throw new Error('Invalid provider');
      }

      await AsyncStorage.setItem('user', JSON.stringify(newUser));
      setUser(newUser);
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await AsyncStorage.multiRemove(['user']);
      setUser(null);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  const updateUser = async (userData: Partial<User>) => {
    if (!user) return;

    try {
      const updatedUser = { ...user, ...userData, id: FIXED_USER_ID }; // Ensure ID stays fixed
      await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (error) {
      console.error('Update user error:', error);
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

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 