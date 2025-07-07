import React from 'react';
import Svg, { Path } from 'react-native-svg';
import { IconProps } from './types';

const LinkIcon: React.FC<IconProps> = ({ color = 'black', width = 24, height = 24 }) => (
  <Svg width={width} height={height} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <Path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72" />
    <Path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72" />
  </Svg>
);

export default LinkIcon; 