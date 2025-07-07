import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface LogoProps {
  size?: number;
  color?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 32, color = '#FFFFFF' }) => {
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Text style={[styles.logoText, { color, fontSize: size * 0.6 }]}>
        ∞
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText: {
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default Logo; 