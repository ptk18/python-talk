import { voiceAPI, googleSpeechAPI } from './api.js';

class VoiceService {
  constructor() {
    this.engine = null;
    this.ttsEngine = null;
    this.googleAvailable = false;
    this.voicesLoaded = false;
    this.audioContextInitialized = false;
    this.cachedVoices = [];
    this.preferredVoice = null;
    this.voiceLoadPromise = null;
    this.init();
    this.initVoices();
  }

  async init() {
    const savedEngine = localStorage.getItem('voice_engine') || 'whisper';
    this.engine = savedEngine;

    const savedTTSEngine = localStorage.getItem('tts_engine') || 'browser';
    this.ttsEngine = savedTTSEngine;

    try {
      const status = await googleSpeechAPI.checkStatus();
      this.googleAvailable = status.available;
    } catch (err) {
      console.warn('Google Speech API not available:', err);
      this.googleAvailable = false;
    }
  }

  initVoices() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    // Create a promise that resolves when voices are loaded
    this.voiceLoadPromise = new Promise((resolve) => {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          this.cachedVoices = voices;
          this.voicesLoaded = true;
          this.preferredVoice = this.selectBestVoice(voices);
          console.log(`[VoiceService] Loaded ${voices.length} voices, preferred: ${this.preferredVoice?.name || 'default'}`);
          resolve(voices);
        }
      };

