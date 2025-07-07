#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('🚀 Memora App Setup');
console.log('==================');
console.log('');

rl.question('Enter your Railway backend URL (e.g., https://your-app.railway.app): ', (backendUrl) => {
  if (!backendUrl) {
    console.log('❌ Backend URL is required!');
    rl.close();
    return;
  }

  // Update the API service file
  const apiServicePath = path.join(__dirname, 'src', 'services', 'api.ts');
  
  try {
    let content = fs.readFileSync(apiServicePath, 'utf8');
    content = content.replace(
      'https://your-railway-app.railway.app',
      backendUrl
    );
    
    fs.writeFileSync(apiServicePath, content);
    
    console.log('✅ Backend URL configured successfully!');
    console.log('');
    console.log('Next steps:');
    console.log('1. Run: npm install');
    console.log('2. Run: npm start');
    console.log('3. Scan the QR code with Expo Go on your phone');
    console.log('');
    console.log('Happy coding! 🎉');
    
  } catch (error) {
    console.error('❌ Error updating configuration:', error.message);
  }
  
  rl.close();
}); 