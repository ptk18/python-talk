/**
 * Text-to-Speech utility using browser's speechSynthesis API
 */

// This will be set by the TTSContext
let isTTSEnabled = true;

export const setTTSEnabled = (enabled: boolean): void => {
  isTTSEnabled = enabled;
  if (!enabled) {
    // Stop any ongoing speech when disabled
    window.speechSynthesis.cancel();
  }
};

export const speak = (text: string, rate: number = 1.2): void => {
  // Only speak if TTS is enabled
  if (!isTTSEnabled) return;

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = rate;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  window.speechSynthesis.speak(utterance);
};

export const stopSpeaking = (): void => {
  window.speechSynthesis.cancel();
};

export const getGreeting = (): string => {
  const hour = new Date().getHours();

  if (hour >= 5 && hour < 12) {
    return "Good Morning, Sir";
  } else if (hour >= 12 && hour < 17) {
    return "Good Afternoon, Sir";
  } else if (hour >= 17 && hour < 21) {
    return "Good Evening, Sir";
  } else {
    return "Welcome, Sir";
  }
};
