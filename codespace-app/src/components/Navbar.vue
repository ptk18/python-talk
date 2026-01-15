<template>
  <div>
    <header :class="['navbar', { 'navbar--sidebar-open': isSidebarOpen }]">
      <button
        class="navbar__menu-btn"
        @click="toggleSidebar"
        aria-label="Toggle menu"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </button>

      <router-link to="/" class="navbar__logo">PyTalk</router-link>
      <nav class="navbar__links">
        <router-link
          to="/"
          :class="{ 'is-active': $route.path === '/' }"
          @click="closeSidebar"
        >
          {{ t.navbar.home }}
        </router-link>
        <router-link
          to="/settings"
          :class="{ 'is-active': $route.path === '/settings' }"
          @click="closeSidebar"
        >
          {{ t.navbar.settings }}
        </router-link>
        <router-link
          to="/profile"
          :class="{ 'is-active': $route.path === '/profile' }"
          @click="closeSidebar"
        >
          {{ t.navbar.profile }}
        </router-link>
        <button
          class="navbar__lang-toggle"
          @click="toggleLanguage"
          :title="`Switch to ${language === 'en' ? 'Thai' : 'English'}`"
        >
          {{ language === 'en' ? 'EN' : 'TH' }}
        </button>
        <button
          class="navbar__tts-toggle"
          @click="toggleTTS"
          :title="ttsEnabled ? 'Disable Voice' : 'Enable Voice'"
        >
          <svg v-if="ttsEnabled" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="23" y1="9" x2="17" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="17" y1="9" x2="23" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </nav>
      <div v-if="rightButton" class="navbar__button">
        <router-link v-if="rightButton.to" :to="rightButton.to" class="navbar__button-link">
          {{ rightButton.text }}
        </router-link>
        <button v-else class="navbar__button-btn" @click="rightButton.onClick">
          {{ rightButton.text }}
        </button>
      </div>
    </header>

    <div v-if="isSidebarOpen" class="navbar__overlay" @click="closeSidebar"></div>

    <aside :class="['navbar__sidebar', { 'navbar__sidebar--open': isSidebarOpen }]">
      <div class="navbar__sidebar-header">
        <router-link to="/" class="navbar__sidebar-logo" @click="closeSidebar">PyTalk</router-link>
      </div>
      <nav class="navbar__sidebar-links">
        <router-link
          to="/"
          :class="{ 'is-active': $route.path === '/' }"
          @click="closeSidebar"
        >
          {{ t.navbar.home }}
        </router-link>
        <router-link
          to="/settings"
          :class="{ 'is-active': $route.path === '/settings' }"
          @click="closeSidebar"
        >
          {{ t.navbar.settings }}
        </router-link>
        <router-link
          to="/profile"
          :class="{ 'is-active': $route.path === '/profile' }"
          @click="closeSidebar"
        >
          {{ t.navbar.profile }}
        </router-link>
        <button
          class="navbar__lang-toggle navbar__lang-toggle--sidebar"
          @click="toggleLanguage"
          :title="`Switch to ${language === 'en' ? 'Thai' : 'English'}`"
        >
          <span>{{ language === 'en' ? 'English' : 'ไทย' }}</span>
        </button>
        <button
          class="navbar__tts-toggle navbar__tts-toggle--sidebar"
          @click="toggleTTS"
          :title="ttsEnabled ? 'Disable Voice' : 'Enable Voice'"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path v-if="ttsEnabled" d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path v-if="ttsEnabled" d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path v-if="ttsEnabled" d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path v-if="!ttsEnabled" d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line v-if="!ttsEnabled" x1="23" y1="9" x2="17" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line v-if="!ttsEnabled" x1="17" y1="9" x2="23" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>{{ ttsEnabled ? t.sidebar.voiceOn : t.sidebar.voiceOff }}</span>
        </button>
      </nav>
      <div v-if="rightButton" class="navbar__sidebar-button">
        <router-link v-if="rightButton.to" :to="rightButton.to" class="navbar__button-link" @click="closeSidebar">
          {{ rightButton.text }}
        </router-link>
        <button v-else class="navbar__button-btn" @click="handleRightButtonClick">
          {{ rightButton.text }}
        </button>
      </div>
    </aside>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTTS } from '../composables/useTTS';
import { useLanguage } from '../composables/useLanguage';
import { useTranslations } from '../utils/translations';

export default {
  name: 'Navbar',
  props: {
    rightButton: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const route = useRoute();
    const isSidebarOpen = ref(false);
    const { ttsEnabled, setTTSEnabled } = useTTS();
    const { language, setLanguage } = useLanguage();

    const t = computed(() => useTranslations(language.value));

    const toggleSidebar = () => {
      isSidebarOpen.value = !isSidebarOpen.value;
    };

    const closeSidebar = () => {
      isSidebarOpen.value = false;
    };

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value);
    };

    const toggleLanguage = () => {
      setLanguage(language.value === 'en' ? 'th' : 'en');
    };

    const handleRightButtonClick = () => {
      if (props.rightButton?.onClick) {
        props.rightButton.onClick();
      }
      closeSidebar();
    };

    return {
      route,
      isSidebarOpen,
      ttsEnabled,
      language,
      t,
      toggleSidebar,
      closeSidebar,
      toggleTTS,
      toggleLanguage,
      handleRightButtonClick,
    };
  }
};
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background-color: var(--navbar-bg, #001f3f);
  color: white;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar__menu-btn {
  display: none;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0.5rem;
}

.navbar__logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
  font-family: 'Jaldi', sans-serif;
}

.navbar__links {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.navbar__links a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.navbar__links a:hover,
.navbar__links a.is-active {
  opacity: 0.8;
  text-decoration: underline;
}

.navbar__lang-toggle,
.navbar__tts-toggle {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.navbar__lang-toggle:hover,
.navbar__tts-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.navbar__button-link,
.navbar__button-btn {
  background: white;
  color: #001f3f;
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.navbar__button-link:hover,
.navbar__button-btn:hover {
  background: #f0f0f0;
}

.navbar__overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 98;
}

.navbar__sidebar {
  position: fixed;
  top: 0;
  left: -300px;
  width: 300px;
  height: 100%;
  background: var(--navbar-bg, #001f3f);
  color: white;
  transition: left 0.3s;
  z-index: 99;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.navbar__sidebar--open {
  left: 0;
}

.navbar__sidebar-header {
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.navbar__sidebar-logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.navbar__sidebar-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.navbar__sidebar-links a,
.navbar__sidebar-links button {
  color: white;
  text-decoration: none;
  padding: 0.75rem;
  border-radius: 4px;
  transition: background 0.2s;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.navbar__sidebar-links a:hover,
.navbar__sidebar-links a.is-active,
.navbar__sidebar-links button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.navbar__lang-toggle--sidebar,
.navbar__tts-toggle--sidebar {
  justify-content: flex-start;
}

@media (max-width: 768px) {
  .navbar__menu-btn {
    display: block;
  }

  .navbar__links {
    display: none;
  }

  .navbar__button {
    display: none;
  }
}
</style>
