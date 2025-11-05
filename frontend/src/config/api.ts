// Use environment variable or fallback to relative URL
// In local dev: VITE_API_BASE_URL=http://localhost:3005/api
// In Docker: uses relative "/api" proxied by nginx
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// export const API_ENDPOINTS = {
//   AUTH: {
//     LOGIN: '/api/v1/auth/login',
//     SIGNUP: '/api/v1/auth/signup',
//   },
//   USERS: '/api/v1/users',
//   CONVERSATIONS: '/api/v1/conversations',
//   MESSAGES: '/api/v1/messages',
//   POSTS: '/api/v1/posts',
//   VOICE: '/voice/transcribe',
//   RUN: '/api/v1/run', // Will create this endpoint later
// } as const;

// export const HTTP_METHODS = {
//   GET: 'GET',
//   POST: 'POST',
//   PUT: 'PUT',
//   DELETE: 'DELETE',
// } as const;
