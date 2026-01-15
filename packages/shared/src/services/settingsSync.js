/**
 * Settings synchronization service for cross-app communication
 * Uses BroadcastChannel API for real-time sync between tabs/apps
 * Falls back to URL params for cross-origin navigation
 */

const SYNC_KEYS = ['language', 'tts_enabled', 'tts_engine', 'voice_engine', 'theme'];
const CHANNEL_NAME = 'py-talk-settings';

class SettingsSyncService {
  constructor() {
    this.channel = null;
    this.listeners = new Map();
    this.initialized = false;
  }

  /**
   * Initialize the sync service (must be called in browser context)
   */
  init() {
    if (this.initialized || typeof window === 'undefined') return;

    try {
      this.channel = new BroadcastChannel(CHANNEL_NAME);
      this.channel.onmessage = (event) => {
        this._handleMessage(event.data);
      };
      this.initialized = true;
      console.log('[SettingsSync] Initialized BroadcastChannel');
    } catch (err) {
      console.warn('[SettingsSync] BroadcastChannel not supported, falling back to localStorage events');
      // Fallback to storage events for cross-tab sync (same origin only)
      window.addEventListener('storage', (event) => {
        if (SYNC_KEYS.includes(event.key)) {
          this._handleMessage({ type: 'setting', key: event.key, value: event.newValue });
        }
      });
      this.initialized = true;
    }
  }

  /**
   * Handle incoming sync messages
   */
  _handleMessage(data) {
    if (data.type === 'setting' && SYNC_KEYS.includes(data.key)) {
      // Update localStorage with new value
      if (data.value !== null) {
        localStorage.setItem(data.key, data.value);
      } else {
        localStorage.removeItem(data.key);
      }

      // Notify listeners
      const listener = this.listeners.get(data.key);
      if (listener) {
        listener(data.value);
      }

      console.log(`[SettingsSync] Received: ${data.key} = ${data.value}`);
    }
  }

  /**
   * Set a setting and broadcast to other tabs/apps
   */
  set(key, value) {
    if (!SYNC_KEYS.includes(key)) {
      console.warn(`[SettingsSync] Key "${key}" is not in sync list`);
    }

    const stringValue = value !== null && value !== undefined ? String(value) : null;

    // Update local storage
    if (stringValue !== null) {
      localStorage.setItem(key, stringValue);
    } else {
      localStorage.removeItem(key);
    }

    // Broadcast to other tabs
    if (this.channel) {
      this.channel.postMessage({ type: 'setting', key, value: stringValue });
    }

    console.log(`[SettingsSync] Set: ${key} = ${stringValue}`);
  }

  /**
   * Get a setting value
   */
  get(key) {
    return localStorage.getItem(key);
  }

  /**
   * Register a listener for setting changes
   */
  onSettingChange(key, callback) {
    this.listeners.set(key, callback);
  }

  /**
   * Remove a listener
   */
  offSettingChange(key) {
    this.listeners.delete(key);
  }

  /**
   * Sync settings from URL parameters (for cross-origin navigation)
   */
  syncFromUrl() {
    if (typeof window === 'undefined') return;

    const params = new URLSearchParams(window.location.search);
    let synced = false;

    SYNC_KEYS.forEach(key => {
      if (params.has(key)) {
        const value = params.get(key);
        localStorage.setItem(key, value);

        // Notify listeners
        const listener = this.listeners.get(key);
        if (listener) {
          listener(value);
        }

        synced = true;
        console.log(`[SettingsSync] Synced from URL: ${key} = ${value}`);
      }
    });

    // Clean URL params after syncing
    if (synced) {
      const url = new URL(window.location.href);
      SYNC_KEYS.forEach(key => url.searchParams.delete(key));
      window.history.replaceState({}, '', url.toString());
    }
  }

  /**
   * Generate URL with all settings as query params (for cross-origin navigation)
   */
  getUrlWithSettings(baseUrl) {
    if (typeof window === 'undefined') return baseUrl;

    try {
      const url = new URL(baseUrl, window.location.origin);

      SYNC_KEYS.forEach(key => {
        const value = localStorage.getItem(key);
        if (value !== null) {
          url.searchParams.set(key, value);
        }
      });

      return url.toString();
    } catch (err) {
      console.error('[SettingsSync] Error generating URL:', err);
      return baseUrl;
    }
  }

  /**
   * Get all current settings
   */
  getAllSettings() {
    const settings = {};
    SYNC_KEYS.forEach(key => {
      settings[key] = localStorage.getItem(key);
    });
    return settings;
  }

  /**
   * Cleanup (call on app unmount)
   */
  destroy() {
    if (this.channel) {
      this.channel.close();
      this.channel = null;
    }
    this.listeners.clear();
    this.initialized = false;
  }
}

// Singleton instance
export const settingsSync = new SettingsSyncService();

// Auto-initialize in browser
if (typeof window !== 'undefined') {
  // Defer initialization to ensure DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => settingsSync.init());
  } else {
    settingsSync.init();
  }
}
