import { ref, onMounted } from 'vue';
import { settingsSync } from '../services/settingsSync.js';

const ttsEnabled = ref(true);
const ttsEngine = ref('browser');

// Initialize from localStorage
const savedTTS = localStorage.getItem('tts_enabled');
if (savedTTS !== null) {
  ttsEnabled.value = savedTTS === 'true';
}

const savedEngine = localStorage.getItem('tts_engine');
if (savedEngine) {
  ttsEngine.value = savedEngine;
}

export function useTTS() {
  const setTTSEnabled = (enabled) => {
    ttsEnabled.value = enabled;
    settingsSync.set('tts_enabled', enabled.toString());
  };

  const setTTSEngine = (engine) => {
    ttsEngine.value = engine;
    settingsSync.set('tts_engine', engine);
  };

  // Listen for changes from other tabs/apps
  onMounted(() => {
    settingsSync.onSettingChange('tts_enabled', (newValue) => {
      if (newValue !== null) {
        ttsEnabled.value = newValue === 'true';
      }
    });

    settingsSync.onSettingChange('tts_engine', (newValue) => {
      if (newValue && newValue !== ttsEngine.value) {
        ttsEngine.value = newValue;
      }
    });

    // Sync from URL on mount (for cross-origin navigation)
    settingsSync.syncFromUrl();
    const urlTTS = localStorage.getItem('tts_enabled');
    const urlEngine = localStorage.getItem('tts_engine');
    if (urlTTS !== null) {
      ttsEnabled.value = urlTTS === 'true';
    }
    if (urlEngine) {
      ttsEngine.value = urlEngine;
    }
  });

  return {
    ttsEnabled,
    ttsEngine,
    setTTSEnabled,
    setTTSEngine,
  };
}
