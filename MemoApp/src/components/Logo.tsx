import React from 'react';
import { View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

interface LogoProps {
  size?: number;
  color?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 32, color = '#4F46E5' }) => {
  return (
    <View style={{ width: size, height: size }}>
      <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
        {/* Memora logo: stylized M with a memory dot */}
        <Path
          d="M8 56V16C8 12.6863 10.6863 10 14 10H22C25.3137 10 28 12.6863 28 16V56"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <Path
          d="M36 56V24C36 20.6863 38.6863 18 42 18H50C53.3137 18 56 20.6863 56 24V56"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Memory dot */}
        <Path
          d="M32 38C34.2091 38 36 36.2091 36 34C36 31.7909 34.2091 30 32 30C29.7909 30 28 31.7909 28 34C28 36.2091 29.7909 38 32 38Z"
          fill={color}
          fillOpacity="0.7"
        />
      </Svg>
    </View>
  );
};

export default Logo; 