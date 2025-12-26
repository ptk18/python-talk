import { voiceAPI, googleSpeechAPI } from './api';

class VoiceService {
  constructor() {
    this.engine = null;
    this.ttsEngine = null;
    this.googleAvailable = false;
    this.voicesLoaded = false;
    this.audioContextInitialized = false;
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
    if ('speechSynthesis' in window) {
      // Load voices (required on some browsers)
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          this.voicesLoaded = true;
          console.log(`[VoiceService] Loaded ${voices.length} voices`);
        }
      };

      // Chrome loads voices asynchronously
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }

      // Try loading immediately
      loadVoices();
    }
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

  async transcribe(audioFile, language = 'en') {
    const currentEngine = this.getEngine();

    if (currentEngine === 'google' && this.googleAvailable) {
      console.log('[VoiceService] Using Google Speech API');
      return await googleSpeechAPI.speechToText(audioFile);
    } else {
      const modelName = language === 'th'
        ? 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)'
        : 'Whisper English (distil-whisper/distil-large-v3)';

      console.log(`[VoiceService] Using ${modelName}`);
      const result = await voiceAPI.transcribe(audioFile, language);
      console.log(`[VoiceService] ✅ Transcription successful`);
      console.log(`[VoiceService] Model: ${modelName}`);
      console.log(`[VoiceService] Text: "${result.text}"`);
      console.log(`[VoiceService] Confidence: ${result.confidence || 'N/A'}`);
      return result;
    }
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
          console.error('[VoiceService] ✗ Audio playback error:', err);
          URL.revokeObjectURL(audioUrl);
        };

        // Handle autoplay policy rejection
        try {
          await audio.play();
          console.log('[VoiceService] ✓ Google TTS audio played successfully');
        } catch (playError) {
          console.error('[VoiceService] ✗ Audio play failed (likely autoplay policy):', playError);
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

  speakWithBrowser(text) {
    if (!text) return;

    // Check if TTS is enabled
    const ttsEnabled = localStorage.getItem('tts_enabled');
    if (ttsEnabled === 'false') {
      console.log('[VoiceService] TTS is disabled');
      return;
    }

    if ('speechSynthesis' in window) {
      console.log('[VoiceService] Using browser speech synthesis');

      // Safari/iOS workaround: cancel any pending speech first
      if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
        console.log('[VoiceService] Canceling previous speech (Safari workaround)');
        window.speechSynthesis.cancel();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      utterance.lang = 'en-US'; // Explicitly set language

      // Try to set a voice (helps with some browsers)
      const voices = window.speechSynthesis.getVoices();
      console.log(`[VoiceService] Available voices: ${voices.length}`);

      if (voices.length > 0) {
        // Prefer English voices
        const englishVoice = voices.find(voice => voice.lang.startsWith('en-US'))
                          || voices.find(voice => voice.lang.startsWith('en'));
        if (englishVoice) {
          utterance.voice = englishVoice;
          console.log(`[VoiceService] Selected voice: ${englishVoice.name} (${englishVoice.lang})`);
        } else {
          console.log('[VoiceService] No English voice found, using default');
        }
      } else {
        console.warn('[VoiceService] No voices available yet, using default');
      }

      utterance.onstart = () => {
        console.log('[VoiceService] ✓ Browser TTS started:', text.substring(0, 50));
      };

      utterance.onend = () => {
        console.log('[VoiceService] ✓ Browser TTS ended');
      };

      utterance.onerror = (event) => {
        console.error('[VoiceService] ✗ Browser TTS error:', event);
        console.error('[VoiceService] Error details:', {
          error: event.error,
          charIndex: event.charIndex,
          elapsedTime: event.elapsedTime
        });
        if (event.error === 'not-allowed') {
          console.warn('[VoiceService] Browser TTS blocked by autoplay policy. User interaction required first.');
        } else if (event.error === 'canceled') {
          console.warn('[VoiceService] Speech was canceled');
        } else if (event.error === 'interrupted') {
          console.warn('[VoiceService] Speech was interrupted');
        }
      };

      utterance.onpause = () => {
        console.log('[VoiceService] Speech paused');
      };

      utterance.onresume = () => {
        console.log('[VoiceService] Speech resumed');
      };

      // Check synthesis state before speaking
      console.log('[VoiceService] SpeechSynthesis state:', {
        speaking: window.speechSynthesis.speaking,
        pending: window.speechSynthesis.pending,
        paused: window.speechSynthesis.paused
      });

      window.speechSynthesis.speak(utterance);
      console.log('[VoiceService] Browser TTS queued');

      // Safari workaround: force resume if needed
      setTimeout(() => {
        if (window.speechSynthesis.paused) {
          console.log('[VoiceService] Forcing resume (Safari workaround)');
          window.speechSynthesis.resume();
        }
      }, 100);
    } else {
      console.warn('[VoiceService] Speech synthesis not supported in this browser');
    }
  }

  stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  isGoogleAvailable() {
    return this.googleAvailable;
  }
}

export const voiceService = new VoiceService();
