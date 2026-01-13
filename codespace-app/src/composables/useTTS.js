import { ref } from 'vue';

const ttsEnabled = ref(true);
const ttsEngine = ref('browser');

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
    localStorage.setItem('tts_enabled', enabled.toString());
  };

  const setTTSEngine = (engine) => {
    ttsEngine.value = engine;
    localStorage.setItem('tts_engine', engine);
  };

  return {
    ttsEnabled,
    ttsEngine,
    setTTSEnabled,
    setTTSEngine,
  };
}
