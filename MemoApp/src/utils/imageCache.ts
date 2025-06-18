/**
 * Simple in-memory cache for image URLs
 */

// Simple in-memory cache for image URLs
const imageCache: Record<string, string> = {};

/**
 * Get a cached image URL for a content URL
 * @param contentUrl The content URL to get the cached image for
 * @returns The cached image URL or undefined if not found
 */
export const getCachedImage = (contentUrl: string): string | undefined => {
  return imageCache[contentUrl];
};

/**
 * Cache an image URL for a content URL
 * @param contentUrl The content URL to cache the image for
 * @param imageUrl The image URL to cache
 */
export const cacheImage = (contentUrl: string, imageUrl: string): void => {
  imageCache[contentUrl] = imageUrl;
};

/**
 * Clear the image cache
 */
export const clearImageCache = (): void => {
  Object.keys(imageCache).forEach(key => {
    delete imageCache[key];
  });
}; 