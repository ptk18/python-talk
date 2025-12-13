import { voiceAPI, googleSpeechAPI } from './api';
import type { VoiceTranscriptionResponse } from './api';

export type VoiceEngine = 'standard' | 'google';

export class VoiceService {
  private static instance: VoiceService;
  private currentEngine: VoiceEngine = 'standard';
  private voicesLoaded: boolean = false;

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

  /**
   * Transcribe audio using the currently selected voice engine
   */
  async transcribe(audioFile: File, language: string): Promise<VoiceTranscriptionResponse> {
    if (this.currentEngine === 'google') {
      try {
        const languageCode = this.mapLanguageCode(language);
        const result = await googleSpeechAPI.speechToText(audioFile, languageCode);
        return result;
      } catch (error) {
        try {
          const result = await voiceAPI.transcribe(audioFile, language);
          return result;
        } catch (fallbackError) {
          throw fallbackError;
        }
      }
    } else {
      try {
        const result = await voiceAPI.transcribe(audioFile, language);
        return result;
      } catch (error) {
        throw error;
      }
    }
  }

  /**
   * Text to speech using the currently selected voice engine
   */
  async speak(text: string, language: string = 'en'): Promise<void> {
    if (this.currentEngine === 'google') {
      try {
        const languageCode = this.mapLanguageCode(language);
        const audioBlob = await googleSpeechAPI.textToSpeech(text, languageCode);
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
   * Map short language codes to full Google Speech language codes
   */
  private mapLanguageCode(lang: string): string {
    const languageMap: Record<string, string> = {
      'en': 'en-US',
      'th': 'th-TH',
      'es': 'es-ES',
      'fr': 'fr-FR',
      'de': 'de-DE',
      'ja': 'ja-JP',
      'zh': 'zh-CN',
    };
    return languageMap[lang] || 'en-US';
  }

  /**
   * Play audio blob
   */
  private async playAudioBlob(blob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);

      const savedVolume = localStorage.getItem('pytalk_volume');
      if (savedVolume) {
        audio.volume = Number(savedVolume) / 100;
      } else {
        audio.volume = 0.7;
      }

      const cleanup = () => {
        URL.revokeObjectURL(audioUrl);
        audio.remove();
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
   * Fallback to browser's built-in speech synthesis (FEMALE voice)
   */
  private fallbackSpeak(text: string): void {
    if (!('speechSynthesis' in window)) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    const voices = window.speechSynthesis.getVoices();

    const femaleVoice = voices.find(voice =>
      voice.name.toLowerCase().includes('female') ||
      voice.name.toLowerCase().includes('samantha') ||
      voice.name.toLowerCase().includes('victoria') ||
      voice.name.toLowerCase().includes('karen') ||
      voice.name.toLowerCase().includes('zira') ||
      (voice.name.toLowerCase().includes('google us english') && voice.name.toLowerCase().includes('female'))
    );

    if (femaleVoice) {
      utterance.voice = femaleVoice;
    } else {
      const englishVoice = voices.find(v => v.lang.startsWith('en'));
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
    }

    utterance.pitch = 1.1;
    utterance.rate = 1.25;
    utterance.lang = 'en-US';

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
