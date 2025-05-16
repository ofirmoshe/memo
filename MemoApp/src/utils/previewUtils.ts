import { Platform } from 'react-native';
import { previewConfig } from '../config/previewConfig';

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
export function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url);
    let domain = urlObj.hostname;
    
    // Remove 'www.' prefix if present
    if (domain.startsWith('www.')) {
      domain = domain.substring(4);
    }
    
    return domain;
  } catch (e) {
    console.error('Invalid URL:', url);
    return '';
  }
}

/**
 * Get preview image URL for any content URL
 */
export function getPreviewImageUrl(url: string, contentType?: string | null): string {
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
    
    // Check for common patterns in URLs to optimize image fetching
    
    // For YouTube, extract the video ID from URL parameters
    if (url.includes('youtube.com/watch') && url.includes('v=')) {
      const videoIdMatch = url.match(/v=([^&]+)/);
      if (videoIdMatch && videoIdMatch[1]) {
        return `https://img.youtube.com/vi/${videoIdMatch[1]}/hqdefault.jpg`;
      }
    }
    
    // For Instagram posts
    if (url.includes('instagram.com/p/')) {
      // We can't directly get Instagram images anymore, so use link preview
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
    // This would require server-side fetching or a service
    // For now, use a general approach with link preview
    return getLinkPreviewImage(url);
  } catch (e) {
    console.error('Error getting preview image:', e);
    return '';
  }
}

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
  if (previewConfig.preferFreeApis) {
    // Use Microlink's free version without a key
    // 50 requests per day in the free tier without a key
    return `https://api.microlink.io/?url=${encodeURIComponent(url)}&embed=image.url`;
  } else if (previewConfig.linkPreviewApiKey) {
    // Use LinkPreview.it API with key
    return `https://api.linkpreview.net/?key=${previewConfig.linkPreviewApiKey}&q=${encodeURIComponent(url)}`;
  } else if (previewConfig.microlinkApiKey) {
    // Use Microlink API with key
    return `https://api.microlink.io/?url=${encodeURIComponent(url)}&apiKey=${previewConfig.microlinkApiKey}&embed=image.url`;
  } else {
    // Use a free API that doesn't require a key but has limitations
    // We'll use a free service from PageSpeed for a quick preview
    return `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${encodeURIComponent(url)}&screenshot=true`;
  }
}

/**
 * Get favicon for a domain
 */
export function getFaviconUrl(url: string): string {
  try {
    const domain = extractDomain(url);
    if (!domain) return '';
    
    // Google's favicon service
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
  } catch (e) {
    console.error('Error getting favicon:', e);
    return '';
  }
}

/**
 * Generate a placeholder image URL using UI Avatars service based on content title
 */
export function getPlaceholderImageUrl(title: string, contentType: string | null): string {
  // Get first letter of title or use a default
  const firstLetter = title.charAt(0).toUpperCase() || 'M';
  const colorMap: Record<string, string> = {
    'article': '0984e3',
    'video': 'e84118',
    'audio': '8854d0',
    'social_media': '3b5998',
    'image': '20bf6b',
    'pdf': 'd63031',
  };
  
  const color = contentType && colorMap[contentType] ? colorMap[contentType] : '8395a7';
  
  // Use UI Avatars to generate a custom placeholder with the first letter
  return `https://ui-avatars.com/api/?name=${firstLetter}&background=${color}&color=fff&size=128`;
} 