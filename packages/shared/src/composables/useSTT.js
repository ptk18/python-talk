import { ref, onMounted } from 'vue';
import { settingsSync } from '../services/settingsSync.js';

const sttEngine = ref('whisper');

// Initialize from localStorage
const savedEngine = localStorage.getItem('voice_engine');
if (savedEngine) {
  sttEngine.value = savedEngine;
}

export function useSTT() {
  const setSTTEngine = (engine) => {
    sttEngine.value = engine;
    settingsSync.set('voice_engine', engine);
  };

  onMounted(() => {
    settingsSync.onSettingChange('voice_engine', (newValue) => {
      if (newValue && newValue !== sttEngine.value) {
        sttEngine.value = newValue;
      }
    });

    settingsSync.syncFromUrl();
    const urlEngine = localStorage.getItem('voice_engine');
    if (urlEngine) {
      sttEngine.value = urlEngine;
    }
  });

  return {
    sttEngine,
    setSTTEngine,
  };
}
