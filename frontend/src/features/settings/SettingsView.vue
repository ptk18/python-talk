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
          <div class="settings-section">
            <!-- Language -->
            <div class="setting-row">
              <span class="setting-label">{{ t.settings.languageSelection }}</span>
              <select class="setting-select" :value="selectedLanguage" @change="selectLanguage($event.target.value)">
                <option value="en">English</option>
                <option value="th">ไทย (Thai)</option>
              </select>
            </div>

            <div class="setting-divider"></div>

            <!-- Speech-to-Text Model -->
            <div class="setting-row">
              <span class="setting-label">{{ t.settings.speechToText }}</span>
              <select class="setting-select" :value="selectedSTTModel" @change="selectSTTModel($event.target.value)">
                <option v-for="stt in sttModels" :key="stt.id" :value="stt.id" :disabled="stt.disabled">
                  {{ stt.name }}
                </option>
              </select>
            </div>

            <div class="setting-divider"></div>

            <!-- Text-to-Speech Model -->
            <div class="setting-row">
              <span class="setting-label">{{ t.settings.ttsModel }}</span>
              <select class="setting-select" :value="selectedTTSModel" @change="selectVoiceModel($event.target.value)">
                <option v-for="voice in ttsModels" :key="voice.id" :value="voice.id">
                  {{ voice.name }}
                </option>
              </select>
            </div>

            <div class="setting-divider"></div>

            <!-- Enable Voice -->
            <div class="setting-row">
              <span class="setting-label">{{ t.settings.enableTTS }}</span>
              <label class="toggle-switch">
                <input type="checkbox" v-model="ttsEnabledState" @change="toggleTTS">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-divider"></div>

            <!-- Speech Rate -->
            <div class="setting-row">
              <span class="setting-label">{{ t.settings.speechRate }}</span>
              <div class="rate-control">
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
                <span class="rate-value">{{ speechRateLabel }}</span>
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

const googleAvailable = ref(voiceService.isGoogleAvailable());
const ttsEnabledState = ref(true);
const speechRateValue = ref(1.0);

const ttsModels = computed(() => {
  const models = [];

  if (googleAvailable.value) {
    models.push({
      id: 'google',
      name: t.value.settings.googleTTS
    });
  }

  models.push({
    id: 'browser',
    name: t.value.settings.browserTTS
  });

  return models;
});

const selectedLanguage = computed(() => language.value);
const selectedTTSModel = computed(() => ttsEngine.value);
const selectedSTTModel = computed(() => sttEngine.value);

const sttModels = computed(() => {
  const models = [];

  models.push({
    id: 'google',
    name: t.value.settings.googleSTT,
    disabled: !googleAvailable.value
  });

  models.push({
    id: 'whisper',
    name: t.value.settings.whisperSTT,
    disabled: false
  });

  return models;
});

const selectLanguage = (code) => {
  setLanguage(code);
};

const selectVoiceModel = (id) => {
  setTTSEngine(id);
  voiceService.setTTSEngine(id);
};

const selectSTTModel = (id) => {
  setSTTEngine(id);
  voiceService.setEngine(id);
};

const toggleTTS = () => {
  setTTSEnabled(ttsEnabledState.value);
};

const speechRateLabel = computed(() => {
  return `${speechRateValue.value.toFixed(1)}x`;
});

const onSpeechRateChange = (rate) => {
  speechRateValue.value = rate;
  setTTSRate(rate);
  voiceService.setSpeechRate(rate);
};

onMounted(async () => {
  await voiceService.waitForGoogleCheck();
  googleAvailable.value = voiceService.isGoogleAvailable();

  ttsEnabledState.value = ttsEnabled.value;
  speechRateValue.value = ttsRate.value;
});
</script>

<style scoped>
.settings-content {
  padding: 20px;
}

.settings-container {
  max-width: 600px;
  margin: 0 auto;
}

.settings-section {
  padding: 0;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
}

.setting-label {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  flex-shrink: 0;
  margin-right: 24px;
}

.setting-divider {
  height: 1px;
  background: #e8e8e8;
}

/* Dropdown */
.setting-select {
  padding: 8px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  background: white;
  font-size: 16px;
  color: var(--color-text);
  cursor: pointer;
  min-width: 200px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%23999' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
}

.setting-select:focus {
  border-color: var(--color-primary);
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
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
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--color-primary);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

/* Rate Slider */
.rate-control {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
}

.rate-slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: #e0e0e0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.rate-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.rate-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: none;
}

.rate-slider:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.rate-value {
  font-size: 16px;
  color: var(--color-text-muted);
  min-width: 36px;
  text-align: right;
}

.page-title {
  font-size: var(--font-size-page-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

/* Tablet */
@media (max-width: 1024px) {
  .settings-container {
    max-width: 500px;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }

  .settings-content {
    padding: 16px;
  }

  .setting-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 14px 0;
  }

  .setting-label {
    font-size: 16px;
    margin-right: 0;
  }

  .setting-select {
    width: 100%;
    min-width: unset;
  }

  .rate-control {
    width: 100%;
    min-width: unset;
  }

  .page-title {
    font-size: 20px;
  }

  .top-header {
    padding: 12px 16px;
  }
}

/* Small mobile */
@media (max-width: 480px) {
  .settings-content {
    padding: 12px;
  }

  .setting-label {
    font-size: 15px;
  }

  .setting-select {
    font-size: 14px;
    padding: 10px 14px;
  }
}
</style>
