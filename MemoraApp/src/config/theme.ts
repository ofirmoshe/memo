import { DefaultTheme } from '@react-navigation/native';

export const theme = {
  colors: {
    primary: '#000000',
    secondary: '#FFFFFF',
    background: '#000000',
    surface: '#111111',
    card: '#111111',
    text: '#FFFFFF',
    textSecondary: '#CCCCCC',
    border: '#333333',
    accent: '#FFFFFF',
    success: '#FFFFFF',
    error: '#FFFFFF',
    warning: '#FFFFFF',
    info: '#FFFFFF',
    transparent: 'transparent',
    overlay: 'rgba(0, 0, 0, 0.8)',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  typography: {
    sizes: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    weights: {
      regular: '400' as const,
      medium: '500' as const,
      semibold: '600' as const,
      bold: '700' as const,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.4,
      relaxed: 1.6,
    },
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 999,
  },
  shadows: {
    sm: {
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.4,
      shadowRadius: 8,
      elevation: 8,
    },
  },
  animation: {
    timing: {
      fast: 200,
      normal: 300,
      slow: 500,
    },
  },
  navigation: {
    ...DefaultTheme,
    colors: {
      ...DefaultTheme.colors,
      primary: '#FFFFFF',
      background: '#000000',
      card: '#000000',
      text: '#FFFFFF',
      border: '#333333',
      notification: '#FFFFFF',
    },
  },
};

export type Theme = typeof theme; 