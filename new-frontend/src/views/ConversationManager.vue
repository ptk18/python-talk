<template>
  <div class="app-container">
    <Sidebar />
    <div class="homeReal__viewport">
      <div class="homeReal__headerRow">
      <div class="homeReal__titleWrapper">
        <span class="homeReal__titleLabel">Title: </span>
        <input
          class="homeReal__titleInput"
          placeholder=""
          v-model="title"
        />
      </div>
      <input
        ref="fileInputRef"
        type="file"
        accept=".py"
        style="display: none"
        @change="handleFileChange"
      />
      <button class="homeReal__btn" @click="handleFileSelect">
        {{ selectedFile ? selectedFile.name : 'Upload File' }}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <button class="homeReal__btn homeReal__btn--create" @click="handleCreate">Create</button>
    </div>

    <main class="homeReal__panel">
      <div class="homeReal__searchWrap">
        <input
          class="homeReal__search"
          placeholder="Search..."
          v-model="searchQuery"
        />
        <button class="homeReal__searchIcon" type="button" aria-label="Search">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2" />
            <path d="m20 20-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="homeReal__list">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="homeReal__row"
        >
          <div class="homeReal__row-content" @click="handleConversationClick(conv.id)">
            <strong>{{ conv.title }}</strong><br />
            <small>File: {{ conv.file_name || 'N/A' }}</small>
          </div>
          <div class="homeReal__row-actions">
            <button
              class="homeReal__icon-btn"
              @click.stop="handleConversationClick(conv.id)"
              title="Open File"
              aria-label="Open File"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-7-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M13 2v7h7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 13l-3 3 3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 16H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button
              class="homeReal__icon-btn homeReal__icon-btn--delete"
              @click.stop="handleDeleteConversation(conv.id)"
              title="Delete Conversation"
              aria-label="Delete Conversation"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M10 11v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M14 11v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import Sidebar from '../components/Sidebar.vue';
import { conversationAPI } from '../services/api';
import { useAuth } from '../composables/useAuth';
import { voiceService } from '../services/voiceService';

