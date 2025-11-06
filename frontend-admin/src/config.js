/**
 * API Configuration
 * Automatically detects environment and uses appropriate API base URL
 */

// Detect if running in development mode
const isDevelopment = import.meta.env.DEV || 
                      import.meta.env.MODE === 'development' ||
                      window.location.hostname === 'localhost' ||
                      window.location.hostname === '127.0.0.1'

// Set API base URL based on environment
export const API_BASE = isDevelopment 
  ? '/api'  // Use proxy in development (localhost)
  : 'https://api.xfinai.cloud/api'  // Production URL

// Export for debugging
export const API_CONFIG = {
  base: API_BASE,
  isDevelopment,
  mode: import.meta.env.MODE,
  hostname: window.location.hostname
}

console.log('API Configuration:', API_CONFIG)

