<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar @new-app="showNewAppDialog = true" />
    <main class="main-content">
      <div class="content-area">
        <!-- Favourites Section (only show if user has favorites) -->
        <section v-if="favoriteApps.length > 0" class="favorites-section">
          <div class="section-header">
            <h2 class="section-title favorites-title">{{ t.home.favourites || 'Favourites' }}</h2>
          </div>
          <div class="app-grid">
            <AppCard
              v-for="app in favoriteApps"
              :key="'fav-' + app.id"
              :app="app"
              :is-favorited="true"
              @click="handleAppClick(app)"
              @edit="handleEditApp"
              @delete="handleDeleteApp"
              @toggle-favorite="handleToggleFavorite"
            />
          </div>
        </section>

        <!-- Featured Apps Section -->
        <section class="featured-section">
          <div class="section-header">
            <h2 class="section-title">{{ t.home.featuredApps }}</h2>
          </div>
          <div class="app-grid">
            <AppCard
              v-for="app in allFeaturedApps"
              :key="app.id"
              :app="app"
              :is-favorited="isAppFavorited(app)"
              @click="handleAppClick(app)"
              @edit="handleEditApp"
              @delete="handleDeleteApp"
              @toggle-favorite="handleToggleFavorite"
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

    <!-- New App Dialog -->
    <NewAppDialog
      :visible="showNewAppDialog"
      @close="showNewAppDialog = false"
      @create="handleCreateApp"
    />

    <!-- Edit App Dialog -->
    <EditAppDialog
      :visible="showEditDialog"
      :app="selectedApp"
      @close="showEditDialog = false"
      @save="handleSaveEdit"
    />

    <!-- Delete Confirm Dialog -->
    <DeleteConfirmDialog
      :visible="showDeleteDialog"
      :app-name="selectedApp?.name"
      :app-id="selectedApp?.appId"
      @close="showDeleteDialog = false"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage, useAuth, conversationAPI, favoritesAPI, voiceService } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import { getGreeting } from '@/shared/utils/formatters'
import TopToolbar from '@/shared/components/TopToolbar.vue'
import Sidebar from '@/shared/components/Sidebar.vue'
import AppCard from './components/AppCard.vue'
import NewAppDialog from './components/NewAppDialog.vue'
import EditAppDialog from './components/EditAppDialog.vue'
import DeleteConfirmDialog from './components/DeleteConfirmDialog.vue'

