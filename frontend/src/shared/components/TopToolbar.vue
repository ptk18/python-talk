<template>
  <header class="top-toolbar">
    <div class="toolbar-left">
      <img :src="appIcon" alt="AgentTalk" class="toolbar-logo" @click="goToHome" />
      <span class="toolbar-title">AgentTalk</span>
    </div>
    <div class="toolbar-right">
      <!-- Language Switcher -->
      <div class="lang-switcher" ref="langSwitcher">
        <button class="lang-active-btn" @click="toggleDropdown">
          <span class="lang-label">{{ language === 'en' ? 'ENG' : 'THAI' }}</span>
        </button>
        <div v-if="dropdownOpen" class="lang-dropdown">
          <button
            class="lang-option"
            :class="{ selected: language === 'en' }"
            @click="selectLanguage('en')"
          >
            <span class="lang-option-code">ENG</span>
            <span class="lang-option-name">English</span>
          </button>
          <button
            class="lang-option"
            :class="{ selected: language === 'th' }"
            @click="selectLanguage('th')"
          >
            <span class="lang-option-code">THAI</span>
            <span class="lang-option-name">ไทย</span>
          </button>
        </div>
      </div>

      <!-- Sound Toggle -->
      <button class="toolbar-icon-btn" @click="toggleTTS" :title="ttsEnabled ? 'Sound On' : 'Sound Off'">
        <img :src="ttsEnabled ? soundIcon : nosoundIcon" alt="Sound" class="toolbar-icon" />
      </button>
    </div>
  </header>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
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
    const dropdownOpen = ref(false)
    const langSwitcher = ref(null)

    const goToHome = () => {
      router.push('/')
    }

    const toggleDropdown = () => {
      dropdownOpen.value = !dropdownOpen.value
    }

    const selectLanguage = (lang) => {
      setLanguage(lang)
      dropdownOpen.value = false
    }

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value)
    }

    const handleClickOutside = (e) => {
      if (langSwitcher.value && !langSwitcher.value.contains(e.target)) {
        dropdownOpen.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    return {
      appIcon,
      soundIcon,
      nosoundIcon,
      language,
      ttsEnabled,
      dropdownOpen,
      langSwitcher,
      goToHome,
      toggleDropdown,
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

/* Language Switcher */
.lang-switcher {
  position: relative;
}

.lang-active-btn {
  height: 34px;
  padding: 0 10px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: background 0.2s ease;
  display: flex;
  align-items: center;
}

.lang-active-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.lang-label {
  line-height: 1;
}

.lang-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  min-width: 160px;
  z-index: 100;
}

.lang-option {
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.15s ease;
}

.lang-option:hover {
  background: #f0f0f0;
}

.lang-option.selected {
  background: #e8f0fe;
}

.lang-option-code {
  font-size: 13px;
  font-weight: 700;
  color: #333;
  min-width: 38px;
}

.lang-option-name {
  font-size: 13px;
  color: #555;
}
</style>
