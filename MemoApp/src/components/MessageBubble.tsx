import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { ContentItem } from '../types/api';

type MessageBubbleProps = {
  message: string | ContentItem;
  isUser?: boolean;
  style?: object;
};

const MessageBubble = ({ message, isUser = false, style }: MessageBubbleProps) => {
  const isContentItem = typeof message !== 'string';

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer, style]}>
      {isContentItem ? (
        <View>
          <Text style={[styles.title, isUser ? styles.userText : styles.assistantText]}>
            {(message as ContentItem).title}
          </Text>
          <Text style={[styles.url, isUser ? styles.userText : styles.assistantText]}>
            {(message as ContentItem).url}
          </Text>
          <Text style={[styles.platform, isUser ? styles.userText : styles.assistantText]}>
            {(message as ContentItem).platform}
          </Text>
        </View>
      ) : (
        <Text style={[styles.text, isUser ? styles.userText : styles.assistantText]}>
          {message as string}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginVertical: 4,
    marginHorizontal: 8,
  },
  userContainer: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  assistantContainer: {
    alignSelf: 'flex-start',
    backgroundColor: '#F2F2F7',
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  url: {
    fontSize: 14,
    color: '#007AFF',
    marginBottom: 4,
  },
  platform: {
    fontSize: 12,
    color: '#8E8E93',
  },
  userText: {
    color: '#FFFFFF',
  },
  assistantText: {
    color: '#000000',
  },
});

export default MessageBubble; 