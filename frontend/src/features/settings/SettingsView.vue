<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">{{ t.settings.pageTitle }}</h2>
      </header>

      <div class="content-area settings-content">
        <div class="settings-container">
          <!-- Language Selection Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">{{ t.settings.languageSelection }}</h3>
              <p class="section-description">{{ t.settings.languageDescription }}</p>
            </div>
            <div class="settings-options">
              <div
                v-for="lang in languages"
                :key="lang.code"
                class="option-card"
                :class="{ 'active': selectedLanguage === lang.code }"
                @click="selectLanguage(lang.code)"
              >
                <div class="option-content">
                  <span class="option-icon">{{ lang.flag }}</span>
                  <div class="option-info">
                    <div class="option-label">{{ lang.name }}</div>
                    <div class="option-subtitle">{{ lang.nativeName }}</div>
                  </div>
                </div>
                <div class="option-check" v-if="selectedLanguage === lang.code">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- TTS Enable/Disable Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">{{ t.settings.textToSpeech }}</h3>
              <p class="section-description">{{ t.settings.ttsDescription }}</p>
            </div>
            <div class="toggle-container">
              <div class="toggle-row">
                <div class="toggle-info">
                  <div class="toggle-label">{{ t.settings.enableTTS }}</div>
                  <div class="toggle-description">{{ t.settings.turnVoiceOnOff }}</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" v-model="ttsEnabledState" @change="toggleTTS">
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <button
                class="test-tts-btn"
                @click="testTTS"
                :disabled="!ttsEnabledState"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 9V15H7L12 20V4L7 9H3ZM16.5 12C16.5 10.23 15.48 8.71 14 7.97V16.02C15.48 15.29 16.5 13.77 16.5 12Z" fill="currentColor"/>
                </svg>
                {{ t.settings.testVoice }}
              </button>
            </div>
          </div>

          <!-- TTS Model Selection Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">{{ t.settings.ttsModel }}</h3>
              <p class="section-description">{{ t.settings.ttsModelDescription }}</p>
            </div>
            <div class="settings-options">
              <div
                v-for="voice in ttsModels"
                :key="voice.id"
                class="option-card"
                :class="{ 'active': selectedTTSModel === voice.id, 'disabled': !ttsEnabledState }"
                @click="ttsEnabledState && selectVoiceModel(voice.id)"
              >
                <div class="option-content">
                  <div class="option-icon-voice">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 9V15H7L12 20V4L7 9H3ZM16.5 12C16.5 10.23 15.48 8.71 14 7.97V16.02C15.48 15.29 16.5 13.77 16.5 12ZM14 3.23V5.29C16.89 6.15 19 8.83 19 12C19 15.17 16.89 17.85 14 18.71V20.77C18.01 19.86 21 16.28 21 12C21 7.72 18.01 4.14 14 3.23Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="option-info">
                    <div class="option-label">{{ voice.name }}</div>
                    <div class="option-subtitle">{{ voice.description }}</div>
                  </div>
                </div>
                <div class="option-check" v-if="selectedTTSModel === voice.id">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Speech Rate Control Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">{{ t.settings.speechRate }}</h3>
              <p class="section-description">{{ t.settings.speechRateDescription }}</p>
            </div>

            <div class="rate-control-container">
              <!-- Rate Slider -->
              <div class="rate-slider-wrapper">
                <label class="rate-label">
                  {{ t.settings.currentRate }}: <strong>{{ speechRateLabel }}</strong>
                </label>
                <input
                  type="range"
                  class="rate-slider"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  :value="speechRateValue"
                  @input="onSpeechRateChange(parseFloat($event.target.value))"
                  :disabled="!ttsEnabledState"
                />
                <div class="rate-markers">
                  <span>0.5x</span>
                  <span>1.0x</span>
                  <span>1.5x</span>
                  <span>2.0x</span>
                </div>
              </div>

              <!-- Rate Presets -->
              <div class="rate-presets">
                <button
                  v-for="preset in ratePresets"
                  :key="preset.value"
                  class="preset-btn"
                  :class="{ 'active': speechRateValue === preset.value }"
                  @click="onSpeechRateChange(preset.value)"
                  :disabled="!ttsEnabledState"
                >
                  {{ preset.label }}
                </button>
              </div>

              <!-- Test Button -->
              <button
                class="test-rate-btn"
                @click="testSpeechRate"
                :disabled="!ttsEnabledState"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
                </svg>
                {{ t.settings.testRate }}
              </button>
            </div>
          </div>

          <!-- STT Model Selection Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">{{ t.settings.speechToText }}</h3>
              <p class="section-description">{{ t.settings.sttDescription }}</p>
            </div>
            <div class="settings-options">
              <div
                v-for="stt in sttModels"
                :key="stt.id"
                class="option-card"
                :class="{ 'active': selectedSTTModel === stt.id, 'disabled': stt.disabled }"
                @click="!stt.disabled && selectSTTModel(stt.id)"
              >
                <div class="option-content">
                  <div class="option-icon-voice">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z" fill="currentColor"/>
                      <path d="M17 11C17 13.76 14.76 16 12 16C9.24 16 7 13.76 7 11H5C5 14.53 7.61 17.43 11 17.92V21H13V17.92C16.39 17.43 19 14.53 19 11H17Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="option-info">
                    <div class="option-label">{{ stt.name }}</div>
                    <div class="option-subtitle">{{ stt.description }}</div>
                  </div>
                </div>
                <div class="option-check" v-if="selectedSTTModel === stt.id">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import TopToolbar from '@/shared/components/TopToolbar.vue';
