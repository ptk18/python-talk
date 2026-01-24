<template>
  <header class="top-toolbar">
    <div class="toolbar-left">
      <img :src="appIcon" alt="PyTalk" class="toolbar-logo" @click="goToHome" />
      <span class="toolbar-title">PyTalk</span>
    </div>
    <div class="toolbar-right">
      <!-- Language Dropdown -->
      <div class="toolbar-dropdown" ref="langDropdownRef">
        <button class="toolbar-icon-btn" @click="toggleLangDropdown" title="Language">
          <img :src="langIcon" alt="Language" class="toolbar-icon" />
        </button>
        <div v-if="showLangDropdown" class="toolbar-dropdown-menu">
          <button
            class="toolbar-dropdown-item"
            @click="selectLanguage('en')"
          >
            <svg v-if="language === 'en'" class="tick-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span :class="{ 'has-tick': language === 'en' }">English</span>
          </button>
          <button
            class="toolbar-dropdown-item"
            @click="selectLanguage('th')"
          >
            <svg v-if="language === 'th'" class="tick-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span :class="{ 'has-tick': language === 'th' }">ไทย (Thai)</span>
          </button>
        </div>
      </div>

      <!-- Sound Toggle -->
      <button class="toolbar-icon-btn" @click="toggleTTS" :title="ttsEnabled ? 'Sound On' : 'Sound Off'">
        <img :src="ttsEnabled ? soundIcon : nosoundIcon" alt="Sound" class="toolbar-icon" />
      </button>

      <div class="user-avatar" @click="goToProfile">{{ userInitial }}</div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage, useTTS } from '@py-talk/shared'
import appIcon from '@/assets/app-icon.svg'
import langIcon from '@/assets/lang-icon.svg'
import soundIcon from '@/assets/sound-icon.svg'
import nosoundIcon from '@/assets/nosound-icon.svg'

export default {
  name: 'TopToolbar',
  setup() {
    const router = useRouter()
    const userInfo = ref({})
    const { language, setLanguage } = useLanguage()
    const { ttsEnabled, setTTSEnabled } = useTTS()

    const showLangDropdown = ref(false)
    const langDropdownRef = ref(null)

    const userInitial = computed(() => {
      const source = userInfo.value.username || userInfo.value.email || 'U'
      return source.charAt(0).toUpperCase()
    })

    const loadUserInfo = () => {
      const stored = localStorage.getItem('auth_user')
      if (stored) {
        userInfo.value = JSON.parse(stored)
      } else {
        const oldStored = localStorage.getItem('userInfo')
        if (oldStored) {
          userInfo.value = JSON.parse(oldStored)
        }
      }
    }

    const goToHome = () => {
      router.push('/')
    }

    const goToProfile = () => {
      router.push('/profile')
    }

    const toggleLangDropdown = () => {
      showLangDropdown.value = !showLangDropdown.value
    }

    const selectLanguage = (lang) => {
      setLanguage(lang)
      showLangDropdown.value = false
    }

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value)
    }

    const handleClickOutside = (event) => {
      if (langDropdownRef.value && !langDropdownRef.value.contains(event.target)) {
        showLangDropdown.value = false
      }
    }

    loadUserInfo()

    onMounted(() => {
      if (typeof window !== 'undefined') {
        window.addEventListener('userInfoUpdated', loadUserInfo)
        document.addEventListener('click', handleClickOutside)
      }
    })

    onUnmounted(() => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('userInfoUpdated', loadUserInfo)
        document.removeEventListener('click', handleClickOutside)
      }
    })

    return {
      appIcon,
      langIcon,
      soundIcon,
      nosoundIcon,
      userInitial,
      language,
      ttsEnabled,
      showLangDropdown,
      langDropdownRef,
      goToHome,
      goToProfile,
      toggleLangDropdown,
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
  height: 48px;
  background: linear-gradient(180deg, #024A14 0%, #01350e 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 150;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
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
  font-size: 18px;
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

/* Dropdown Styles */
.toolbar-dropdown {
  position: relative;
}

.toolbar-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 140px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 200;
  animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.toolbar-dropdown-item {
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  color: #333;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-dropdown-item:hover {
  background: #f5f5f5;
}

.tick-icon {
  width: 16px;
  height: 16px;
  color: #024A14;
  flex-shrink: 0;
}

.toolbar-dropdown-item span.has-tick {
  margin-left: 0;
}

.toolbar-dropdown-item span:not(.has-tick) {
  margin-left: 24px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.user-avatar:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
