<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">History</h2>
      </header>
      
      <div class="content-area history-content">
        <div class="history-container">
          <div v-if="chatHistory.length === 0" class="empty-state">
            <h3>No Chat History</h3>
            <p>Your chat conversations will appear here</p>
            <router-link to="/conversation-manager" class="start-chat-button">Start New Chat</router-link>
          </div>
          
          <div v-else class="history-list">
            <div 
              v-for="chat in chatHistory" 
              :key="chat.id"
              class="history-item"
            >
              <div class="history-item-header">
                <div class="history-item-info" @click="continueChat(chat.id)">
                  <input 
                    v-if="editingChatId === chat.id"
                    v-model="editingChatName"
                    @blur="saveChatName(chat.id)"
                    @keyup.enter="saveChatName(chat.id)"
                    @keyup.esc="cancelEdit"
                    class="chat-name-input"
                    ref="editInput"
                  />
                  <h3 v-else class="history-item-title">{{ getChatTitle(chat) }}</h3>
                  <p class="history-item-date">{{ formatDate(chat.updatedAt) }}</p>
                </div>
                <div class="history-item-actions">
                  <button 
                    class="action-button edit-button"
                    @click.stop="startEdit(chat.id, chat)"
                    :title="'Rename chat'"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 17.25V21H6.75L17.81 9.94L14.06 6.19L3 17.25ZM20.71 7.04C21.1 6.65 21.1 6.02 20.71 5.63L18.37 3.29C17.98 2.9 17.35 2.9 16.96 3.29L15.12 5.12L18.87 8.87L20.71 7.04Z" fill="currentColor"/>
                    </svg>
                  </button>
                  <button 
                    class="action-button delete-button"
                    @click.stop="deleteChat(chat.id)"
                    :title="'Delete chat'"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19ZM19 4H15.5L14.5 3H9.5L8.5 4H5V6H19V4Z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="history-item-preview" @click="continueChat(chat.id)">
                <span class="message-count">{{ chat.messages.length }} messages</span>
              </div>
              <!-- <div class="history-item-preview-text" @click="continueChat(chat.id)">
                {{ getLastMessage(chat) }}
              </div> -->
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'

export default {
  name: 'History',
  components: {
    Sidebar
  },
  data() {
    return {
      chatHistory: [],
      editingChatId: null,
      editingChatName: ''
    }
  },
  mounted() {
    this.loadChatHistory()
  },
  watch: {
    '$route'() {
      // Reload history when navigating to this page
      this.loadChatHistory()
    }
  },
  methods: {
    loadChatHistory() {
      try {
        const stored = localStorage.getItem('chatHistory')
        if (stored) {
          const parsed = JSON.parse(stored)
          // Filter out chats with no messages
          this.chatHistory = parsed.filter(chat => chat.messages && chat.messages.length > 0)
          // Sort by most recent first
          this.chatHistory.sort((a, b) => {
            const dateA = new Date(a.updatedAt || a.createdAt || 0)
            const dateB = new Date(b.updatedAt || b.createdAt || 0)
            return dateB - dateA
          })
        } else {
          this.chatHistory = []
        }
      } catch (error) {
        console.error('Error loading chat history:', error)
        this.chatHistory = []
      }
    },
    getChatTitle(chat) {
      // Use custom name if set
      if (chat.customName) {
        return chat.customName
      }
      // Otherwise use first message
      if (!chat.messages || chat.messages.length === 0) return 'New Chat'
      const firstMessage = chat.messages.find(m => m.type === 'sent') || chat.messages[0]
      if (firstMessage && firstMessage.text) {
        return firstMessage.text.length > 30 
          ? firstMessage.text.substring(0, 30) + '...' 
          : firstMessage.text
      }
      return 'Chat Conversation'
    },
    getLastMessage(chat) {
      if (!chat.messages || chat.messages.length === 0) return 'No messages yet'
      const lastMessage = chat.messages[chat.messages.length - 1]
      if (lastMessage && lastMessage.text) {
        return lastMessage.text.length > 100 
          ? lastMessage.text.substring(0, 100) + '...' 
          : lastMessage.text
      }
      return 'No messages yet'
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = Math.abs(now - date)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
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
    continueChat(chatId) {
      this.$router.push({ path: '/conversation-manager', query: { id: chatId } })
    },
    startEdit(chatId, chat) {
      this.editingChatId = chatId
      this.editingChatName = chat.customName || this.getChatTitle(chat)
      this.$nextTick(() => {
        const input = this.$refs.editInput
        if (input && input[0]) {
          input[0].focus()
          input[0].select()
        }
      })
    },
    saveChatName(chatId) {
      if (!this.editingChatName.trim()) {
        this.cancelEdit()
        return
      }
      
      try {
        const stored = localStorage.getItem('chatHistory')
        if (stored) {
          const chatHistory = JSON.parse(stored)
          const chatIndex = chatHistory.findIndex(c => c.id === chatId)
          if (chatIndex !== -1) {
            chatHistory[chatIndex].customName = this.editingChatName.trim()
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory))
            this.loadChatHistory()
          }
        }
      } catch (error) {
        console.error('Error saving chat name:', error)
      }
      
      this.editingChatId = null
      this.editingChatName = ''
    },
    cancelEdit() {
      this.editingChatId = null
      this.editingChatName = ''
    },
    deleteChat(chatId) {
      if (confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        try {
          const stored = localStorage.getItem('chatHistory')
          if (stored) {
            const chatHistory = JSON.parse(stored)
            const filtered = chatHistory.filter(c => c.id !== chatId)
            localStorage.setItem('chatHistory', JSON.stringify(filtered))
            this.loadChatHistory()
          }
        } catch (error) {
          console.error('Error deleting chat:', error)
          alert('Error deleting chat. Please try again.')
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
  background: #001f3f;
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
  background: #001a33;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 31, 63, 0.3);
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
  border-color: #001f3f;
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
  color: #001f3f;
  background: rgba(0, 31, 63, 0.1);
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
  border: 2px solid #001f3f;
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

.message-count {
  font-size: 12px;
  color: #001f3f;
  background: rgba(0, 31, 63, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
  font-family: 'Jaldi', sans-serif;
}

.history-item-preview-text {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  font-family: 'Jaldi', sans-serif;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