      // Chrome loads voices asynchronously
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }

      // Try loading immediately (works in some browsers)
      loadVoices();

      // Fallback timeout - resolve even if no voices loaded
      setTimeout(() => {
        if (!this.voicesLoaded) {
          console.warn('[VoiceService] Voice loading timeout, using defaults');
          resolve([]);
        }
      }, 3000);
    });
  }

  selectBestVoice(voices) {
    // Priority order for voice selection
    return (
      voices.find(v => v.name.includes('Google') && v.lang === 'en-US') ||
      voices.find(v => v.name.includes('Samantha')) ||
      voices.find(v => v.name.includes('Microsoft') && v.lang === 'en-US') ||
      voices.find(v => v.lang === 'en-US') ||
      voices.find(v => v.lang.startsWith('en')) ||
      voices[0]
    );
  }

  // Call this on first user interaction to enable audio
  enableAudioContext() {
    if (this.audioContextInitialized) return;

    // Initialize a dummy audio context to unlock audio on mobile browsers
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContext.resume();
      this.audioContextInitialized = true;
      console.log('[VoiceService] Audio context initialized');
    } catch (err) {
      console.warn('[VoiceService] Could not initialize audio context:', err);
    }

    // Also trigger voice loading for browser TTS
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();

      // Chrome workaround: speak a silent utterance to unlock TTS
      const unlock = new SpeechSynthesisUtterance('');
      unlock.volume = 0;
      window.speechSynthesis.speak(unlock);
      console.log('[VoiceService] Chrome TTS unlocked with silent utterance');
    }
  }

  setEngine(engine) {
    this.engine = engine;
    localStorage.setItem('voice_engine', engine);
  }

  getEngine() {
    return this.engine || localStorage.getItem('voice_engine') || 'whisper';
  }

  setTTSEngine(engine) {
    this.ttsEngine = engine;
    localStorage.setItem('tts_engine', engine);
  }

  getTTSEngine() {
    return this.ttsEngine || localStorage.getItem('tts_engine') || 'browser';
  }

  // Detect browser for audio format handling
  getBrowserInfo() {
    if (typeof navigator === 'undefined') {
      return { isSafari: false, isChrome: false, isFirefox: false, isIOS: false };
    }
    const ua = navigator.userAgent;
    const isSafari = /^((?!chrome|android).)*safari/i.test(ua);
    const isChrome = /chrome/i.test(ua) && !/edge/i.test(ua);
    const isFirefox = /firefox/i.test(ua);
    const isIOS = /iPad|iPhone|iPod/.test(ua);

    return { isSafari, isChrome, isFirefox, isIOS };
  }

  // Get preferred audio MIME type based on browser
  getPreferredAudioType() {
    if (typeof MediaRecorder === 'undefined') {
      return 'audio/wav';
    }

    const { isSafari, isIOS } = this.getBrowserInfo();

    // Safari and iOS prefer MP4/M4A, not WebM
    if (isSafari || isIOS) {
      if (MediaRecorder.isTypeSupported('audio/mp4')) {
        return 'audio/mp4';
      }
      // Fallback for Safari
      return 'audio/wav';
    }

    // Chrome/Firefox prefer WebM
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      return 'audio/webm;codecs=opus';
    }
    if (MediaRecorder.isTypeSupported('audio/webm')) {
      return 'audio/webm';
    }

    // Final fallback
    return 'audio/wav';
  }

  async transcribe(audioFile, language = 'en') {
    const currentEngine = this.getEngine();

    if (currentEngine === 'google' && this.googleAvailable) {
      console.log('[VoiceService] Using Google Speech API');
      return await this.transcribeWithRetry(() =>
        googleSpeechAPI.speechToText(audioFile, language)
      );
    } else {
      const modelName = language === 'th'
        ? 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)'
        : 'Whisper English (distil-whisper/distil-large-v3)';

      console.log(`[VoiceService] Using ${modelName}`);

      const result = await this.transcribeWithRetry(() =>
        voiceAPI.transcribe(audioFile, language)
      );

      console.log(`[VoiceService] Transcription successful`);
      console.log(`[VoiceService] Model: ${modelName}`);
      console.log(`[VoiceService] Text: "${result.text}"`);
      console.log(`[VoiceService] Confidence: ${result.confidence || 'N/A'}`);
      return result;
    }
  }

  // Retry logic for network failures
  async transcribeWithRetry(fn, maxRetries = 3, delayMs = 1000) {
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        console.warn(`[VoiceService] Transcription attempt ${attempt}/${maxRetries} failed:`, error.message);

        if (attempt < maxRetries) {
          // Exponential backoff
          const delay = delayMs * Math.pow(2, attempt - 1);
          console.log(`[VoiceService] Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError;
  }

  async speak(text) {
    if (!text) return;

    // Check if TTS is enabled
    const ttsEnabled = localStorage.getItem('tts_enabled');
    if (ttsEnabled === 'false') {
      console.log('[VoiceService] TTS is disabled');
      return;
    }

    const currentTTSEngine = this.getTTSEngine();

    if (currentTTSEngine === 'google' && this.googleAvailable) {
      try {
        console.log('[VoiceService] Using Google Cloud TTS');
        const audioBlob = await googleSpeechAPI.textToSpeech(text);
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
        };

        audio.onerror = (err) => {
          console.error('[VoiceService] Audio playback error:', err);
          URL.revokeObjectURL(audioUrl);
        };

        // Handle autoplay policy rejection
        try {
          await audio.play();
          console.log('[VoiceService] Google TTS audio played successfully');
        } catch (playError) {
          console.error('[VoiceService] Audio play failed (likely autoplay policy):', playError);
          // Try browser TTS as fallback
          this.speakWithBrowser(text);
        }
      } catch (err) {
        console.error('[VoiceService] Google TTS failed, falling back to browser:', err);
        this.speakWithBrowser(text);
      }
    } else {
      this.speakWithBrowser(text);
    }
  }

  async speakWithBrowser(text) {
    if (!text) return;

    // Check if TTS is enabled
    const ttsEnabled = localStorage.getItem('tts_enabled');
    if (ttsEnabled === 'false') {
      console.log('[VoiceService] TTS is disabled');
      return;
    }

    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      console.warn('[VoiceService] Speech synthesis not supported in this browser');
      return;
    }

    console.log('[VoiceService] Using browser speech synthesis');

    // Cancel any previous speech
    window.speechSynthesis.cancel();

    // Wait for voices to be loaded (fixes race condition)
    if (this.voiceLoadPromise) {
      await this.voiceLoadPromise;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = 'en-US';

    // Use cached preferred voice (avoids race condition)
    if (this.preferredVoice) {
      utterance.voice = this.preferredVoice;
      console.log(`[VoiceService] Using cached voice: ${this.preferredVoice.name}`);
    } else {
      // Fallback: try to get voices synchronously
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        const voice = this.selectBestVoice(voices);
        if (voice) {
          utterance.voice = voice;
          console.log(`[VoiceService] Selected voice: ${voice.name}`);
        }
      } else {
        console.warn('[VoiceService] No voices available, using default');
      }
    }

    utterance.onstart = () => {
      console.log('[VoiceService] Browser TTS started:', text.substring(0, 50));
    };

    utterance.onend = () => {
      console.log('[VoiceService] Browser TTS ended');
    };

    utterance.onerror = (event) => {
      // Ignore canceled errors when we intentionally cancel
      if (event.error === 'canceled') {
        console.log('[VoiceService] Speech was canceled (expected)');
        return;
      }

      console.error('[VoiceService] Browser TTS error:', event.error);

      if (event.error === 'not-allowed') {
        console.warn('[VoiceService] Browser TTS blocked by autoplay policy. User interaction required first.');
      }
    };

    window.speechSynthesis.speak(utterance);
    console.log('[VoiceService] Browser TTS queued');

    // Safari workaround: force resume if needed
    const { isSafari, isIOS } = this.getBrowserInfo();
    if (isSafari || isIOS) {
      setTimeout(() => {
        if (window.speechSynthesis.paused) {
          console.log('[VoiceService] Forcing resume (Safari workaround)');
          window.speechSynthesis.resume();
        }
      }, 100);
    }
  }

  stopSpeaking() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  isGoogleAvailable() {
    return this.googleAvailable;
  }
}

export const voiceService = new VoiceService();
