import { voiceAPI, googleSpeechAPI } from './api';

class VoiceService {
  constructor() {
    this.engine = null;
    this.googleAvailable = false;
    this.init();
  }

  async init() {
    const savedEngine = localStorage.getItem('voice_engine') || 'whisper';
    this.engine = savedEngine;

    try {
      const status = await googleSpeechAPI.checkStatus();
      this.googleAvailable = status.available;
    } catch (err) {
      console.warn('Google Speech API not available:', err);
      this.googleAvailable = false;
    }
  }

  setEngine(engine) {
    this.engine = engine;
    localStorage.setItem('voice_engine', engine);
  }

  getEngine() {
    return this.engine || localStorage.getItem('voice_engine') || 'whisper';
  }

  async transcribe(audioFile, language = 'en') {
    const currentEngine = this.getEngine();

    if (currentEngine === 'google' && this.googleAvailable) {
      return await googleSpeechAPI.speechToText(audioFile);
    } else {
      return await voiceAPI.transcribe(audioFile, language);
    }
  }

  speak(text) {
    if (!text) return;

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }

  stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
}

export const voiceService = new VoiceService();
