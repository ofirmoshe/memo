import { NavigatorScreenParams } from '@react-navigation/native';

export type RootStackParamList = {
  Search: undefined;
  UrlSubmission: undefined;
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
} 