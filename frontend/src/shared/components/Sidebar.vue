<template>
  <aside class="sidebar sidebar-slim">
    <nav class="sidebar-nav">
      <!-- Navigation items -->
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

      <!-- New App button -->
      <button class="nav-item nav-item--button nav-item--primary" @click="handleNewApp">
        <svg class="nav-icon-svg new-app-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="3" ry="3" />
          <line x1="12" y1="8" x2="12" y2="16" />
          <line x1="8" y1="12" x2="16" y2="12" />
        </svg>
        <span class="nav-label">{{ t.home.newApp || 'New App' }}</span>
      </button>
    </nav>
    <div class="sidebar-footer">
      <div class="user-section" @click="goToProfile">
        <div class="user-avatar">{{ userInitial }}</div>
        <span class="nav-label">{{ userInfo.username || 'Profile' }}</span>
      </div>
      <button class="nav-item nav-item--button logout-btn" @click="handleLogout">
        <img :src="logoutIcon" alt="" class="nav-icon-svg" />
        <span class="nav-label">{{ t.sidebar.logout }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLanguage, useAuth } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import logoutIcon from '@/assets/side-logout-icon.svg'
import homeIcon from '@/assets/side-home-icon.svg'
import settingsIcon from '@/assets/side-setting-icon.svg'

export default {
  name: 'Sidebar',
  emits: ['new-app'],
  setup(props, { emit }) {
    const route = useRoute()
    const router = useRouter()
    const { language } = useLanguage()
    const { logout: authLogout } = useAuth()
    const userInfo = ref({})

    const t = computed(() => useTranslations(language.value))

    // Only Home and Settings
    const navItems = computed(() => [
      { id: 1, label: t.value.sidebar.home, iconSvg: homeIcon, path: '/' },
      { id: 4, label: t.value.sidebar.settings, iconSvg: settingsIcon, path: '/settings' }
    ])

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

    const isActive = (path) => {
      return route.path === path
    }

    const handleLogout = () => {
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

    const handleNewApp = () => {
      emit('new-app')
    }

    loadUserInfo()
    if (typeof window !== 'undefined') {
      window.addEventListener('userInfoUpdated', loadUserInfo)
    }

    return {
      logoutIcon,
      navItems,
      userInfo,
      userInitial,
      t,
      isActive,
      handleLogout,
      goToProfile,
      handleNewApp
    }
  }
}
</script>

<style scoped>
/* Slim sidebar with icons and labels */
.sidebar-slim {
  width: 80px !important;
  top: 48px;
  height: calc(100vh - 48px);
}

.sidebar-slim .sidebar-nav {
  padding: 8px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-slim .nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 4px;
  margin: 0 8px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 4px;
}

.sidebar-slim .nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.sidebar-slim .nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.sidebar-slim .nav-item--button {
  width: calc(100% - 16px);
}

.sidebar-slim .nav-item--primary {
  background: transparent;
}

.sidebar-slim .nav-item--primary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-slim .nav-icon-svg {
  width: 22px;
  height: 22px;
  object-fit: contain;
  margin: 0;
}

.sidebar-slim .nav-icon {
  font-size: 20px;
  line-height: 1;
}

.sidebar-slim .nav-label {
  font-size: 10px;
  text-align: center;
  line-height: 1.2;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-slim .new-app-icon {
  width: 22px;
  height: 22px;
  filter: none;
  opacity: 0.9;
}

.sidebar-slim .sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-slim .user-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255, 255, 255, 0.8);
}

.sidebar-slim .user-section:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.sidebar-slim .user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.sidebar-slim .logout-btn {
  margin: 0;
}

/* Filter for white icons */
.sidebar-slim .nav-icon-svg {
  filter: brightness(0) invert(1);
  opacity: 0.9;
}

.sidebar-slim .nav-item:hover .nav-icon-svg,
.sidebar-slim .nav-item.active .nav-icon-svg {
  opacity: 1;
}
</style>
