<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <div class="content-area">
        <section class="featured-section">
          <div class="section-header">
            <h2 class="section-title">{{ t.home.featuredApps }}</h2>
            <div class="control-buttons">
              <button class="control-button" @click="toggleLanguage" :title="`Switch to ${language === 'en' ? 'Thai' : 'English'}`">
                <img :src="langIcon" alt="Language" class="control-icon" />
              </button>
              <button class="control-button" @click="toggleTTS" :title="ttsEnabled ? 'Disable Voice' : 'Enable Voice'">
                <img :src="ttsEnabled ? soundIcon : nosoundIcon" alt="Sound" class="control-icon" />
              </button>
            </div>
          </div>
          <div class="app-grid">
            <AppCard
              v-for="app in featuredApps"
              :key="app.id"
              :app="app"
              @click="handleAppClick(app)"
            />
          </div>
        </section>

        <section class="category-section" v-for="category in categories" :key="category.name">
          <h2 class="section-title">{{ category.name }}</h2>
          <div class="app-grid">
            <AppCard
              v-for="app in category.apps"
              :key="app.id"
              :app="app"
              @click="handleAppClick(app)"
            />
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage, useTTS, useAuth } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import Sidebar from '@/shared/components/Sidebar.vue'
import AppCard from './components/AppCard.vue'
import codeGeneratorIcon from '@/assets/F-code-generator.png'
import smartHomeIcon from '@/assets/F-smart-home.png'
import langIcon from '@/assets/lang-icon.svg'
import soundIcon from '@/assets/sound-icon.svg'
import nosoundIcon from '@/assets/nosound-icon.svg'

export default {
  name: 'Home',
  components: {
    Sidebar,
    AppCard
  },
  setup() {
    const router = useRouter()
    const { language, setLanguage } = useLanguage()
    const { ttsEnabled, setTTSEnabled } = useTTS()
    const t = computed(() => useTranslations(language.value))

    const handleAppClick = (app) => {
      if (app.route) {
        router.push(app.route)
      }
    }

    const featuredApps = computed(() => [
      {
        id: 1,
        name: 'Codespace',
        icon: codeGeneratorIcon,
        category: t.value.home.codeAssistant,
        rating: 4.5,
        route: '/conversation-manager',
        themeColor: '#024A14',
        themeColorDark: '#01350e'
      },
      {
        id: 2,
        name: t.value.home.turtlePlayground,
        icon: '🐢',
        category: t.value.home.learningTools,
        rating: 4.8,
        route: '/turtle-playground',
        themeColor: '#024A14',
        themeColorDark: '#01350e'
      },
      {
        id: 3,
        name: t.value.home.smartHome,
        icon: smartHomeIcon,
        category: t.value.home.connectToYourHome,
        rating: 4.7,
        themeColor: '#024A14',
        themeColorDark: '#01350e'
      }
    ])

    const toggleLanguage = () => {
      setLanguage(language.value === 'en' ? 'th' : 'en')
    }

    const toggleTTS = () => {
      setTTSEnabled(!ttsEnabled.value)
    }

    return {
      handleAppClick,
      featuredApps,
      t,
      language,
      ttsEnabled,
      langIcon,
      soundIcon,
      nosoundIcon,
      toggleLanguage,
      toggleTTS
    }
  },
  data() {
    return {
      searchQuery: '',
      categories: []
    }
  }
}
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.control-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-button {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
}

.control-button:hover {
  background: transparent;
  transform: translateY(-1px);
  opacity: 0.7;
}

.control-button:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.control-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

@media (max-width: 768px) {
  .section-title {
    font-size: 22px;
  }
  
  .control-button {
    width: 36px;
    height: 36px;
  }
  
  .control-icon {
    width: 18px;
    height: 18px;
  }
}
</style>
