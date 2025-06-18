import { Platform } from 'react-native';

// Types of services we can get preview images from
type PreviewService = 'linkpreview' | 'microlink' | 'favicon' | 'ogimage';

/**
 * Domain-specific thumbnail extraction rules
 */
const DOMAIN_SPECIFIC_RULES: Record<string, { 
  getImageUrl: (url: string) => string,
  type: string
}> = {
  'youtube.com': {
    getImageUrl: (url: string) => {
      // Extract video ID from YouTube URL
      const videoId = extractYoutubeVideoId(url);
      return videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : '';
    },
    type: 'video'
  },
  'youtu.be': {
    getImageUrl: (url: string) => {
      // Extract video ID from youtu.be URL
      const videoId = url.split('/').pop();
      return videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : '';
    },
    type: 'video'
  },
  'vimeo.com': {
    getImageUrl: (url: string) => {
      // We'd need to use Vimeo API for thumbnails
      // Fallback to using a LinkPreview service
      return getLinkPreviewImage(url);
    },
    type: 'video'
  },
  'twitter.com': {
    getImageUrl: (url: string) => {
      // Twitter preview images need authentication now
      // Fallback to using LinkPreview service
      return getLinkPreviewImage(url);
    },
    type: 'social_media'
  },
  'x.com': {
    getImageUrl: (url: string) => {
      return getLinkPreviewImage(url);
    },
    type: 'social_media'
  },
  'tiktok.com': {
    getImageUrl: (url: string) => {
      // Use link preview service for TikTok
      return getLinkPreviewImage(url);
    },
    type: 'social_media'
  },
  'medium.com': {
    getImageUrl: (url: string) => {
      return getLinkPreviewImage(url);
    },
    type: 'article'
  }
};

/**
 * Extract domain from URL
 */
const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname;
  } catch (e) {
    console.error('Error extracting domain:', e);
    return url;
  }
};

/**
 * Get preview image URL for any content URL
 */
export const getPreviewImageUrl = (url: string, contentType?: string | null): string | undefined => {
  try {
    // First try domain-specific rules
    const domain = extractDomain(url);
    
    // Check for full domain match
    if (DOMAIN_SPECIFIC_RULES[domain]) {
      const result = DOMAIN_SPECIFIC_RULES[domain].getImageUrl(url);
      if (result) return result;
    }
    
    // Check for partial domain matches (subdomains)
    for (const key in DOMAIN_SPECIFIC_RULES) {
      if (domain.endsWith(key) || domain.includes(key)) {
        const result = DOMAIN_SPECIFIC_RULES[key].getImageUrl(url);
        if (result) return result;
      }
    }
    
    // Special handling for TikTok
    if (domain.includes('tiktok.com')) {
      return getLinkPreviewImage(url);
    }
    
    // For YouTube videos
    if (contentType === 'video' && url.includes('youtube.com')) {
      const videoId = url.match(/v=([^&]+)/)?.[1];
      if (videoId) {
        return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
      }
    }
    
    // For Instagram posts
    if (url.includes('instagram.com/p/')) {
      return getLinkPreviewImage(url);
    }
    
    // For known article sites, use domain-specific image
    if (contentType === 'article') {
      const articleDomains = ['medium.com', 'nytimes.com', 'theguardian.com', 'bbc.com', 'cnn.com'];
      if (articleDomains.some(d => domain.includes(d))) {
        return getLinkPreviewImage(url);
      }
    }
    
    // For GitHub repositories
    if (domain === 'github.com') {
      const parts = url.split('/');
      if (parts.length >= 5) {
        const username = parts[3];
        const repo = parts[4];
        return `https://opengraph.githubassets.com/1/${username}/${repo}`;
      }
    }
    
    // If no specific rule matches, use OpenGraph image if available
    return getLinkPreviewImage(url);
  } catch (e) {
    console.error('Error getting preview image URL:', e);
    return undefined;
  }
};

/**
 * Extract YouTube video ID from a YouTube URL
 */
function extractYoutubeVideoId(url: string): string | null {
  const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[7].length === 11) ? match[7] : null;
}

/**
 * Get a preview image using a link preview service
 */
function getLinkPreviewImage(url: string): string {
  // Use a reliable service that doesn't require API keys for demo purposes
  // In a production app, you would use a paid API with proper keys
  
  // For demo purposes, use a service that provides CORS-friendly responses
  return `https://api.microlink.io/?url=${encodeURIComponent(url)}&embed=image.url`;
}

/**
 * Get favicon for a domain
 */
export const getFaviconUrl = (url: string): string | undefined => {
  try {
    // Extract the domain from the URL
    const urlObj = new URL(url);
    const domain = urlObj.hostname;
    
    // Return a Google favicon service URL
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
  } catch (e) {
    console.error('Error parsing URL for favicon:', e);
    return undefined;
  }
};

/**
 * Generate a placeholder image URL based on title and content type
 * 
 * @param title The title of the content
 * @param contentType The type of content
 * @returns A URL for a placeholder image
 */
export const getPlaceholderImageUrl = (title: string, contentType?: string | null): string => {
  // For now, we'll just return a placeholder image
  // In a real app, you might use a service like DiceBear or Placeholder.com
  
  // Get first letter of title, or use a default
  const initial = title && title.length > 0 ? title[0].toUpperCase() : 'M';
  
  // Get a color based on content type
  let color = '007AFF'; // Default blue
  if (contentType === 'article') color = 'FF9500';
  if (contentType === 'video') color = 'FF3B30';
  if (contentType === 'audio') color = 'AF52DE';
  if (contentType === 'social_media') color = '5856D6';
  if (contentType === 'image') color = '34C759';
  
  // Return a placeholder URL
  return `https://via.placeholder.com/400/${color}/FFFFFF?text=${initial}`;
}; 