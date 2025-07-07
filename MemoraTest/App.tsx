import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './src/contexts/AuthContext';
import { ThemeProvider, useTheme } from './src/contexts/ThemeContext';
import { ChatScreen } from './src/screens/ChatScreen';
import { BrowseScreen } from './src/screens/BrowseScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { View, StyleSheet } from 'react-native';
import { Path, Svg } from 'react-native-svg';

const Tab = createBottomTabNavigator();

const BrowseIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <Svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <Path 
      d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" 
      stroke={color} 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      opacity={focused ? 1 : 0.5}
    />
    <Path 
      d="M15.5 8.5L8.5 15.5" 
      stroke={color} 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      opacity={focused ? 1 : 0.5}
    />
    <Path 
      d="M12 12L15.5 8.5" 
      stroke={color} 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      opacity={focused ? 1 : 0.5}
    />
  </Svg>
);

const ChatIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <Svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <Path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22C13.8561 22 15.6053 21.5538 17.1118 20.7828L21.5251 22L20.7828 17.1118C21.5538 15.6053 22 13.8561 22 12C22 6.47715 17.5228 2 12 2ZM12 4C16.4183 4 20 7.58172 20 12C20 13.6322 19.5815 15.1517 18.8483 16.429L19.5 20L16.429 18.8483C15.1517 19.5815 13.6322 20 12 20C7.58172 20 4 16.4183 4 12C4 7.58172 7.58172 4 12 4Z"
      fill={color}
      opacity={focused ? 1 : 0.5}
    />
  </Svg>
);

const ProfileIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <Svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <Path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2ZM9 7C9 5.34315 10.3431 4 12 4C13.6569 4 15 5.34315 15 7C15 8.65685 13.6569 10 12 10C10.3431 10 9 8.65685 9 7Z"
      fill={color}
      opacity={focused ? 1 : 0.5}
    />
    <Path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 14C7.58172 14 4 17.5817 4 22H6C6 18.6863 8.68629 16 12 16C15.3137 16 18 18.6863 18 22H20C20 17.5817 16.4183 14 12 14Z"
      fill={color}
      opacity={focused ? 1 : 0.5}
    />
  </Svg>
);

const AppNavigator = () => {
  const { theme } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: {
          backgroundColor: theme.colors.background,
          borderTopColor: theme.colors.border,
          height: 90,
          paddingTop: 10,
        },
        tabBarIcon: ({ focused, color, size }) => {
          if (route.name === 'Browse') {
            return <BrowseIcon color={color} focused={focused} />;
          } else if (route.name === 'Chat') {
            return <ChatIcon color={color} focused={focused} />;
          } else if (route.name === 'Profile') {
            return <ProfileIcon color={color} focused={focused} />;
          }
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textTertiary,
      })}
    >
      <Tab.Screen name="Browse" component={BrowseScreen} />
      <Tab.Screen name="Chat" component={ChatScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
};

const styles = StyleSheet.create({
  iconContainer: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatIconDot: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 3,
  }
});

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <ThemeProvider>
          <NavigationContainer>
            <AppNavigator />
          </NavigationContainer>
        </ThemeProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
