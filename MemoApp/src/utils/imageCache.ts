/**
 * Simple in-memory cache for image URLs to avoid excessive API calls
 */

interface CacheEntry {
  url: string;
  timestamp: number;
}

// Cache entries with URL as key
const imageCache: Record<string, CacheEntry> = {};

// Cache expiration time (3 days in milliseconds)
const CACHE_EXPIRATION = 3 * 24 * 60 * 60 * 1000;

/**
 * Get an image URL from cache if available
 * @param key - Unique identifier for the cached image (usually content URL)
 * @returns Cached image URL or null if not found/expired
 */
export function getCachedImage(key: string): string | null {
  const entry = imageCache[key];
  
  if (!entry) {
    return null;
  }
  
  // Check if cache has expired
  const now = Date.now();
  if (now - entry.timestamp > CACHE_EXPIRATION) {
    // Cache expired, remove it
    delete imageCache[key];
    return null;
  }
  
  return entry.url;
}

/**
 * Store an image URL in the cache
 * @param key - Unique identifier for the image (usually content URL)
 * @param imageUrl - URL of the image to cache
 */
export function cacheImage(key: string, imageUrl: string): void {
  imageCache[key] = {
    url: imageUrl,
    timestamp: Date.now()
  };
}

/**
 * Clear the entire image cache or entries for a specific key
 * @param key - Optional key to remove specific cache entry
 */
export function clearImageCache(key?: string): void {
  if (key) {
    delete imageCache[key];
  } else {
    // Clear all cache
    Object.keys(imageCache).forEach(k => {
      delete imageCache[k];
    });
  }
} 