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
    this.currentEngine = 'standard';

    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        this.voicesLoaded = true;
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
   */
  async transcribe(audioFile: File): Promise<VoiceTranscriptionResponse> {
    let result: VoiceTranscriptionResponse;

    // Only use Google if explicitly selected by user
    const useGoogle = this.currentEngine === 'google';

    if (useGoogle) {
      try {
        console.log(`[VoiceService] Using Google Speech (English)`);
        result = await googleSpeechAPI.speechToText(audioFile);

        // Check if Google actually transcribed anything
        if (!result.text || result.text.trim() === '' || result.error) {
          console.warn(`[VoiceService] Google returned empty/error result: ${result.error || 'empty text'}, falling back to Whisper`);
          result = await voiceAPI.transcribe(audioFile);
          console.log(`[VoiceService] Whisper fallback result: ${result.text}`);
        } else {
          console.log(`[VoiceService] Google transcription: "${result.text}", confidence: ${result.confidence}`);
        }
      } catch (error) {
        console.warn('[VoiceService] Google Speech failed, falling back to Whisper:', error);
        try {
          result = await voiceAPI.transcribe(audioFile);
          console.log(`[VoiceService] Whisper fallback result: ${result.text}`);
        } catch (fallbackError) {
          throw fallbackError;
        }
      }
    } else {
      try {
        console.log(`[VoiceService] Using Whisper (English)`);
        result = await voiceAPI.transcribe(audioFile);
        console.log(`[VoiceService] Whisper result: text="${result.text}", confidence=${result.confidence}`);
      } catch (error) {
        console.error('[VoiceService] Whisper failed:', error);
        throw error;
      }
    }

    return result;
  }

  /**
   * Text to speech using the currently selected voice engine
   */
  async speak(text: string): Promise<void> {
    // Don't speak if muted
    if (this.isMuted) return;

    if (this.currentEngine === 'google') {
      try {
        const audioBlob = await googleSpeechAPI.textToSpeech(text);
        await this.playAudioBlob(audioBlob);
      } catch (error) {
        this.fallbackSpeak(text);
      }
    } else {
      this.fallbackSpeak(text);
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
   * Fallback to browser's built-in speech synthesis
   */
  private fallbackSpeak(text: string): void {
    if (!('speechSynthesis' in window)) {
      return;
    }

    // Don't speak if muted
    if (this.isMuted) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';

    const voices = window.speechSynthesis.getVoices();

    // Prefer female English voices
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
    }

    utterance.pitch = 1.1;
    utterance.rate = 1.25;

    const savedVolume = localStorage.getItem('pytalk_volume');
    if (savedVolume) {
      utterance.volume = Number(savedVolume) / 100;
    } else {
      utterance.volume = 0.7;
    }

    window.speechSynthesis.speak(utterance);
  }
}

// Export singleton instance
export const voiceService = VoiceService.getInstance();
