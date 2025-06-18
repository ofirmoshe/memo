#!/usr/bin/env node

/**
 * This script updates the ngrok URL in the config.ts file
 * Usage: node scripts/update-ngrok-url.js <ngrok-url>
 * Example: node scripts/update-ngrok-url.js https://1234-567-890.ngrok-free.app
 */

const fs = require('fs');
const path = require('path');

const CONFIG_FILE_PATH = path.join(__dirname, '..', 'src', 'config.ts');

// Get the ngrok URL from command line arguments
const newNgrokUrl = process.argv[2];

if (!newNgrokUrl) {
  console.error('Error: No ngrok URL provided');
  console.log('Usage: node scripts/update-ngrok-url.js <ngrok-url>');
  console.log('Example: node scripts/update-ngrok-url.js https://1234-567-890.ngrok-free.app');
  process.exit(1);
}

// Validate the URL format
if (!newNgrokUrl.startsWith('http')) {
  console.error('Error: Invalid ngrok URL. It should start with http:// or https://');
  process.exit(1);
}

try {
  // Read the config file
  const configContent = fs.readFileSync(CONFIG_FILE_PATH, 'utf8');
  
  // Replace the TUNNEL URL with the new ngrok URL
  const updatedContent = configContent.replace(
    /(TUNNEL:[ ]*['"])([^'"]*)(["'])/,
    `$1${newNgrokUrl}$3`
  );
  
  // Write the updated content back to the file
  fs.writeFileSync(CONFIG_FILE_PATH, updatedContent);
  
  console.log(`✅ Successfully updated ngrok URL to: ${newNgrokUrl}`);
  console.log('Restart your Expo app to apply the changes');
} catch (error) {
  console.error('Error updating ngrok URL:', error.message);
  process.exit(1);
} 