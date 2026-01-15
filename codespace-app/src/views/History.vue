<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">History</h2>
      </header>

      <div class="content-area history-content">
        <div class="history-container">
          <div v-if="loading" class="loading-state">
            <p>Loading conversations...</p>
          </div>

          <div v-else-if="conversations.length === 0" class="empty-state">
            <h3>No Chat History</h3>
            <p>Your chat conversations will appear here</p>
            <router-link to="/conversation-manager" class="start-chat-button">Start New Chat</router-link>
          </div>

          <div v-else class="history-list">
            <div
              v-for="conv in conversations"
              :key="conv.id"
              class="history-item"
            >
              <div class="history-item-header">
                <div class="history-item-info" @click="openConversation(conv.id)">
                  <input
                    v-if="editingId === conv.id"
                    v-model="editingTitle"
                    @blur="saveTitle(conv.id)"
                    @keyup.enter="saveTitle(conv.id)"
                    @keyup.esc="cancelEdit"
                    class="chat-name-input"
                    ref="editInput"
                  />
                  <h3 v-else class="history-item-title">{{ conv.title || 'Untitled' }}</h3>
                  <p class="history-item-date">{{ formatDate(conv.created_at) }}</p>
                </div>
                <div class="history-item-actions">
                  <button
                    class="action-button edit-button"
                    @click.stop="startEdit(conv)"
                    title="Rename conversation"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 17.25V21H6.75L17.81 9.94L14.06 6.19L3 17.25ZM20.71 7.04C21.1 6.65 21.1 6.02 20.71 5.63L18.37 3.29C17.98 2.9 17.35 2.9 16.96 3.29L15.12 5.12L18.87 8.87L20.71 7.04Z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button
                    class="action-button delete-button"
                    @click.stop="deleteConversation(conv.id)"
                    title="Delete conversation"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19ZM19 4H15.5L14.5 3H9.5L8.5 4H5V6H19V4Z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="history-item-preview" @click="openConversation(conv.id)">
                <span class="file-name">{{ conv.file_name || 'No file' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import { conversationAPI, useAuth } from '@py-talk/shared'

export default {
  name: 'History',
  components: {
    Sidebar
  },
  data() {
    return {
      conversations: [],
      loading: true,
      editingId: null,
      editingTitle: ''
    }
  },
  setup() {
    const { user } = useAuth()
    return { user }
  },
  mounted() {
    this.loadConversations()
  },
  watch: {
    '$route'() {
      this.loadConversations()
    },
    'user'() {
      this.loadConversations()
    }
  },
  methods: {
    async loadConversations() {
      if (!this.user) {
        this.loading = false
        this.conversations = []
        return
      }

      try {
        this.loading = true
        const convs = await conversationAPI.getByUser(this.user.id)
        // Sort by most recent first
        this.conversations = convs.sort((a, b) => {
          const dateA = new Date(a.created_at || 0)
          const dateB = new Date(b.created_at || 0)
          return dateB - dateA
        })
      } catch (error) {
        console.error('Error loading conversations:', error)
        this.conversations = []
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = Math.abs(now - date)
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 0) {
        return 'Today'
      } else if (diffDays === 1) {
        return 'Yesterday'
      } else if (diffDays < 7) {
        return `${diffDays} days ago`
      } else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        })
      }
    },
    openConversation(convId) {
      this.$router.push(`/workspace?conversationId=${convId}`)
    },
    startEdit(conv) {
      this.editingId = conv.id
      this.editingTitle = conv.title || ''
      this.$nextTick(() => {
        const input = this.$refs.editInput
        if (input && input[0]) {
          input[0].focus()
          input[0].select()
        }
      })
    },
    async saveTitle(convId) {
      if (!this.editingTitle.trim()) {
        this.cancelEdit()
        return
      }

      try {
        await conversationAPI.update(convId, { title: this.editingTitle.trim() })
        await this.loadConversations()
      } catch (error) {
        console.error('Error saving title:', error)
        alert('Failed to update title')
      }

      this.editingId = null
      this.editingTitle = ''
    },
    cancelEdit() {
      this.editingId = null
      this.editingTitle = ''
    },
    async deleteConversation(convId) {
      if (confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
        try {
          await conversationAPI.delete(convId)
          await this.loadConversations()
        } catch (error) {
          console.error('Error deleting conversation:', error)
          alert('Failed to delete conversation')
        }
      }
    }
  }
}
</script>

<style scoped>
.history-content {
  padding: 0;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.history-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-family: 'Jaldi', sans-serif;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
  font-family: 'Jaldi', sans-serif;
  color: #1a1a1a;
}

.empty-state p {
  font-size: 16px;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 24px;
}

.start-chat-button {
  padding: 12px 24px;
  background: #024A14;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-block;
}

.start-chat-button:hover {
  background: #01350e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.3);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
  padding-right: 8px;
}

.history-list::-webkit-scrollbar {
  width: 8px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

.history-list::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}

.history-item {
  padding: 20px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fafafa;
  margin-top: 10px;
}

.history-item:hover {
  border-color: #024A14;
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.history-item-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-item:hover .history-item-actions {
  opacity: 1;
}

.action-button {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.8);
  color: #666;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-button:hover {
  background: #f0f0f0;
  color: #333;
}

.edit-button:hover {
  color: #024A14;
  background: rgba(2, 74, 20, 0.1);
}

.delete-button:hover {
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
}

.chat-name-input {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  border: 2px solid #024A14;
  border-radius: 6px;
  padding: 4px 8px;
  width: 100%;
  max-width: 300px;
  outline: none;
  background: white;
}

.history-item-info {
  flex: 1;
  cursor: pointer;
}

.history-item-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
  font-family: 'Jaldi', sans-serif;
}

.history-item-date {
  font-size: 12px;
  color: #999;
  font-family: 'Jaldi', sans-serif;
}

.history-item-preview {
  display: flex;
  align-items: center;
}

.file-name {
  font-size: 12px;
  color: #024A14;
  background: rgba(2, 74, 20, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
  font-family: 'Jaldi', sans-serif;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
}

@media (max-width: 768px) {
  .history-content {
    height: calc(100vh - 100px);
  }

  .history-container {
    padding: 16px;
    border-radius: 0;
  }

  .history-item {
    padding: 16px;
  }

  .history-item-title {
    font-size: 16px;
  }

  .history-item-actions {
    opacity: 1;
  }

  .action-button {
    width: 32px;
    height: 32px;
  }

  .page-title {
    font-size: 22px;
  }
}
</style>
