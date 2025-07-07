import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface ThemeColors {
  background: string;
  surface: string;
  card: string;
  border: string;
  text: string;
  textSecondary: string;
  textTertiary: string;
  primary: string;
  secondary: string;
  error: string;
  success: string;
  warning: string;
}

export interface Theme {
  colors: ThemeColors;
  typography: {
    h1: { fontSize: number; fontWeight: '700'; lineHeight: number };
    h2: { fontSize: number; fontWeight: '600'; lineHeight: number };
    h3: { fontSize: number; fontWeight: '600'; lineHeight: number };
    body: { fontSize: number; fontWeight: '400'; lineHeight: number };
    caption: { fontSize: number; fontWeight: '500'; lineHeight: number };
    small: { fontSize: number; fontWeight: '400'; lineHeight: number };
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
    xxxl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
    full: number;
  };
  shadows: {
    sm: any;
    md: any;
    lg: any;
  };
  animations: {
    fast: number;
    normal: number;
    slow: number;
  };
}

const lightColors: ThemeColors = {
  background: '#ffffff',
  surface: '#f8f9fa',
  card: '#ffffff',
  border: '#e9ecef',
  text: '#212529',
  textSecondary: '#495057',
  textTertiary: '#6c757d',
  primary: '#007bff',
  secondary: '#6c757d',
  error: '#dc3545',
  success: '#28a745',
  warning: '#ffc107',
};

const darkColors: ThemeColors = {
  background: '#121212',
  surface: '#1e1e1e',
  card: '#2d2d2d',
  border: '#404040',
  text: '#ffffff',
  textSecondary: '#e0e0e0',
  textTertiary: '#a0a0a0',
  primary: '#4dabf7',
  secondary: '#ced4da',
  error: '#f03e3e',
  success: '#51cf66',
  warning: '#ffd43b',
};

const createTheme = (colors: ThemeColors): Theme => ({
  colors,
  typography: {
    h1: {
      fontSize: 32,
      fontWeight: '700' as const,
      lineHeight: 40,
    },
    h2: {
      fontSize: 24,
      fontWeight: '600' as const,
      lineHeight: 32,
    },
    h3: {
      fontSize: 20,
      fontWeight: '600' as const,
      lineHeight: 28,
    },
    body: {
      fontSize: 16,
      fontWeight: '400' as const,
      lineHeight: 24,
    },
    caption: {
      fontSize: 12,
      fontWeight: '500' as const,
      lineHeight: 16,
    },
    small: {
      fontSize: 10,
      fontWeight: '400' as const,
      lineHeight: 14,
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32,
    xxxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    xxl: 24,
    full: 9999,
  },
  shadows: {
    sm: {
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
      elevation: 8,
    },
  },
  animations: {
    fast: 200,
    normal: 300,
    slow: 500,
  },
});

export const lightTheme = createTheme(lightColors);
export const darkTheme = createTheme(darkColors);

interface ThemeContextType {
  theme: Theme;
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    loadThemePreference();
  }, []);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('theme');
      if (savedTheme) {
        setIsDarkMode(savedTheme === 'dark');
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }
  };

  const toggleTheme = async () => {
    try {
      const newIsDarkMode = !isDarkMode;
      setIsDarkMode(newIsDarkMode);
      await AsyncStorage.setItem('theme', newIsDarkMode ? 'dark' : 'light');
    } catch (error) {
      console.error('Error saving theme preference:', error);
    }
  };

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ theme, isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Export current theme for backward compatibility
export const theme = lightTheme; 