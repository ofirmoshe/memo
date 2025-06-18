import React from 'react';
import { StatusBar, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './src/services/queryClient';
import SearchScreen from './src/screens/SearchScreen';
import UrlSubmissionScreen from './src/screens/UrlSubmissionScreen';
import HomeScreen from './src/screens/HomeScreen';
import TagsScreen from './src/screens/TagsScreen';
import ItemDetailScreen from './src/screens/ItemDetailScreen';
import Icon from 'react-native-vector-icons/Ionicons';
import Logo from './src/components/Logo';
import type { BottomTabNavigationOptions } from '@react-navigation/bottom-tabs';
import type { RouteProp } from '@react-navigation/native';
import theme from './src/config/theme';
import { BottomTabBar } from '@react-navigation/bottom-tabs';

const Tab = createBottomTabNavigator();

const CustomTabBar = (props: any) => {
  return (
    <View style={{
      position: 'absolute',
      left: 16,
      right: 16,
      bottom: 16,
      borderRadius: 32,
      backgroundColor: theme.colors.cardGlass,
      shadowColor: theme.colors.shadow,
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.18,
      shadowRadius: 24,
      elevation: 12,
      paddingBottom: 0,
      paddingTop: 0,
      overflow: 'hidden',
    }}>
      <BottomTabBar {...props} />
    </View>
  );
};

const MainTabs = () => (
  <Tab.Navigator
    initialRouteName="Home"
    tabBar={props => <CustomTabBar {...props} />}
    screenOptions={({ route }: { route: RouteProp<Record<string, object | undefined>, string> }) => ({
      headerShown: false,
      tabBarShowLabel: false,
      tabBarStyle: {
        backgroundColor: 'transparent',
        borderTopWidth: 0,
        elevation: 0,
        position: 'absolute',
        height: 64,
      },
      tabBarIcon: ({ focused, color, size }: { focused: boolean; color: string; size: number }) => {
        let iconName = '';
        if (route.name === 'Home') iconName = focused ? 'home' : 'home-outline';
        if (route.name === 'Search') iconName = focused ? 'search' : 'search-outline';
        if (route.name === 'Tags') iconName = focused ? 'pricetags' : 'pricetags-outline';
        if (route.name === 'UrlSubmission') iconName = focused ? 'add-circle' : 'add-circle-outline';
        return <Icon name={iconName} size={28} color={focused ? theme.colors.primary : theme.colors.textSecondary} style={{ marginTop: 4 }} />;
      },
    })}
  >
    <Tab.Screen name="Home" component={HomeScreen} />
    <Tab.Screen name="Search" component={SearchScreen} />
    <Tab.Screen name="UrlSubmission" component={UrlSubmissionScreen} />
    <Tab.Screen name="Tags" component={TagsScreen} />
  </Tab.Navigator>
);

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <StatusBar
          barStyle="dark-content"
          backgroundColor="#FFFFFF"
          translucent={false}
        />
        <NavigationContainer>
          <MainTabs />
        </NavigationContainer>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
};

export default App;
