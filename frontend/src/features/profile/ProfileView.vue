<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <main class="main-content">
      <header class="top-header">
        <h2 class="page-title">{{ t.profile.pageTitle }}</h2>
      </header>

      <div class="content-area profile-content">
        <div class="profile-card">
          <div class="profile-header">
            <div class="profile-avatar-large">
              <span>{{ userInfo.name ? userInfo.name.charAt(0).toUpperCase() : 'U' }}</span>
            </div>
            <h1 class="profile-name">{{ userInfo.name || 'User' }}</h1>
            <p class="profile-email">{{ userInfo.email || 'user@example.com' }}</p>
          </div>

          <div class="profile-details">
            <div class="detail-section">
              <h3 class="section-title">{{ t.profile.personalInformation }}</h3>
              <div class="detail-item">
                <label>{{ t.profile.fullName }}</label>
                <input
                  type="text"
                  v-model="profileData.name"
                  class="profile-input"
                  :placeholder="t.profile.enterFullName"
                />
              </div>
              <div class="detail-item">
                <label>{{ t.profile.email }}</label>
                <input
                  type="email"
                  v-model="profileData.email"
                  class="profile-input"
                  :placeholder="t.profile.enterEmail"
                />
              </div>
            </div>

            <div class="detail-section">
              <h3 class="section-title">{{ t.profile.accountSettings }}</h3>
              <div class="detail-item">
                <label>{{ t.profile.changePassword }}</label>
                <input
                  type="password"
                  v-model="profileData.password"
                  class="profile-input"
                  :placeholder="t.profile.enterNewPassword"
                />
              </div>
              <div class="detail-item">
                <label>{{ t.profile.confirmPassword }}</label>
                <input
                  type="password"
                  v-model="profileData.confirmPassword"
                  class="profile-input"
                  :placeholder="t.profile.confirmNewPassword"
                />
              </div>
            </div>

            <div class="profile-actions">
              <button class="save-button" @click="saveProfile">{{ t.profile.saveChanges }}</button>
              <button class="cancel-button" @click="cancelEdit">{{ t.profile.cancel }}</button>
            </div>

            <div v-if="message" :class="['message', messageType]">
              {{ message }}
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useLanguage } from '@py-talk/shared'
import { useTranslations } from '@/utils/translations'
import TopToolbar from '@/shared/components/TopToolbar.vue'
import Sidebar from '@/shared/components/Sidebar.vue'

export default {
  name: 'Profile',
  components: {
    TopToolbar,
    Sidebar
  },
  setup() {
    const { language } = useLanguage()
    const t = computed(() => useTranslations(language.value))
    return { t }
  },
  data() {
    return {
      userInfo: {},
      profileData: {
        name: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      message: '',
      messageType: 'success'
    }
  },
  mounted() {
    this.loadUserInfo()
  },
  methods: {
    loadUserInfo() {
      const stored = localStorage.getItem('userInfo')
      if (stored) {
        this.userInfo = JSON.parse(stored)
        this.profileData.name = this.userInfo.name || ''
        this.profileData.email = this.userInfo.email || ''
      }
    },
    saveProfile() {
      // Validation
      if (!this.profileData.name || !this.profileData.email) {
        this.showMessage(this.t.profile.fillAllFields, 'error')
        return
      }

      if (this.profileData.password && this.profileData.password !== this.profileData.confirmPassword) {
        this.showMessage(this.t.profile.passwordsDoNotMatch, 'error')
        return
      }

      // Update user info
      const updatedUserInfo = {
        name: this.profileData.name,
        email: this.profileData.email
      }

      localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo))
      this.userInfo = updatedUserInfo
      window.dispatchEvent(new Event('userInfoUpdated'))

      this.showMessage(this.t.profile.profileUpdated, 'success')

      // Clear password fields
      this.profileData.password = ''
      this.profileData.confirmPassword = ''
    },
    cancelEdit() {
      this.loadUserInfo()
      this.profileData.password = ''
      this.profileData.confirmPassword = ''
      this.message = ''
    },
    showMessage(text, type) {
      this.message = text
      this.messageType = type
      setTimeout(() => {
        this.message = ''
      }, 3000)
    }
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.main-content {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-area.profile-content {
  padding: 20px;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.profile-content {
  padding: 20px;
}

.profile-card {
  background: var(--color-surface);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.profile-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--color-border);
}

.profile-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: var(--font-size-page-title);
  color: white;
  font-weight: var(--font-weight-medium);
}

.profile-name {
  font-size: var(--font-size-page-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: 8px;
}

.profile-email {
  font-size: var(--font-size-card-title);
  color: var(--color-text-muted);
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-section .section-title {
  font-size: var(--font-size-section-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item label {
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.profile-input {
  padding: 12px 16px;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  font-size: var(--font-size-body);
  transition: all 0.2s ease;
  width: 100%;
}

.profile-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.profile-actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.save-button,
.cancel-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-button {
  background: var(--color-primary);
  color: white;
}

.save-button:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.3);
}

.cancel-button {
  background: #f5f5f5;
  color: var(--color-text-muted);
}

.cancel-button:hover {
  background: var(--color-border);
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: var(--font-size-body);
  margin-top: 16px;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.page-title {
  font-size: var(--font-size-page-title);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

/* Responsive Design */
@media (max-width: 768px) {
  .profile-content {
    padding: 16px;
  }

  .profile-card {
    padding: 24px 20px;
  }

  .profile-actions {
    flex-direction: column;
  }

  .save-button,
  .cancel-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .profile-card {
    padding: 20px 16px;
  }

  .profile-avatar-large {
    width: 60px;
    height: 60px;
  }
}
</style>

