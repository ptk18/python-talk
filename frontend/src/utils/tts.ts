/**
 * Text-to-Speech utility - now uses the global voiceService
 * This ensures all TTS calls respect the user's voice engine selection
 */

import { voiceService } from '../services/voiceService';

// This will be set by the TTSContext
let isTTSEnabled = true;

export const setTTSEnabled = (enabled: boolean): void => {
  isTTSEnabled = enabled;
  // Update the voice service mute state
  voiceService.setMuted(!enabled);
  if (!enabled) {
    // Stop any ongoing speech when disabled
    window.speechSynthesis.cancel();
  }
};

/**
 * Speak using the globally selected voice engine (Standard or Google Speech)
 * This replaces the old browser-only implementation
 */
export const speak = (text: string, rate: number = 1.2): void => {
  // Only speak if TTS is enabled
  if (!isTTSEnabled) return;

  // Use the global voiceService which respects user's engine selection
  voiceService.speak(text);

  // Note: rate parameter is deprecated in favor of voice engine-specific settings
  // The voiceService handles all voice characteristics based on selected engine
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