export default {
  name: 'Home',
  components: {
    Sidebar
  },
  setup() {
    const router = useRouter();
    const { user } = useAuth();
    const title = ref('');
    const searchQuery = ref('');
    const conversations = ref([]);
    const selectedFile = ref(null);
    const fileInputRef = ref(null);
    const hasGreeted = ref(false);

    const filteredConversations = computed(() => {
      return conversations.value.filter(conv =>
        conv.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        (conv.file_name && conv.file_name.toLowerCase().includes(searchQuery.value.toLowerCase()))
      );
    });

    const fetchConversations = async () => {
      if (!user.value) return;
      try {
        const convs = await conversationAPI.getByUser(user.value.id);
        conversations.value = convs;
      } catch (err) {
        alert('Failed to fetch conversations.');
      }
    };

    const handleFileSelect = () => {
      fileInputRef.value?.click();
    };

    const handleFileChange = (e) => {
      const file = e.target.files?.[0];
      if (file) {
        selectedFile.value = file;
      }
    };

    const handleCreate = async () => {
      if (!title.value.trim() || !selectedFile.value || !user.value) {
        voiceService.speak('Please enter a title and select a Python file');
        alert('Please enter a title and select a Python file.');
        return;
      }

      try {
        const code = await selectedFile.value.text();
        await conversationAPI.create(user.value.id, {
          title: title.value,
          file_name: selectedFile.value.name,
          code,
        });
        title.value = '';
        selectedFile.value = null;
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
        voiceService.speak('Conversation created successfully');
        fetchConversations();
      } catch (err) {
        voiceService.speak('Failed to create conversation');
        alert('Failed to create conversation.');
      }
    };

    const handleConversationClick = (convId) => {
      router.push(`/workspace?conversationId=${convId}`);
    };

    const handleDeleteConversation = async (convId) => {
      if (!window.confirm('Are you sure you want to delete this conversation?')) {
        voiceService.speak('Deletion cancelled');
        return;
      }
      try {
        await conversationAPI.delete(convId);
        voiceService.speak('Conversation deleted successfully');
        fetchConversations();
      } catch (err) {
        voiceService.speak('Failed to delete conversation');
        alert('Failed to delete conversation.');
      }
    };

    const getGreeting = () => {
      const hour = new Date().getHours();
      if (hour >= 5 && hour < 12) return 'Good Morning, Sir';
      if (hour >= 12 && hour < 17) return 'Good Afternoon, Sir';
      if (hour >= 17 && hour < 21) return 'Good Evening, Sir';
      return 'Welcome, Sir';
    };

    onMounted(() => {
      if (user.value) {
        fetchConversations();
      }

      const greetOnInteraction = () => {
        if (!hasGreeted.value && user.value) {
          hasGreeted.value = true;
          const greeting = getGreeting();
          voiceService.speak(greeting);
          document.removeEventListener('click', greetOnInteraction);
          document.removeEventListener('keydown', greetOnInteraction);
        }
      };

      document.addEventListener('click', greetOnInteraction);
      document.addEventListener('keydown', greetOnInteraction);
    });

    return {
      title,
      searchQuery,
      conversations,
      selectedFile,
      fileInputRef,
      filteredConversations,
      handleFileSelect,
      handleFileChange,
      handleCreate,
      handleConversationClick,
      handleDeleteConversation,
    };
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

:root {
    --bg: #b8c7b4;
    --deep: #1b4e2b;
    --white: #fff;
    --shadow: 0 20px 60px rgba(0, 0, 0, .08);
    --panelRadius: 10px;
}

.homeReal__viewport {
    margin-left: 260px;
    width: calc(100vw - 260px);
    height: 100vh;
    background: var(--bg);
    font-family: "Poppins", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    color: var(--deep);
    display: grid;
    grid-template-rows: auto 1fr;
}

.homeReal__headerRow {
    width: 86%;
    max-width: 1600px;
    margin: 45px auto 18px;
    display: flex;
    flex-wrap: nowrap;
    gap: 18px;
    align-items: center;
}

.homeReal__titleWrapper {
    display: flex;
    align-items: center;
    flex: 1;
    min-width: 250px;
    height: 48px;
    border-radius: 8px;
    background: #e8eee9;
    padding: 0 14px;
    box-sizing: border-box;
}

.homeReal__titleLabel {
    font-weight: 700;
    font-size: 18px;
    color: var(--deep);
    flex-shrink: 0;
    margin-right: 8px;
}

.homeReal__titleInput {
    height: 100%;
    width: 100%;
    min-width: 0;
    border-radius: 0;
    border: none;
    padding: 0;
    background: transparent;
    color: var(--deep);
    font-weight: 700;
    font-size: 18px;
    outline: none;
    box-sizing: border-box;
}

.homeReal__btn {
    height: 48px;
    padding: 0 20px;
    border-radius: 12px;
    border: 2px solid var(--deep);
    background: #ffffff;
    color: var(--deep);
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    box-shadow: 0 2px 0 rgba(0, 0, 0, .06);
    white-space: nowrap;
    flex-shrink: 0;
}

.homeReal__btn--create {
    padding: 0 24px;
}

.homeReal__panel {
    width: 83%;
    max-width: 1600px;
    margin: 0 auto 24px;
    background: #ffffff;
    border-radius: var(--panelRadius);
    box-shadow: var(--shadow);
    padding: 26px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.homeReal__searchWrap {
    padding: 6px 12px 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
}

.homeReal__search {
    width: 100%;
    max-width: 1400px;
    height: 46px;
    border: 1.5px solid #e7e7e7;
    border-radius: 12px;
    padding: 0 14px;
    font-size: 15px;
    outline: none;
    background: #fff;
}

.homeReal__search::placeholder {
    color: #9aa19e;
}

.homeReal__searchIcon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 46px;
    height: 46px;
    border: 1.5px solid #e7e7e7;
    border-radius: 12px;
    background: #fff;
    color: var(--deep);
    cursor: pointer;
    padding: 0;
    transition: background 0.2s ease, border-color 0.2s ease;
    flex-shrink: 0;
}

.homeReal__searchIcon:hover {
    background: #f5f7f6;
    border-color: var(--deep);
}

.homeReal__list {
    margin-top: 8px;
    border-radius: 8px;
    overflow-y: auto;
    flex: 1;
}

.homeReal__row {
    min-height: 72px;
    border-bottom: 1.2px solid rgba(0, 0, 0, .06);
    padding: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}

.homeReal__row:last-child {
    border-bottom: none;
}

.homeReal__row-content {
    flex: 1;
    cursor: pointer;
    min-width: 0;
}

.homeReal__row-content:hover {
    opacity: 0.8;
}

.homeReal__row-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
}

.homeReal__icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: 1.5px solid #e7e7e7;
    border-radius: 8px;
    background: #fff;
    color: var(--deep);
    cursor: pointer;
    padding: 0;
    transition: all 0.2s ease;
}

.homeReal__icon-btn:hover {
    background: #f5f7f6;
    border-color: var(--deep);
}

.homeReal__icon-btn--delete:hover {
    background: #fee;
    border-color: #d33;
    color: #d33;
}

.homeReal__icon-btn:active {
    transform: scale(0.97);
}

@media (max-width: 768px) {
    .homeReal__headerRow {
        width: 95%;
        flex-direction: column;
        gap: 12px;
        margin: 30px auto 15px;
    }

    .homeReal__panel {
        width: 95%;
        padding: 20px;
    }
}
</style>
