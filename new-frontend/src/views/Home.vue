<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <div class="content-area">
        <section class="featured-section">
          <h2 class="section-title">Featured Apps</h2>
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
import { useRouter } from 'vue-router'
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

    const handleAppClick = (app) => {
      if (app.route) {
        router.push(app.route)
      } else if (app.url) {
        window.open(app.url, '_blank')
      }
    }

    return {
      handleAppClick
    }
  },
  data() {
    return {
      searchQuery: '',
      featuredApps: [
        {
          id: 1,
          name: 'PyTalk Workspace',
          icon: codeGeneratorIcon,
          category: 'Code Assistant',
          rating: 4.5,
          route: '/conversation-manager'
        },
        {
          id: 2,
          name: 'Smart Home',
          icon: smartHomeIcon,
          category: 'Connect to your home',
          rating: 4.7
        },
        {
          id: 3,
          name: 'ReflexTest',
          icon: '💬',
          category: 'Entertainment',
          rating: 4.6,
          url: 'http://localhost:3010/'
        }
      ],
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