export default {
  name: 'Home',
  components: {
    TopToolbar,
    Sidebar,
    AppCard,
    NewAppDialog,
    EditAppDialog,
    DeleteConfirmDialog
  },
  setup() {
    const router = useRouter()
    const { language } = useLanguage()
    const { user } = useAuth()
    const t = computed(() => useTranslations(language.value))

    const showNewAppDialog = ref(false)
    const showEditDialog = ref(false)
    const showDeleteDialog = ref(false)
    const selectedApp = ref(null)
    const userApps = ref([])
    const userFavorites = ref([])
    const hasGreeted = ref(false)

    const greetUser = () => {
      if (!hasGreeted.value) {
        hasGreeted.value = true
        voiceService.speak(getGreeting() + ' Here are your apps.')
      }
    }

    // Default icon based on app type - uses initial letter for non-turtle apps
    const getDefaultIcon = (appType, appTitle) => {
      return appType === 'turtle' ? '🐢' : appTitle.charAt(0).toUpperCase()
    }

    // Fetch user's apps from backend
    const fetchUserApps = async () => {
      if (!user.value?.id) return
      try {
        const apps = await conversationAPI.getByUser(user.value.id)
        userApps.value = apps.map(app => ({
          id: `user-${app.id}`,
          appId: app.id,
          name: app.title,
          icon: app.app_image || getDefaultIcon(app.app_type, app.title),
          category: app.app_type === 'turtle' ? t.value.home.turtleApp || 'Turtle App' : t.value.home.uploadedApp || 'Uploaded App',
          route: app.app_type === 'turtle'
            ? `/turtle-playground/${app.id}`
            : { name: 'Workspace', query: { conversationId: app.id } },
          themeColor: '#024A14',
          themeColorDark: '#01350e',
          isUserApp: true
        }))
      } catch (error) {
        console.error('Failed to fetch user apps:', error)
      }
    }

    const handleAppClick = (app) => {
      if (app.route) {
        router.push(app.route)
      }
    }

    const handleCreateApp = async (appData) => {
      try {
        if (!user.value?.id) {
          console.error('User not logged in')
          return
        }

        await conversationAPI.create(user.value.id, appData)

        showNewAppDialog.value = false

        voiceService.speak('App created!')

        await fetchUserApps()
      } catch (error) {
        console.error('Failed to create app:', error)
        voiceService.speak("Couldn't create the app.")
      }
    }

    // Edit app handlers
    const handleEditApp = (app) => {
      selectedApp.value = app
      showEditDialog.value = true
    }

    const handleSaveEdit = async (editData) => {
      try {
        await conversationAPI.update(editData.id, {
          title: editData.title,
          app_image: editData.app_image
        })
        showEditDialog.value = false
        voiceService.speak('App updated!')
        await fetchUserApps()
      } catch (error) {
        console.error('Failed to update app:', error)
        voiceService.speak('Update failed.')
      }
    }

    // Delete app handlers
    const handleDeleteApp = (app) => {
      selectedApp.value = app
      showDeleteDialog.value = true
    }

    const handleConfirmDelete = async (appId) => {
      try {
        await conversationAPI.delete(appId)
        showDeleteDialog.value = false
        voiceService.speak('App deleted.')
        await fetchUserApps()
      } catch (error) {
        console.error('Failed to delete app:', error)
        voiceService.speak('Deletion failed.')
        showDeleteDialog.value = false
      }
    }

    // Fetch user's favorites
    const fetchUserFavorites = async () => {
      if (!user.value?.id) return
      try {
        const favorites = await favoritesAPI.getByUser(user.value.id)
        userFavorites.value = favorites
      } catch (error) {
        console.error('Failed to fetch favorites:', error)
      }
    }

    // Check if an app is favorited
    const isAppFavorited = (app) => {
      return userFavorites.value.some(fav => fav.conversation_id === app.appId)
    }

    const handleToggleFavorite = async (app) => {
      if (!user.value?.id) return

      const wasFavorited = isAppFavorited(app)

      try {
        await favoritesAPI.toggle(user.value.id, { conversation_id: app.appId })
        await fetchUserFavorites()
        voiceService.speak(wasFavorited ? 'Removed from favorites.' : 'Added to favorites!')
      } catch (error) {
        console.error('Failed to toggle favorite:', error)
      }
    }

    // All apps (only user apps now)
    const allFeaturedApps = computed(() => userApps.value)

    // Computed property for favorite apps
    const favoriteApps = computed(() => {
      return userFavorites.value
        .filter(fav => fav.conversation_id)
        .map(fav => userApps.value.find(app => app.appId === fav.conversation_id))
        .filter(Boolean)
    })

    // Fetch user apps on mount
    onMounted(() => {
      fetchUserApps()
      fetchUserFavorites()

      const handleFirstInteraction = () => {
        voiceService.enableAudioContext()
        greetUser()
        document.removeEventListener('click', handleFirstInteraction)
        document.removeEventListener('keydown', handleFirstInteraction)
      }

      document.addEventListener('click', handleFirstInteraction)
      document.addEventListener('keydown', handleFirstInteraction)
    })

    // Re-fetch when user changes
    watch(() => user.value?.id, (newId) => {
      if (newId) {
        fetchUserApps()
        fetchUserFavorites()
      } else {
        userApps.value = []
        userFavorites.value = []
      }
    })

    return {
      handleAppClick,
      handleCreateApp,
      handleEditApp,
      handleSaveEdit,
      handleDeleteApp,
      handleConfirmDelete,
      handleToggleFavorite,
      isAppFavorited,
      allFeaturedApps,
      userApps,
      favoriteApps,
      t,
      showNewAppDialog,
      showEditDialog,
      showDeleteDialog,
      selectedApp
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
/* Main content area - scrollable */
.main-content {
  margin-left: var(--sidebar-width);
  margin-top: var(--toolbar-height);
  height: calc(100vh - var(--toolbar-height));
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.content-area::-webkit-scrollbar {
  width: 8px;
}

.content-area::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.content-area::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.content-area::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}

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

/* Favourites section styles */
.favorites-section {
  margin-bottom: 48px;
}

.favorites-title {
  color: #1a1a1a;
}

/* Featured section */
.featured-section {
  margin-bottom: 48px;
}

@media (max-width: 768px) {
  .content-area {
    padding: 16px;
  }

  .section-title {
    font-size: 22px;
  }
}
</style>
