<template>
  <aside class="sidebar">
    <div class="sidebar-header" @click="goToMainApp">
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLanguage, useAuth } from '@py-talk/shared'
import { useTranslations } from '../utils/translations'
import appIcon from '../assets/app-icon.svg'
import turtleIcon from '../assets/side-turtle-icon.svg'
import logoutIcon from '../assets/side-logout-icon.svg'

export default {
  name: 'Sidebar',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { language } = useLanguage()
    const { user, logout: authLogout } = useAuth()
    const userInfo = ref({})

    const t = computed(() => useTranslations(language.value))

    const navItems = computed(() => [
      { id: 2, label: t.value.sidebar.turtle, iconSvg: turtleIcon, path: '/turtle-playground' }
    ])

    const userInitial = computed(() => {
      const source = userInfo.value.username || userInfo.value.email || 'U'
      return source.charAt(0).toUpperCase()
    })

    const loadUserInfo = () => {
      // First check the reactive user from useAuth
      if (user.value) {
        userInfo.value = user.value
        return
      }
      // Try to get user info from localStorage as fallback
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

    // Watch for changes in the auth user
    watch(user, (newUser) => {
      if (newUser) {
        userInfo.value = newUser
      }
    }, { immediate: true })

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

    const goToMainApp = () => {
      // Navigate to main app (port 3001)
      const hostname = window.location.hostname
      window.location.href = `${window.location.protocol}//${hostname}:3001`
    }

    onMounted(() => {
      loadUserInfo()
    })

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
      goToMainApp
    }
  }
}
</script>