import Sidebar from '@/shared/components/Sidebar.vue';
import { useLanguage, useTTS, useSTT, voiceService } from '@py-talk/shared';
import { useTranslations } from '@/utils/translations';

const { language, setLanguage } = useLanguage();
const { ttsEnabled, ttsEngine, ttsRate, setTTSEnabled, setTTSEngine, setTTSRate } = useTTS();
const { sttEngine, setSTTEngine } = useSTT();

const t = computed(() => useTranslations(language.value));

const languages = computed(() => [
  { code: 'en', name: t.value.settings.english, nativeName: 'English', flag: '🇺🇸' },
  { code: 'th', name: t.value.settings.thai, nativeName: 'ไทย', flag: '🇹🇭' }
]);

const googleAvailable = ref(voiceService.isGoogleAvailable());
const ttsEnabledState = ref(true);
const speechRateValue = ref(1.0);

const ttsModels = computed(() => {
  const models = [
    {
      id: 'browser',
      name: t.value.settings.browserTTS,
      description: t.value.settings.browserTTSDescription
    }
  ];

  if (googleAvailable.value) {
    models.push({
      id: 'google',
      name: t.value.settings.googleTTS,
      description: t.value.settings.googleTTSDescription
    });
  }

  return models;
});

const selectedLanguage = computed(() => language.value);
const selectedTTSModel = computed(() => ttsEngine.value);
const selectedSTTModel = computed(() => sttEngine.value);

const sttModels = computed(() => {
  const models = [
    {
      id: 'whisper',
      name: t.value.settings.whisperSTT,
      description: t.value.settings.whisperSTTDescription,
      disabled: false
    }
  ];

  models.push({
    id: 'google',
    name: t.value.settings.googleSTT,
    description: t.value.settings.googleSTTDescription,
    disabled: !googleAvailable.value
  });

  return models;
});

const selectLanguage = (code) => {
  setLanguage(code);
};

const selectVoiceModel = (id) => {
  setTTSEngine(id);
  voiceService.setTTSEngine(id);
  console.log(`[Settings] TTS engine changed to: ${id}`);
};

const selectSTTModel = (id) => {
  setSTTEngine(id);
  voiceService.setEngine(id);
  console.log(`[Settings] STT engine changed to: ${id}`);
};

const toggleTTS = () => {
  setTTSEnabled(ttsEnabledState.value);
  console.log(`[Settings] TTS ${ttsEnabledState.value ? 'enabled' : 'disabled'}`);
};

const testTTS = () => {
  // Enable audio context first
  voiceService.enableAudioContext();
  const testMessage = selectedTTSModel.value === 'google'
    ? 'Testing Google Cloud Text to Speech. This is a high quality voice synthesis.'
    : 'Testing browser text to speech. This uses your browser\'s built-in voice.';
  voiceService.speak(testMessage);
  console.log('[Settings] Testing TTS with message:', testMessage);
};

const speechRateLabel = computed(() => {
  return `${speechRateValue.value.toFixed(1)}x`;
});

