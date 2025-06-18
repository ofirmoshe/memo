import { NavigatorScreenParams } from '@react-navigation/native';
import { ContentItem } from './api';

export type RootStackParamList = {
  Home: undefined;
  Search: undefined;
  UrlSubmission: undefined;
  Tags: { tag?: string } | undefined;
  ItemDetail: { item: ContentItem };
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
} 