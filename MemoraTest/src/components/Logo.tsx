import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface LogoProps {
  size?: number;
  color?: string;
}

export const Logo: React.FC<LogoProps> = ({ size = 24, color = '#ffffff' }) => {
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Text style={[styles.infinity, { fontSize: size * 0.8, color }]}>∞</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  infinity: {
    fontWeight: '300',
  },
}); 