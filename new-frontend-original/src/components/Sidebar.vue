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
    </nav>
    <div class="sidebar-footer">
      <div class="user-section" @click="goToProfile">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info">
          <div class="user-name">{{ userInfo.name || 'User' }}</div>
          <div class="user-email">{{ userInfo.email || 'user@example.com' }}</div>
        </div>
      </div>
      <button class="logout-button" @click="handleLogout">
        <img :src="logoutIcon" alt="" class="logout-icon" />
        <span class="logout-label">Logout</span>
      </button>
    </div>
  </aside>
</template>

<script>
import appIcon from '../assets/app-icon.svg'
import homeIcon from '../assets/side-home-icon.svg'
import historyIcon from '../assets/side-history-icon.svg'
import runIcon from '../assets/side-run-icon.svg'
import logoutIcon from '../assets/side-logout-icon.svg'
import settingsIcon from '../assets/side-setting-icon.svg'

export default {
  name: 'Sidebar',
  data() {
    return {
      appIcon: appIcon,
      logoutIcon: logoutIcon,
      navItems: [
        { id: 1, label: 'Home', iconSvg: homeIcon, path: '/' },
        { id: 2, label: 'Code Space', iconSvg: runIcon, path: '/run' },
        { id: 3, label: 'History', iconSvg: historyIcon, path: '/history' },
        { id: 4, label: 'Settings', iconSvg: settingsIcon, path: '/settings' }
      ],
      userInfo: {}
    }
  },
  mounted() {
    this.loadUserInfo()
    window.addEventListener('userInfoUpdated', this.loadUserInfo)
  },
  beforeUnmount() {
    window.removeEventListener('userInfoUpdated', this.loadUserInfo)
  },
  computed: {
    userInitial() {
      const source = this.userInfo.name || this.userInfo.email || 'U'
      return source.charAt(0).toUpperCase()
    }
  },
  methods: {
    isActive(path) {
      return this.$route.path === path
    },
    loadUserInfo() {
      const stored = localStorage.getItem('userInfo')
      if (stored) {
        this.userInfo = JSON.parse(stored)
      }
    },
    handleLogout() {
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('userInfo')
      this.$router.push('/login')
    },
    goToProfile() {
      this.$router.push('/profile')
    }
  }
}
</script>

