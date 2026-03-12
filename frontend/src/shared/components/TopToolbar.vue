<template>
  <header class="top-toolbar">
    <div class="toolbar-left">
      <img :src="appIcon" alt="AgentTalk" class="toolbar-logo" @click="goToHome" />
      <span class="toolbar-title">AgentTalk</span>
    </div>
    <div class="toolbar-right">
      <!-- Language Flags -->
      <div class="lang-flags">
        <button
          class="flag-btn"
          :class="{ active: language === 'en' }"
          @click="selectLanguage('en')"
          title="English"
        >
          <span class="flag-emoji">🇺🇸</span>
        </button>
        <button
          class="flag-btn"
          :class="{ active: language === 'th' }"
          @click="selectLanguage('th')"
          title="ไทย"
        >
          <span class="flag-emoji">🇹🇭</span>
        </button>
      </div>

      <!-- Sound Toggle -->
      <button class="toolbar-icon-btn" @click="toggleTTS" :title="ttsEnabled ? 'Sound On' : 'Sound Off'">
        <img :src="ttsEnabled ? soundIcon : nosoundIcon" alt="Sound" class="toolbar-icon" />
      </button>
    </div>
  </header>
</template>

<script>
import { useRouter } from 'vue-router'
import { useLanguage, useTTS } from '@py-talk/shared'
import appIcon from '@/assets/app-icon.svg'
import soundIcon from '@/assets/sound-icon.svg'
import nosoundIcon from '@/assets/nosound-icon.svg'

export default {
  name: 'TopToolbar',
  setup() {
    const router = useRouter()
    const { language, setLanguage } = useLanguage()
    const { ttsEnabled, setTTSEnabled } = useTTS()

    const goToHome = () => {
      router.push('/')
    }

    const selectLanguage = (lang) => {
      setLanguage(lang)
    }

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value)
    }

    return {
      appIcon,
      soundIcon,
      nosoundIcon,
      language,
      ttsEnabled,
      goToHome,
      selectLanguage,
      toggleTTS
    }
  }
}
</script>

<style scoped>
.top-toolbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--toolbar-height);
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: var(--z-toolbar);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 6px;
}

.toolbar-logo {
  width: 32px;
  height: 32px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.toolbar-logo:hover {
  transform: scale(1.05);
}

.toolbar-title {
  color: white;
  font-size: 20px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Icon Button Styles */
.toolbar-icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
}

.toolbar-icon-btn:hover {
  opacity: 0.7;
}

.toolbar-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

/* Language Flags */
.lang-flags {
  display: flex;
  align-items: center;
  gap: 2px;
}

.flag-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 6px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  opacity: 0.45;
}

.flag-btn.active {
  opacity: 1;
}

.flag-btn:hover {
  opacity: 0.85;
}

.flag-btn.active:hover {
  opacity: 1;
}

.flag-emoji {
  font-size: 22px;
  line-height: 1;
}
</style>
