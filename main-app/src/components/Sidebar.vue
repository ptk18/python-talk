<template>
  <aside class="sidebar">
    <div class="sidebar-header" @click="goToHome">
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
import { useLanguage } from '../composables/useLanguage'
import { useAuth } from '../composables/useAuth'
import { useTranslations } from '../utils/translations'
import appIcon from '../assets/app-icon.svg'
import logoutIcon from '../assets/side-logout-icon.svg'

export default {
  name: 'Sidebar',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { language } = useLanguage()
    const { logout: authLogout } = useAuth()
    const userInfo = ref({})

    const t = computed(() => useTranslations(language.value))

    const navItems = computed(() => [])

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
      // Clear all auth-related data
      authLogout()
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('auth_user')
      localStorage.removeItem('auth_token')
      router.push('/login')
    }

    const goToProfile = () => {
      router.push('/profile')
    }

    const goToHome = () => {
      router.push('/')
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
      language,
      t,
      isActive,
      handleLogout,
      goToProfile,
      goToHome
    }
  }
}
</script>


