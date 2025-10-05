#!/usr/bin/env node

/**
 * Deep Linking Test Script for Memora
 * 
 * This script helps test the deep linking functionality by generating
 * test URLs that can be used to verify the sharing feature works correctly.
 */

const testUrls = [
  // Instagram post
  'memora://share?url=https://instagram.com/p/ABC123&title=Instagram%20Post',
  
  // TikTok video
  'memora://share?url=https://tiktok.com/@user/video/123456789&title=TikTok%20Video',
  
  // YouTube video
  'memora://share?url=https://youtube.com/watch?v=dQw4w9WgXcQ&title=YouTube%20Video',
  
  // Web article
  'memora://share?url=https://example.com/article&title=Web%20Article',
  
  // Text content
  'memora://share?text=This%20is%20a%20test%20note&title=Test%20Note',
  
  // Mixed content
  'memora://share?url=https://example.com&text=Check%20this%20out&title=Mixed%20Content'
];

console.log('🧪 Memora Deep Linking Test URLs\n');
console.log('Copy and paste these URLs into your browser or notes app to test:\n');

testUrls.forEach((url, index) => {
  console.log(`${index + 1}. ${url}\n`);
});

console.log('📱 Testing Instructions:');
console.log('1. Copy one of the URLs above');
console.log('2. Paste it in your browser address bar');
console.log('3. Press Enter - Memora should open automatically');
console.log('4. Verify the app opens on the Chat screen');
console.log('5. Check that the content is pre-filled in the input field\n');

console.log('🔧 Manual Testing:');
console.log('- Open Memora app');
console.log('- Navigate to Chat screen');
console.log('- Type a URL in the input field');
console.log('- Press send to test content processing\n');

console.log('📋 Expected Behavior:');
console.log('✅ App opens automatically from deep link');
console.log('✅ Navigation to Chat screen');
console.log('✅ Content pre-filled in input field');
console.log('✅ User can add context and send');
console.log('✅ Content is processed and saved');

// Generate a simple test URL for quick testing
const quickTest = 'memora://share?url=https://example.com&title=Quick%20Test';
console.log(`\n🚀 Quick Test URL: ${quickTest}`); 