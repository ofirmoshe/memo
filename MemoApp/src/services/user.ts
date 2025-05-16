import AsyncStorage from '@react-native-async-storage/async-storage';

const USER_ID_KEY = '@memoapp:user_id';

export const getUser = async (): Promise<string | null> => {
  try {
    return await AsyncStorage.getItem(USER_ID_KEY);
  } catch (error) {
    console.error('Error getting user:', error);
    return null;
  }
};

export const setUser = async (userId: string): Promise<void> => {
  try {
    await AsyncStorage.setItem(USER_ID_KEY, userId);
  } catch (error) {
    console.error('Error setting user:', error);
  }
};

export const clearUser = async (): Promise<void> => {
  try {
    await AsyncStorage.removeItem(USER_ID_KEY);
  } catch (error) {
    console.error('Error clearing user:', error);
  }
};

// Set default user ID
setUser('guy'); 