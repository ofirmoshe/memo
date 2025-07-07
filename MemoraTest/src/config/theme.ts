export const lightTheme = {
  colors: {
    background: '#ffffff',
    surface: '#f0f2f5',
    card: '#ffffff',
    border: '#e0e0e0',
    
    text: '#000000',
    textSecondary: '#595959',
    textTertiary: '#8c8c8c',
    
    primary: '#000000', // Black for primary actions in light mode
    secondary: '#595959',
    error: '#d93025',
    success: '#1e8e3e',
    warning: '#f9ab00',
  },
  
  typography: {
    h1: { fontSize: 32, fontWeight: 'bold' as const, lineHeight: 40 },
    h2: { fontSize: 26, fontWeight: 'bold' as const, lineHeight: 34 },
    h3: { fontSize: 20, fontWeight: '600' as const, lineHeight: 28 },
    body: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
    caption: { fontSize: 12, fontWeight: '500' as const, lineHeight: 16 },
    small: { fontSize: 10, fontWeight: '400' as const, lineHeight: 14 },
  },
  
  spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 },
  
  borderRadius: { sm: 6, md: 10, lg: 16, xl: 20, xxl: 28, full: 9999 },
  
  shadows: {
    sm: { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 2 },
    md: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 4 },
    lg: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 8, elevation: 8 },
  },
  
  animations: { fast: 200, normal: 300, slow: 500 },
};

export const darkTheme = {
  colors: {
    background: '#000000',
    surface: '#121212',
    card: '#1e1e1e',
    border: '#2c2c2e',
    
    text: '#ffffff',
    textSecondary: '#e0e0e0',
    textTertiary: '#a0a0a0',
    
    primary: '#ffffff', // White for primary actions in dark mode
    secondary: '#a0a0a0',
    error: '#ea4335',
    success: '#34a853',
    warning: '#fbbc05',
  },
  
  typography: {
    h1: { fontSize: 32, fontWeight: 'bold' as const, lineHeight: 40 },
    h2: { fontSize: 26, fontWeight: 'bold' as const, lineHeight: 34 },
    h3: { fontSize: 20, fontWeight: '600' as const, lineHeight: 28 },
    body: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
    caption: { fontSize: 12, fontWeight: '500' as const, lineHeight: 16 },
    small: { fontSize: 10, fontWeight: '400' as const, lineHeight: 14 },
  },
  
  spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 },
  
  borderRadius: { sm: 6, md: 10, lg: 16, xl: 20, xxl: 28, full: 9999 },
  
  shadows: {
    sm: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 4, elevation: 2 },
    md: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.4, shadowRadius: 8, elevation: 4 },
    lg: { shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.5, shadowRadius: 12, elevation: 8 },
  },
  
  animations: { fast: 200, normal: 300, slow: 500 },
};

export type Theme = typeof lightTheme; 