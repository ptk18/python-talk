import { ref, onMounted } from 'vue';
import { settingsSync } from '../services/settingsSync.js';

const ttsEnabled = ref(true);
const ttsEngine = ref('browser');
const ttsRate = ref(1.0);

// Initialize from localStorage
const savedTTS = localStorage.getItem('tts_enabled');
if (savedTTS !== null) {
  ttsEnabled.value = savedTTS === 'true';
}

const savedEngine = localStorage.getItem('tts_engine');
if (savedEngine) {
  ttsEngine.value = savedEngine;
}

const savedRate = localStorage.getItem('tts_rate');
if (savedRate) {
  ttsRate.value = parseFloat(savedRate);
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

  const setTTSRate = (rate) => {
    const clampedRate = Math.max(0.5, Math.min(2.0, rate));
    ttsRate.value = clampedRate;
    settingsSync.set('tts_rate', clampedRate.toString());
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

    settingsSync.onSettingChange('tts_rate', (newValue) => {
      if (newValue) {
        ttsRate.value = parseFloat(newValue);
      }
    });

    // Sync from URL on mount (for cross-origin navigation)
    settingsSync.syncFromUrl();
    const urlTTS = localStorage.getItem('tts_enabled');
    const urlEngine = localStorage.getItem('tts_engine');
    const urlRate = localStorage.getItem('tts_rate');
    if (urlTTS !== null) {
      ttsEnabled.value = urlTTS === 'true';
    }
    if (urlEngine) {
      ttsEngine.value = urlEngine;
    }
    if (urlRate) {
      ttsRate.value = parseFloat(urlRate);
    }
  });

  return {
    ttsEnabled,
    ttsEngine,
    ttsRate,
    setTTSEnabled,
    setTTSEngine,
    setTTSRate,
  };
}
