<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">Settings</h2>
      </header>
      
      <div class="content-area settings-content">
        <div class="settings-container">
          <!-- Language Selection Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">Language Selection</h3>
              <p class="section-description">Choose your preferred language for the application</p>
            </div>
            <div class="settings-options">
              <div 
                v-for="lang in languages" 
                :key="lang.code"
                class="option-card"
                :class="{ 'active': selectedLanguage === lang.code }"
                @click="selectLanguage(lang.code)"
              >
                <div class="option-content">
                  <span class="option-icon">{{ lang.flag }}</span>
                  <div class="option-info">
                    <div class="option-label">{{ lang.name }}</div>
                    <div class="option-subtitle">{{ lang.nativeName }}</div>
                  </div>
                </div>
                <div class="option-check" v-if="selectedLanguage === lang.code">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Voice Model Selection Section -->
          <div class="settings-section">
            <div class="settings-header">
              <h3 class="section-title">Voice Model Selection</h3>
              <p class="section-description">Select a voice model for speech recognition and synthesis</p>
            </div>
            <div class="settings-options">
              <div 
                v-for="voice in voiceModels" 
                :key="voice.id"
                class="option-card"
                :class="{ 'active': selectedVoiceModel === voice.id }"
                @click="selectVoiceModel(voice.id)"
              >
                <div class="option-content">
                  <div class="option-icon-voice">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 14C13.1 14 14 13.1 14 12V6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6V12C10 13.1 10.9 14 12 14ZM19 12C19 15.87 15.87 19 12 19V21H16V23H8V21H12V19C8.13 19 5 15.87 5 12H7C7 14.76 9.24 17 12 17C14.76 17 17 14.76 17 12H19Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="option-info">
                    <div class="option-label">{{ voice.name }}</div>
                    <div class="option-subtitle">{{ voice.description }}</div>
                  </div>
                </div>
                <div class="option-check" v-if="selectedVoiceModel === voice.id">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                  </svg>
                </div>
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

export default {
  name: 'Settings',
  components: {
    Sidebar
  },
  data() {
    return {
      languages: [
        { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
        { code: 'th', name: 'Thai', nativeName: 'ไทย', flag: '🇹🇭' }
      ],
      voiceModels: [
        { 
          id: 'whisper-base', 
          name: 'Whisper Base', 
          description: 'Fast and efficient, good for general use' 
        },
        { 
          id: 'whisper-small', 
          name: 'Whisper Small', 
          description: 'Balanced performance and accuracy' 
        },
        { 
          id: 'whisper-medium', 
          name: 'Whisper Medium', 
          description: 'Higher accuracy, slightly slower' 
        },
        { 
          id: 'whisper-large', 
          name: 'Whisper Large', 
          description: 'Best accuracy, requires more resources' 
        },
        { 
          id: 'google-cloud', 
          name: 'Google Cloud Speech', 
          description: 'Cloud-based, high accuracy' 
        },
        { 
          id: 'azure-speech', 
          name: 'Azure Speech', 
          description: 'Microsoft Azure speech services' 
        }
      ],
      selectedLanguage: 'en',
      selectedVoiceModel: 'whisper-base'
    }
  },
  mounted() {
    this.loadSettings()
  },
  methods: {
    selectLanguage(code) {
      this.selectedLanguage = code
      this.saveSettings()
    },
    selectVoiceModel(id) {
      this.selectedVoiceModel = id
      this.saveSettings()
    },
    loadSettings() {
      const settings = localStorage.getItem('appSettings')
      if (settings) {
        try {
          const parsed = JSON.parse(settings)
          this.selectedLanguage = parsed.language || 'en'
          this.selectedVoiceModel = parsed.voiceModel || 'whisper-base'
        } catch (error) {
          console.error('Error loading settings:', error)
        }
      }
    },
    saveSettings() {
      const settings = {
        language: this.selectedLanguage,
        voiceModel: this.selectedVoiceModel,
        updatedAt: new Date().toISOString()
      }
      localStorage.setItem('appSettings', JSON.stringify(settings))
    }
  }
}
</script>

<style scoped>
.settings-content {
  padding: 32px;
}

.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.settings-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 32px;
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
}

.settings-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin: 0 0 8px 0;
}

.section-description {
  font-size: 14px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
  margin: 0;
}

.settings-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.option-card {
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.option-card:hover {
  border-color: #024A14;
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.1);
}

.option-card.active {
  border-color: #024A14;
  background: #f0f7f2;
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.15);
}

.option-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.option-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.option-icon-voice {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  color: #024A14;
}

.option-info {
  flex: 1;
}

.option-label {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 4px;
}

.option-subtitle {
  font-size: 13px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
}

.option-check {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #024A14;
  border-radius: 50%;
  color: white;
  flex-shrink: 0;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
}

@media (max-width: 768px) {
  .settings-content {
    padding: 16px;
  }

  .settings-section {
    padding: 20px;
  }

  .settings-options {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 22px;
  }
}
</style>

