<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <div class="content-area">
        <section class="featured-section">
          <h2 class="section-title">{{ t.home.featuredApps }}</h2>
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
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage } from '../composables/useLanguage'
import { useTranslations } from '../utils/translations'
import { useAuth } from '../composables/useAuth'
import Sidebar from '../components/Sidebar.vue'
import AppCard from '../components/AppCard.vue'
import codeGeneratorIcon from '../assets/F-code-generator.png'
import smartHomeIcon from '../assets/F-smart-home.png'

export default {
  name: 'Home',
  components: {
    Sidebar,
    AppCard
  },
  setup() {
    const router = useRouter()
    const { language } = useLanguage()
    const { user } = useAuth()
    const t = computed(() => useTranslations(language.value))

    onMounted(() => {
      if (!user.value) {
        router.push('/login')
      }
    })

    const handleAppClick = (app) => {
      if (app.route) {
        router.push(app.route)
      } else if (app.url) {
        window.open(app.url, '_blank')
      }
    }

    const featuredApps = computed(() => [
      {
        id: 1,
        name: t.value.home.pytalkWorkspace,
        icon: codeGeneratorIcon,
        category: t.value.home.codeAssistant,
        rating: 4.5,
        route: '/conversation-manager'
      },
      {
        id: 2,
        name: t.value.home.turtlePlayground,
        icon: '🐢',
        category: t.value.home.learningTools,
        rating: 4.8,
        route: '/turtle-playground'
      },
      {
        id: 3,
        name: t.value.home.smartHome,
        icon: smartHomeIcon,
        category: t.value.home.connectToYourHome,
        rating: 4.7
      },
      {
        id: 4,
        name: t.value.home.reflexTest,
        icon: '💬',
        category: t.value.home.entertainment,
        rating: 4.6,
        url: 'http://localhost:3010/'
      }
    ])

    return {
      handleAppClick,
      featuredApps,
      t
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
.section-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .section-title {
    font-size: 22px;
  }
}
</style>
