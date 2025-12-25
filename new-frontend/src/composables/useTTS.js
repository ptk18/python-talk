import { ref } from 'vue';

const ttsEnabled = ref(true);

const savedTTS = localStorage.getItem('tts_enabled');
if (savedTTS !== null) {
  ttsEnabled.value = savedTTS === 'true';
}

export function useTTS() {
  const setTTSEnabled = (enabled) => {
    ttsEnabled.value = enabled;
    localStorage.setItem('tts_enabled', enabled.toString());
  };

  return {
    ttsEnabled,
    setTTSEnabled,
  };
}
