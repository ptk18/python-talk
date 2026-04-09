import { voiceAPI, googleSpeechAPI } from './api.js';

const TTS_TRANSLATIONS = {
  th: {
    // Common
    'Saved!': 'บันทึกแล้ว!',
    'All set!': 'เรียบร้อย!',
    'Save failed.': 'บันทึกไม่สำเร็จ',
    'Undo': 'เลิกทำ',
    'Undo failed': 'เลิกทำไม่สำเร็จ',
    'Nothing to undo': 'ไม่มีอะไรให้เลิกทำ',
    'Listening': 'กำลังฟัง',
    'Canvas cleared': 'ล้างแคนวาสแล้ว',

    // Voice
    'Transcription failed. Please try again.': 'การถอดเสียงล้มเหลว กรุณาลองอีกครั้ง',
    'Transcription error. Please try again.': 'เกิดข้อผิดพลาดในการถอดเสียง กรุณาลองอีกครั้ง',
    'Microphone access denied': 'ไม่สามารถเข้าถึงไมโครโฟนได้',
    'Voice transcription error': 'เกิดข้อผิดพลาดในการแปลงเสียง',
    "I couldn't understand that. Please try again": 'ฉันไม่เข้าใจ กรุณาลองอีกครั้ง',

    // Commands
    'Command translated': 'แปลคำสั่งแล้ว',
    'Command executed': 'คำสั่งสำเร็จ',
    'Command executed successfully': 'ดำเนินการคำสั่งสำเร็จ',
    "I couldn't understand that command. Please try again with a different phrase.": 'ฉันไม่เข้าใจคำสั่งนี้ กรุณาลองใหม่ด้วยประโยคอื่น',
    'Translation failed, please try again': 'การแปลล้มเหลว กรุณาลองอีกครั้ง',
    'Invalid command': 'คำสั่งไม่ถูกต้อง',
    'I encountered an error. Please try again': 'เกิดข้อผิดพลาด กรุณาลองอีกครั้ง',
    'No matching commands found': 'ไม่พบคำสั่งที่ตรงกัน',
    'commands executed successfully': 'คำสั่งดำเนินการสำเร็จ',

    // Code execution
    'Running turtle code': 'กำลังรันโค้ดเต่า',
    'Output ready!': 'ผลลัพธ์พร้อมแล้ว!',
    'Please try again': 'กรุณาลองอีกครั้ง',
    'Turtle graphics running!': 'Turtle graphics กำลังทำงาน!',
    'Runner file is empty. Please add some commands': 'ไฟล์ runner ว่างเปล่า กรุณาเพิ่มคำสั่ง',
    'Runner file not found. Please initialize the session first': 'ไม่พบไฟล์ runner กรุณาเริ่มต้นเซสชันก่อน',

    // RunView
    "Code Space ready! Let's run some code.": 'Code Space พร้อมแล้ว! มาเขียนโค้ดกัน',
    'Please enter some code first.': 'กรุณาใส่โค้ดก่อน',
    'Running your code...': 'กำลังรันโค้ด...',
    'Code ran successfully!': 'รันโค้ดสำเร็จ!',
    'Execution failed. Check the error.': 'รันไม่สำเร็จ ตรวจสอบข้อผิดพลาด',
    'Output cleared.': 'ล้างผลลัพธ์แล้ว',
    'Switched to text mode.': 'เปลี่ยนเป็นโหมดข้อความ',
    'Switched to graphic mode.': 'เปลี่ยนเป็นโหมดกราฟิก',
    'File loaded!': 'โหลดไฟล์แล้ว!',
    'File loading failed.': 'โหลดไฟล์ไม่สำเร็จ',

    // FilePanel
    'File created successfully': 'สร้างไฟล์สำเร็จ',
    'Failed to create file': 'สร้างไฟล์ไม่สำเร็จ',
    'File deleted successfully': 'ลบไฟล์สำเร็จ',
    'Failed to delete file': 'ลบไฟล์ไม่สำเร็จ',

    // HomeView
    'App created!': 'สร้างแอปแล้ว!',
    "Couldn't create the app.": 'สร้างแอปไม่สำเร็จ',
    'App updated!': 'อัปเดตแอปแล้ว!',
    'Update failed.': 'อัปเดตไม่สำเร็จ',
    'App deleted.': 'ลบแอปแล้ว',
    'Deletion failed.': 'ลบไม่สำเร็จ',
    'Removed from favorites.': 'ลบออกจากรายการโปรดแล้ว',
    'Added to favorites!': 'เพิ่มในรายการโปรดแล้ว!',
  }
};

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
    this.lastSpeakTime = 0;
    this.debounceDelay = 100;
    this.isSpeaking = false;
    this.currentSpeechId = null;
    this.speechRate = 1.0;
    this.currentAudio = null;
    this.language = localStorage.getItem('language') || 'en';
    this.googleCheckPromise = null;
    this.init();
    this.initVoices();
  }

  async init() {
    const savedEngine = localStorage.getItem('voice_engine') || 'google';
    this.engine = savedEngine;

    const savedTTSEngine = localStorage.getItem('tts_engine') || 'google';
    this.ttsEngine = savedTTSEngine;

    // Load saved speech rate
    const savedRate = localStorage.getItem('tts_rate');
    if (savedRate) {
      this.speechRate = parseFloat(savedRate);
    }

    // Check Google API availability in background (non-blocking)
    this.googleCheckPromise = googleSpeechAPI.checkStatus()
      .then(status => {
        this.googleAvailable = status.available;
        console.log('[VoiceService] Google Speech API available:', status.available);
      })
      .catch(err => {
        console.warn('[VoiceService] Google Speech API not available:', err);
        this.googleAvailable = false;
      });
  }

  waitForGoogleCheck() {
    return this.googleCheckPromise || Promise.resolve();
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
          console.log('[VoiceService] Voice loading optimistic timeout (500ms), using defaults');
          this.voicesLoaded = true;
          resolve([]);
        }
      }, 500);
    });
  }

  selectBestVoice(voices, language = 'en') {
    if (language === 'th') {
      return (
        voices.find(v => v.name.includes('Google') && v.lang === 'th-TH') ||
        voices.find(v => v.lang === 'th-TH') ||
        voices.find(v => v.lang.startsWith('th')) ||
        voices[0]
      );
    }

    // English priority order
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

    // Eager voice loading
    this.eagerLoadVoices();
  }

  eagerLoadVoices() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    // Force voice loading
    window.speechSynthesis.getVoices();

    // Chrome workaround: speak a silent utterance to unlock TTS and trigger voices
    const unlock = new SpeechSynthesisUtterance('');
    unlock.volume = 0;
    window.speechSynthesis.speak(unlock);
    window.speechSynthesis.cancel();

    console.log('[VoiceService] Eager voice loading triggered');
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
    return this.ttsEngine || localStorage.getItem('tts_engine') || 'google';
  }

  setLanguage(lang) {
    this.language = lang;
    // Stop any current speech so the next speak() call uses the new language cleanly
    this.stopSpeaking();
    console.log(`[VoiceService] Language set to: ${lang}`);
  }

  getLanguage() {
    // Always read from localStorage as source of truth to handle multiple module instances
    const stored = localStorage.getItem('language');
    if (stored) {
      this.language = stored;
      return stored;
    }
    return this.language || 'en';
  }

  setSpeechRate(rate) {
    // Clamp rate between 0.5 and 2.0
    this.speechRate = Math.max(0.5, Math.min(2.0, rate));
    localStorage.setItem('tts_rate', this.speechRate.toString());
    console.log(`[VoiceService] Speech rate set to: ${this.speechRate}x`);
  }

  getSpeechRate() {
    const saved = localStorage.getItem('tts_rate');
    if (saved) {
      this.speechRate = parseFloat(saved);
    }
    return this.speechRate;
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
    console.log(`[VoiceService] STT Engine: ${currentEngine}`);

    if (currentEngine === 'google' && this.googleAvailable) {
      console.log('[VoiceService] Using Google Cloud Speech-to-Text');
      const result = await this.transcribeWithRetry(() =>
        googleSpeechAPI.speechToText(audioFile, language)
      );
      console.log(`[VoiceService] Transcription successful`);
      console.log(`[VoiceService] Model: Google Cloud Speech-to-Text`);
      console.log(`[VoiceService] Text: "${result.text}"`);
      console.log(`[VoiceService] Confidence: ${result.confidence || 'N/A'}`);
      return result;
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

  async speak(text, language) {
    language = language || this.getLanguage();
    if (!text) return;

    // Auto-translate TTS text based on language
    if (language !== 'en' && TTS_TRANSLATIONS[language]) {
      text = TTS_TRANSLATIONS[language][text] || text;
    }

    const now = Date.now();
    if (now - this.lastSpeakTime < this.debounceDelay) {
      console.log('[VoiceService] Debounced - too soon after last speak');
      return;
    }

    // Interrupt current speech to speak the new message
    if (this.isSpeaking) {
      this.stopSpeaking();
    }

    this.lastSpeakTime = now;

    const ttsEnabled = localStorage.getItem('tts_enabled');
    if (ttsEnabled === 'false') {
      console.log('[VoiceService] TTS is disabled');
      return;
    }

    const currentTTSEngine = this.getTTSEngine();

    if (currentTTSEngine === 'google' && this.googleAvailable) {
      try {
        console.log('[VoiceService] Using Google Cloud TTS');
        this.isSpeaking = true;

        const audioBlob = await googleSpeechAPI.textToSpeech(text, this.speechRate, language);
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        this.currentAudio = audio;

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          this.isSpeaking = false;
          this.currentAudio = null;
        };

        audio.onerror = (err) => {
          console.error('[VoiceService] Audio playback error:', err);
          URL.revokeObjectURL(audioUrl);
          this.isSpeaking = false;
          this.currentAudio = null;
        };

        // Handle autoplay policy rejection
        try {
          await audio.play();
          console.log('[VoiceService] Google TTS audio played successfully');
        } catch (playError) {
          console.error('[VoiceService] Audio play failed (likely autoplay policy):', playError);
          this.isSpeaking = false;

          // Only fallback if NOT already speaking with browser
          if (!window.speechSynthesis.speaking) {
            this.speakWithBrowser(text, language);
          }
        }
      } catch (err) {
        console.error('[VoiceService] Google TTS failed, falling back to browser:', err);
        this.isSpeaking = false;

        // Only fallback if NOT already speaking
        if (!window.speechSynthesis.speaking) {
          this.speakWithBrowser(text, language);
        }
      }
    } else {
      this.speakWithBrowser(text, language);
    }
  }

  async speakWithBrowser(text, language = 'en') {
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
    this.isSpeaking = false;

    // Don't wait for voices - speak immediately with default if needed
    // Voices will upgrade later when onvoiceschanged fires
    if (this.voiceLoadPromise && !this.voicesLoaded) {
      console.log('[VoiceService] Speaking optimistically (voices still loading)');
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = this.getSpeechRate();
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    const langMap = { en: 'en-US', th: 'th-TH' };
    utterance.lang = langMap[language] || 'en-US';

    // Select voice based on current language
    const voices = this.cachedVoices.length > 0 ? this.cachedVoices : window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const voice = this.selectBestVoice(voices, language);
      if (voice) {
        utterance.voice = voice;
        console.log(`[VoiceService] Selected voice for ${language}: ${voice.name}`);
      }
    } else {
      console.warn('[VoiceService] No voices available, using default');
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      console.log('[VoiceService] Browser TTS started:', text.substring(0, 50));
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      console.log('[VoiceService] Browser TTS ended');
    };

    utterance.onerror = (event) => {
      this.isSpeaking = false;

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
    // Stop Google TTS audio if playing
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    // Stop browser TTS
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.isSpeaking = false;
  }

  isGoogleAvailable() {
    return this.googleAvailable;
  }
}

export const voiceService = new VoiceService();
