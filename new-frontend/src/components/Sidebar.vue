<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <img :src="appIcon" alt="PyTalk" class="app-icon-img" />
      <h1 class="store-logo">PyTalk</h1>
    </div>
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in navItems" 
        :key="item.id"
        :to="item.path"
        :class="['nav-item', { active: isActive(item.path) }]"
      >
        <img v-if="item.iconSvg" :src="item.iconSvg" alt="" class="nav-icon-svg" />
        <span v-else class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
      <button class="nav-item nav-item--control" @click="toggleLanguage" :title="`Switch to ${language === 'en' ? 'Thai' : 'English'}`">
        <span class="nav-icon">🌐</span>
        <span class="nav-label">{{ language === 'en' ? 'English' : 'ไทย' }}</span>
      </button>
      <button class="nav-item nav-item--control" @click="toggleTTS" :title="ttsEnabled ? 'Disable Voice' : 'Enable Voice'">
        <span class="nav-icon">{{ ttsEnabled ? '🔊' : '🔇' }}</span>
        <span class="nav-label">{{ ttsEnabled ? t.sidebar.voiceOn : t.sidebar.voiceOff }}</span>
      </button>
    </nav>
    <div class="sidebar-footer">
      <div class="user-section" @click="goToProfile">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info">
          <div class="user-name">{{ userInfo.username || 'User' }}</div>
          <div class="user-email">{{ userInfo.email || 'user@example.com' }}</div>
        </div>
      </div>
      <button class="logout-button" @click="handleLogout">
        <img :src="logoutIcon" alt="" class="logout-icon" />
        <span class="logout-label">{{ t.sidebar.logout }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTTS } from '../composables/useTTS'
import { useLanguage } from '../composables/useLanguage'
import { useTranslations } from '../utils/translations'
import appIcon from '../assets/app-icon.svg'
import homeIcon from '../assets/side-home-icon.svg'
import historyIcon from '../assets/side-history-icon.svg'
import runIcon from '../assets/side-run-icon.svg'
import logoutIcon from '../assets/side-logout-icon.svg'
import settingsIcon from '../assets/side-setting-icon.svg'

export default {
  name: 'Sidebar',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { ttsEnabled, setTTSEnabled } = useTTS()
    const { language, setLanguage } = useLanguage()
    const userInfo = ref({})

    const t = computed(() => useTranslations(language.value))

    const navItems = computed(() => [
      { id: 1, label: t.value.sidebar.home, iconSvg: homeIcon, path: '/' },
      { id: 2, label: t.value.sidebar.codeSpace, iconSvg: runIcon, path: '/conversation-manager' },
      { id: 3, label: t.value.sidebar.history, iconSvg: historyIcon, path: '/history' },
      { id: 4, label: t.value.sidebar.settings, iconSvg: settingsIcon, path: '/settings' }
    ])

    const userInitial = computed(() => {
      const source = userInfo.value.username || userInfo.value.email || 'U'
      return source.charAt(0).toUpperCase()
    })

    const loadUserInfo = () => {
      // Try to get user info from auth store first
      const stored = localStorage.getItem('auth_user')
      if (stored) {
        userInfo.value = JSON.parse(stored)
      } else {
        // Fallback to old userInfo key
        const oldStored = localStorage.getItem('userInfo')
        if (oldStored) {
          userInfo.value = JSON.parse(oldStored)
        }
      }
    }

    const isActive = (path) => {
      return route.path === path
    }

    const handleLogout = () => {
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('userInfo')
      router.push('/login')
    }

    const goToProfile = () => {
      router.push('/profile')
    }

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value)
    }

    const toggleLanguage = () => {
      setLanguage(language.value === 'en' ? 'th' : 'en')
    }

    loadUserInfo()
    if (typeof window !== 'undefined') {
      window.addEventListener('userInfoUpdated', loadUserInfo)
    }

    return {
      appIcon,
      logoutIcon,
      navItems,
      userInfo,
      userInitial,
      ttsEnabled,
      language,
      t,
      isActive,
      handleLogout,
      goToProfile,
      toggleTTS,
      toggleLanguage
    }
  }
}
</script>

