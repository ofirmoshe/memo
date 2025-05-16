import React from 'react';
import { View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

interface LogoProps {
  size?: number;
  color?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 24, color = '#007AFF' }) => {
  return (
    <View style={{ width: size, height: size }}>
      <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <Path
          d="M3 3H7L12 18L17 3H21L21 21H17V8L12 21L7 8V21H3V3Z"
          fill={color}
        />
      </Svg>
    </View>
  );
};

export default Logo; 