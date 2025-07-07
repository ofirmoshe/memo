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

const Tab = createBottomTabNavigator();

const BrowseIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <View style={styles.iconContainer}>
    <View style={[styles.icon, { 
      width: 24, height: 24, borderWidth: 2, borderColor: color, borderRadius: 6,
      backgroundColor: focused ? color : 'transparent',
    }]} />
  </View>
);

const ChatIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <View style={styles.iconContainer}>
    <View style={[styles.icon, {
      width: 26, height: 22, borderWidth: 2, borderColor: color, borderRadius: 8,
      backgroundColor: focused ? color : 'transparent',
    }]} />
    {focused && <View style={[styles.chatIconDot, { backgroundColor: 'white' }]} />}
  </View>
);

const ProfileIcon = ({ color, focused }: { color: string, focused: boolean }) => (
  <View style={styles.iconContainer}>
    <View style={[styles.icon, {
      width: 24, height: 24, borderWidth: 2, borderColor: color, borderRadius: 12,
      backgroundColor: focused ? color : 'transparent',
    }]} />
  </View>
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
