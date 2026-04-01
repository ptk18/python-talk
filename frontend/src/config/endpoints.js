export const ENDPOINTS = {
  TURTLE: {
    API_BASE: import.meta.env.VITE_TURTLE_API_BASE || 'http://192.168.4.228:8001',
    WS_BASE: import.meta.env.VITE_TURTLE_WS_BASE || 'ws://192.168.4.228:443'
  },
  STREAM_DEVICE: {
    API_BASE: import.meta.env.VITE_STREAM_DEVICE_BASE_URL || 'https://161.246.5.67:8001',
    WS_BASE: import.meta.env.VITE_STREAM_WS_BASE_URL || 'wss://161.246.5.67:443'
  },
  API: {
    BASE_URL: import.meta.env.VITE_API_BASE_URL || ''
  }
}
