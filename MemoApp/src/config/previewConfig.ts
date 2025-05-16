/**
 * Configuration file for preview services
 * In a production app, these would be loaded from environment variables
 */

export const previewConfig = {
  // LinkPreview.it API (https://www.linkpreview.net/)
  // Free tier has 60 requests per month
  linkPreviewApiKey: 'YOUR_LINKPREVIEW_API_KEY',
  
  // Microlink API (https://microlink.io/)
  // Free tier has 50 requests per day
  microlinkApiKey: 'YOUR_MICROLINK_API_KEY',
  
  // Use APIs that don't require keys when possible
  preferFreeApis: true,
}; 