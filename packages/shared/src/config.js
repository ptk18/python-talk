// API Configuration - can be overridden by apps via environment variables
export const getApiBaseUrl = () => {
  // Check for Vite environment variable first
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    console.log("py-talk/packages/shared/src/config.js: VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL)
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Default fallback
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
console.log("packages/shared/src/config.js", API_BASE_URL)
