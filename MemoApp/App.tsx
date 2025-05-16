import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './src/services/queryClient';
import SearchScreen from './src/screens/SearchScreen';
import UrlSubmissionScreen from './src/screens/UrlSubmissionScreen';

const Stack = createStackNavigator();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Search"
          screenOptions={{
            headerShown: false,
          }}>
          <Stack.Screen name="Search" component={SearchScreen} />
          <Stack.Screen name="UrlSubmission" component={UrlSubmissionScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </QueryClientProvider>
  );
};

export default App;
