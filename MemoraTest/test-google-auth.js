// Simple test script to verify Google auth configuration
// Run this with: node test-google-auth.js

console.log('🧪 Testing Google Auth Configuration...\n');

// Test 1: Check if configuration files exist
const fs = require('fs');
const path = require('path');

console.log('📁 Checking configuration files...');

const configFiles = [
  'src/config/google.ts',
  'src/services/googleAuth.ts',
  'src/contexts/AuthContext.tsx',
  'src/screens/LoginScreen.tsx'
];

configFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`✅ ${file} - EXISTS`);
  } else {
    console.log(`❌ ${file} - MISSING`);
  }
});

// Test 2: Check package.json dependencies
console.log('\n📦 Checking dependencies...');

try {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = [
    '@react-native-google-signin/google-signin',
    '@react-native-async-storage/async-storage',
    'react-native-svg'
  ];
  
  requiredDeps.forEach(dep => {
    if (packageJson.dependencies[dep]) {
      console.log(`✅ ${dep} - INSTALLED (${packageJson.dependencies[dep]})`);
    } else {
      console.log(`❌ ${dep} - MISSING`);
    }
  });
} catch (error) {
  console.log('❌ Could not read package.json');
}

// Test 3: Check app.json configuration
console.log('\n⚙️ Checking app.json configuration...');

try {
  const appJson = JSON.parse(fs.readFileSync('app.json', 'utf8'));
  
  if (appJson.expo.ios.bundleIdentifier === 'com.memora.assistant') {
    console.log('✅ Bundle ID configured correctly');
  } else {
    console.log('❌ Bundle ID mismatch');
  }
  
  if (appJson.expo.scheme === 'memora') {
    console.log('✅ App scheme configured');
  } else {
    console.log('❌ App scheme missing');
  }
} catch (error) {
  console.log('❌ Could not read app.json');
}

console.log('\n🎯 Next Steps:');
console.log('1. Run: npm start (to test in Expo Go)');
console.log('2. Check if app starts without crashing');
console.log('3. Verify login screen appears');
console.log('4. Test basic navigation');

console.log('\n💡 If everything works in Expo Go, then build for real device');
console.log('💡 If there are issues, fix them before building'); 