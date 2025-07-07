import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StyleSheet, View, Text } from 'react-native';

import ChatScreen from './src/screens/ChatScreen';
import BrowseScreen from './src/screens/BrowseScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import { AuthProvider } from './src/contexts/AuthContext';
import { theme } from './src/config/theme';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NavigationContainer theme={theme.navigation}>
          <StatusBar style="light" backgroundColor="#000000" />
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                let iconText = '?';

                if (route.name === 'Chat') {
                  iconText = '💬';
                } else if (route.name === 'Browse') {
                  iconText = '🔍';
                } else if (route.name === 'Profile') {
                  iconText = '👤';
                }

                return (
                  <Text style={{ fontSize: size, color }}>
                    {iconText}
                  </Text>
                );
              },
              tabBarActiveTintColor: '#FFFFFF',
              tabBarInactiveTintColor: '#666666',
              tabBarStyle: {
                backgroundColor: '#000000',
                borderTopWidth: 1,
                borderTopColor: '#333333',
                paddingBottom: 8,
                paddingTop: 8,
                height: 60,
              },
              tabBarLabelStyle: {
                fontSize: 12,
                fontWeight: '600',
              },
              headerStyle: {
                backgroundColor: '#000000',
                borderBottomWidth: 1,
                borderBottomColor: '#333333',
              },
              headerTintColor: '#FFFFFF',
              headerTitleStyle: {
                fontWeight: 'bold',
                fontSize: 18,
              },
            })}
          >
            <Tab.Screen 
              name="Chat" 
              component={ChatScreen}
              options={{
                headerTitle: 'Memora',
                headerTitleAlign: 'center',
              }}
            />
            <Tab.Screen 
              name="Browse" 
              component={BrowseScreen}
              options={{
                headerTitle: 'Browse Memories',
                headerTitleAlign: 'center',
              }}
            />
            <Tab.Screen 
              name="Profile" 
              component={ProfileScreen}
              options={{
                headerTitle: 'Profile',
                headerTitleAlign: 'center',
              }}
            />
          </Tab.Navigator>
        </NavigationContainer>
      </AuthProvider>
    </SafeAreaProvider>
  );
} 