const ratePresets = computed(() => [
  { value: 0.5, label: '0.5x', description: t.value.settings.verySlow },
  { value: 0.75, label: '0.75x', description: t.value.settings.slow },
  { value: 1.0, label: '1.0x', description: t.value.settings.normal },
  { value: 1.25, label: '1.25x', description: t.value.settings.fast },
  { value: 1.5, label: '1.5x', description: t.value.settings.veryFast },
  { value: 2.0, label: '2.0x', description: t.value.settings.fastest }
]);

const onSpeechRateChange = (rate) => {
  speechRateValue.value = rate;
  setTTSRate(rate);
  voiceService.setSpeechRate(rate);
  console.log(`[Settings] Speech rate changed to: ${rate}x`);
};

const testSpeechRate = () => {
  voiceService.enableAudioContext();
  const testMessage = `Testing speech at ${speechRateValue.value.toFixed(1)} times speed.`;
  voiceService.speak(testMessage);
  console.log('[Settings] Testing speech rate:', speechRateValue.value);
};

onMounted(async () => {
  // Wait for the async Google availability check to complete
  await voiceService.waitForGoogleCheck();
  googleAvailable.value = voiceService.isGoogleAvailable();

  ttsEnabledState.value = ttsEnabled.value;
  speechRateValue.value = ttsRate.value;
  console.log('[Settings] TTS enabled:', ttsEnabledState.value);
  console.log('[Settings] TTS engine:', selectedTTSModel.value);
  console.log('[Settings] Speech rate:', speechRateValue.value);
  console.log('[Settings] STT engine:', selectedSTTModel.value);
  console.log('[Settings] Google available:', googleAvailable.value);

  // If Google is available, suggest using it
  if (googleAvailable.value && selectedTTSModel.value === 'browser') {
    console.log('[Settings] TIP: Google Cloud TTS is available and may work better than browser TTS.');
  }
});
</script>

<style scoped>
.settings-content {
  padding: 20px;
}

.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.settings-section {
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 24px;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
}

.settings-header {
  margin-bottom: 16px;
}

.section-title {
  font-size: var(--font-size-section-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin: 0 0 8px 0;
}

.section-description {
  font-size: var(--font-size-body);
  color: var(--color-text-muted);
  margin: 0;
}

.settings-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.option-card {
  border: 2px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg);
}

.option-card:hover {
  border-color: var(--color-primary);
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.1);
}

.option-card.active {
  border-color: var(--color-primary);
  background: #f0f7f2;
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.15);
}

.option-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.option-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.option-icon-voice {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  color: var(--color-primary);
}

.option-info {
  flex: 1;
}

.option-label {
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: 4px;
}

.option-subtitle {
  font-size: var(--font-size-small);
  color: var(--color-text-muted);
}

.option-check {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: 50%;
  color: white;
  flex-shrink: 0;
}

.option-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.option-card.disabled:hover {
  border-color: var(--color-border);
  background: var(--color-bg);
  transform: none;
  box-shadow: none;
}

.toggle-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.toggle-info {
  flex: 1;
}

.toggle-label {
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: 4px;
}

.toggle-description {
  font-size: var(--font-size-small);
  color: var(--color-text-muted);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 56px;
  height: 28px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 28px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--color-primary);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(28px);
}

.test-tts-btn {
  padding: 12px 24px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.test-tts-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.2);
}

.test-tts-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.page-title {
  font-size: var(--font-size-page-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.rate-control-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 16px 0;
}

.rate-slider-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rate-label {
  font-size: var(--font-size-body);
  color: var(--color-text);
  font-weight: var(--font-weight-medium);
}

.rate-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e0e0e0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.rate-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.rate-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 0 0 8px rgba(2, 74, 20, 0.1);
}

.rate-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.rate-slider::-moz-range-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 0 0 8px rgba(2, 74, 20, 0.1);
}

.rate-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rate-markers {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-small);
  color: var(--color-text-muted);
  padding: 0 4px;
}

.rate-presets {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 12px;
}

.preset-btn {
  padding: 10px 16px;
  background: var(--color-bg);
  border: 2px solid var(--color-border);
  border-radius: 8px;
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: #f5f5f5;
  transform: translateY(-2px);
}

.preset-btn.active {
  border-color: var(--color-primary);
  background: #f0f7f2;
  color: var(--color-primary);
}

.preset-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-rate-btn {
  padding: 12px 24px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  align-self: flex-start;
}

.test-rate-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.2);
}

.test-rate-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .settings-content {
    padding: 16px;
  }

  .settings-section {
    padding: 20px;
  }

  .settings-options {
    grid-template-columns: 1fr;
  }

  .rate-presets {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
