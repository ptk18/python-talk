export const ENDPOINTS = {
  TURTLE: {
    API_BASE: import.meta.env.VITE_TURTLE_API_BASE || 'http://192.168.4.228:8001',
    WS_BASE: import.meta.env.VITE_TURTLE_WS_BASE || 'ws://192.168.4.228:5050'
  },
  API: {
    BASE_URL: import.meta.env.VITE_API_BASE_URL || ''
  }
}
