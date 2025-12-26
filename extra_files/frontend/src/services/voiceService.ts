import { voiceAPI, googleSpeechAPI } from './api';
import type { VoiceTranscriptionResponse } from './api';

export type VoiceEngine = 'standard' | 'google';

export class VoiceService {
  private static instance: VoiceService;
  private currentEngine: VoiceEngine = 'standard';
  private voicesLoaded: boolean = false;
  private isMuted: boolean = false;
  private currentAudio: HTMLAudioElement | null = null;

  private constructor() {
    // Load saved engine preference or default to 'standard'
    const savedEngine = localStorage.getItem('pytalk_voice_engine');
    this.currentEngine = (savedEngine === 'google' || savedEngine === 'standard') ? savedEngine : 'standard';

    console.log(`[VoiceService] Initialized with engine: ${this.currentEngine}`);

    if ('speechSynthesis' in window) {
      // Load voices immediately
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        this.voicesLoaded = true;
      }

      // Also set up listener for when voices load
      window.speechSynthesis.onvoiceschanged = () => {
        this.voicesLoaded = true;
        console.log('[VoiceService] Browser voices loaded:', window.speechSynthesis.getVoices().length);
      };
    }
  }

  static getInstance(): VoiceService {
    if (!VoiceService.instance) {
      VoiceService.instance = new VoiceService();
    }
    return VoiceService.instance;
  }

  setEngine(engine: VoiceEngine): void {
    this.currentEngine = engine;
    localStorage.setItem('pytalk_voice_engine', engine);
  }

  getEngine(): VoiceEngine {
    return this.currentEngine;
  }

  setMuted(muted: boolean): void {
    this.isMuted = muted;
    if (muted) {
      // Stop any ongoing speech
      window.speechSynthesis.cancel();
      // Stop any ongoing audio playback
      if (this.currentAudio) {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
        this.currentAudio = null;
      }
    }
  }

  isTTSMuted(): boolean {
    return this.isMuted;
  }

  /**
   * Transcribe audio using the currently selected voice engine
   * Defaults to Whisper (more reliable), with Google as fallback
   * @param audioFile - Audio file to transcribe
   * @param language - Language code ('en' or 'th')
   */
  async transcribe(audioFile: File, language: string = 'en'): Promise<VoiceTranscriptionResponse> {
    let result: VoiceTranscriptionResponse;

    // Only use Google if explicitly selected by user AND language is English
    // Google doesn't support Thai in our current setup
    const useGoogle = this.currentEngine === 'google' && language === 'en';

    if (useGoogle) {
      try {
        console.log(`[VoiceService] Using Google Speech (English)`);
        result = await googleSpeechAPI.speechToText(audioFile);

        // Check if Google actually transcribed anything
        if (!result.text || result.text.trim() === '' || result.error) {
          console.warn(`[VoiceService] Google returned empty/error result: ${result.error || 'empty text'}, falling back to Whisper`);
          result = await voiceAPI.transcribe(audioFile, language);
          console.log(`[VoiceService] Whisper fallback result: ${result.text}`);
        } else {
          console.log(`[VoiceService] Google transcription: "${result.text}", confidence: ${result.confidence}`);
        }
      } catch (error) {
        console.warn('[VoiceService] Google Speech failed, falling back to Whisper:', error);
        try {
          result = await voiceAPI.transcribe(audioFile, language);
          console.log(`[VoiceService] Whisper fallback result: ${result.text}`);
        } catch (fallbackError) {
          throw fallbackError;
        }
      }
    } else {
      try {
        const langName = language === 'th' ? 'Thai' : 'English';
        const modelName = language === 'th'
          ? 'Whisper Thai (nectec/Pathumma-whisper-th-large-v3)'
          : 'Whisper English (distil-whisper/distil-large-v3)';

        console.log(`[VoiceService] Using ${modelName}`);
        result = await voiceAPI.transcribe(audioFile, language);
        console.log(`[VoiceService] ✅ Transcription successful`);
        console.log(`[VoiceService] Model: ${modelName}`);
        console.log(`[VoiceService] Text: "${result.text}"`);
        console.log(`[VoiceService] Confidence: ${result.confidence || 'N/A'}`);
      } catch (error) {
        console.error('[VoiceService] Whisper failed:', error);
        throw error;
      }
    }

    return result;
  }

  /**
   * Text to speech using the currently selected voice engine
   * - Standard: Uses browser's Web Audio API (free, female voice)
   * - Google: Uses Google Cloud TTS API (requires credentials, male voice)
   */
  async speak(text: string): Promise<void> {
    // Don't speak if muted
    if (this.isMuted) return;

    if (this.currentEngine === 'google') {
      try {
        const audioBlob = await googleSpeechAPI.textToSpeech(text);
        await this.playAudioBlob(audioBlob);
      } catch (error) {
        console.error('[VoiceService] Google TTS failed, falling back to browser TTS:', error);
        this.browserSpeak(text);
      }
    } else {
      // Standard engine - use browser's built-in TTS (free)
      this.browserSpeak(text);
    }
  }

  /**
   * Check if Google Speech is available
   */
  async checkGoogleAvailability(): Promise<boolean> {
    try {
      const status = await googleSpeechAPI.checkStatus();
      return status.available;
    } catch (error) {
      return false;
    }
  }

  /**
   * Play audio blob
   */
  private async playAudioBlob(blob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      // Don't play if muted
      if (this.isMuted) {
        resolve();
        return;
      }

      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      this.currentAudio = audio;

      const savedVolume = localStorage.getItem('pytalk_volume');
      if (savedVolume) {
        audio.volume = Number(savedVolume) / 100;
      } else {
        audio.volume = 0.7;
      }

      const cleanup = () => {
        URL.revokeObjectURL(audioUrl);
        audio.remove();
        if (this.currentAudio === audio) {
          this.currentAudio = null;
        }
      };

      audio.onended = () => {
        cleanup();
        resolve();
      };

      audio.onerror = () => {
        cleanup();
        reject(new Error('Audio playback failed'));
      };

      audio.play().catch((err) => {
        cleanup();
        reject(err);
      });
    });
  }

  /**
   * Browser's built-in speech synthesis (Standard Female Voice - Free)
   */
  private browserSpeak(text: string): void {
    if (!('speechSynthesis' in window)) {
      console.warn('[VoiceService] Browser speech synthesis not available');
      return;
    }

    // Don't speak if muted
    if (this.isMuted) {
      console.log('[VoiceService] TTS is muted, skipping speech');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Ensure voices are loaded
    const voices = window.speechSynthesis.getVoices();
    if (voices.length === 0) {
      console.warn('[VoiceService] Voices not loaded yet, waiting for voiceschanged event...');

      // Wait for voices to load with a timeout
      const speakWhenReady = () => {
        const loadedVoices = window.speechSynthesis.getVoices();
        if (loadedVoices.length > 0) {
          console.log('[VoiceService] Voices loaded, speaking now');
          this.performBrowserSpeak(text, loadedVoices);
        } else {
          console.error('[VoiceService] ✗ Voices still not loaded after event');
        }
      };

      // Set up one-time listener for voices loaded
      const onVoicesChanged = () => {
        window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
        speakWhenReady();
      };
      window.speechSynthesis.addEventListener('voiceschanged', onVoicesChanged);

      // Also try with a timeout as fallback
      setTimeout(() => {
        window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
        const retriedVoices = window.speechSynthesis.getVoices();
        if (retriedVoices.length > 0) {
          console.log('[VoiceService] Voices loaded via timeout, speaking now');
          this.performBrowserSpeak(text, retriedVoices);
        } else {
          console.error('[VoiceService] ✗ Failed to load voices after 1 second - TTS unavailable');
        }
      }, 1000);

      return;
    }

    this.performBrowserSpeak(text, voices);
  }

  private performBrowserSpeak(text: string, voices: SpeechSynthesisVoice[]): void {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';

    // Prefer female English voices for standard engine
    const selectedVoice = voices.find(voice =>
      voice.lang.startsWith('en') && (
        voice.name.toLowerCase().includes('female') ||
        voice.name.toLowerCase().includes('samantha') ||
        voice.name.toLowerCase().includes('victoria') ||
        voice.name.toLowerCase().includes('karen') ||
        voice.name.toLowerCase().includes('zira')
      )
    ) || voices.find(v => v.lang.startsWith('en'));

    if (selectedVoice) {
      utterance.voice = selectedVoice;
      console.log(`[VoiceService] Using browser voice: ${selectedVoice.name}`);
    } else {
      console.warn('[VoiceService] No suitable voice found, using default');
    }

    utterance.pitch = 1.1;
    utterance.rate = 1.25;

    const savedVolume = localStorage.getItem('pytalk_volume');
    if (savedVolume) {
      utterance.volume = Number(savedVolume) / 100;
      console.log(`[VoiceService] Volume set to: ${savedVolume}%`);
    } else {
      utterance.volume = 0.7;
      console.log('[VoiceService] Volume set to: 70% (default)');
    }

    // Add event listeners for debugging
    let speechStarted = false;

    utterance.onstart = () => {
      speechStarted = true;
      console.log('[VoiceService] ✓ Speech started:', text.substring(0, 50));
    };

    utterance.onend = () => {
      console.log('[VoiceService] ✓ Speech ended');
    };

    utterance.onerror = (event) => {
      if (event.error === 'not-allowed') {
        console.warn('[VoiceService] ⚠️ Speech blocked: User interaction required first');
        console.warn('[VoiceService] TTS will work after user clicks or types on the page');
      } else {
        console.error('[VoiceService] ✗ Speech error:', event.error, event);
      }
    };

    console.log(`[VoiceService] Speaking: "${text}"`);
    console.log('[VoiceService] Speech synthesis state:', {
      speaking: window.speechSynthesis.speaking,
      pending: window.speechSynthesis.pending,
      paused: window.speechSynthesis.paused
    });

    window.speechSynthesis.speak(utterance);

    // Check if speech actually started after a delay
    setTimeout(() => {
      if (!speechStarted) {
        console.error('[VoiceService] WARNING: Speech was queued but did not start!');
        console.error('[VoiceService] Current state:', {
          speaking: window.speechSynthesis.speaking,
          pending: window.speechSynthesis.pending,
          paused: window.speechSynthesis.paused
        });
        console.error('[VoiceService] Possible issues:');
        console.error('  1. System volume is muted or very low');
        console.error('  2. Browser needs user interaction first (you clicked, so this should be fine)');
        console.error('  3. Speech synthesis is suspended');

        // Try to resume if suspended
        if (window.speechSynthesis.paused) {
          console.log('[VoiceService] Attempting to resume paused speech...');
          window.speechSynthesis.resume();
        }
      }
    }, 200);
  }
}

// Export singleton instance
export const voiceService = VoiceService.getInstance();
