<template>
  <div class="app-container">
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
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import { useLanguage, useTTS, voiceService } from '@py-talk/shared';
import { useTranslations } from '../utils/translations';

const { language, setLanguage } = useLanguage();
const { ttsEnabled, ttsEngine, setTTSEnabled, setTTSEngine } = useTTS();

const t = computed(() => useTranslations(language.value));

const languages = computed(() => [
  { code: 'en', name: t.value.settings.english, nativeName: 'English', flag: '🇺🇸' },
  { code: 'th', name: t.value.settings.thai, nativeName: 'ไทย', flag: '🇹🇭' }
]);

const googleAvailable = ref(false);
const ttsEnabledState = ref(true);

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

const selectLanguage = (code) => {
  setLanguage(code);
};

const selectVoiceModel = (id) => {
  setTTSEngine(id);
  voiceService.setTTSEngine(id);
  console.log(`[Settings] TTS engine changed to: ${id}`);
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

onMounted(async () => {
  // Force check Google availability with delay
  await new Promise(resolve => setTimeout(resolve, 500));
  googleAvailable.value = voiceService.isGoogleAvailable();

  ttsEnabledState.value = ttsEnabled.value;
  console.log('[Settings] TTS enabled:', ttsEnabledState.value);
  console.log('[Settings] TTS engine:', selectedTTSModel.value);
  console.log('[Settings] Google TTS available:', googleAvailable.value);

  // If Google is available, suggest using it
  if (googleAvailable.value && selectedTTSModel.value === 'browser') {
    console.log('[Settings] TIP: Google Cloud TTS is available and may work better than browser TTS.');
  }
});
</script>

<style scoped>
.settings-content {
  padding: 32px;
}

.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.settings-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 32px;
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
}

.settings-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0 0 8px 0;
}

.section-description {
  font-size: 14px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.settings-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.option-card {
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.option-card:hover {
  border-color: #024A14;
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.1);
}

.option-card.active {
  border-color: #024A14;
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  color: #024A14;
}

.option-info {
  flex: 1;
}

.option-label {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 4px;
}

.option-subtitle {
  font-size: 13px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
}

.option-check {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #024A14;
  border-radius: 50%;
  color: white;
  flex-shrink: 0;
}

.option-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.option-card.disabled:hover {
  border-color: #e8e8e8;
  background: #fafafa;
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
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 4px;
}

.toggle-description {
  font-size: 13px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
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
  background-color: #024A14;
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(28px);
}

.test-tts-btn {
  padding: 12px 24px;
  background: #024A14;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.test-tts-btn:hover:not(:disabled) {
  background: #035A1A;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.2);
}

.test-tts-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
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

  .page-title {
    font-size: 22px;
  }
}
</style>
