<template>
  <div class="app-container">
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
import Sidebar from '@/shared/components/Sidebar.vue'

export default {
  name: 'Profile',
  components: {
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
  padding: 32px;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.profile-content {
  padding: 32px;
}

.profile-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.profile-header {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 2px solid #e8e8e8;
}

.profile-avatar-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #024A14 0%, #01350e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 48px;
  color: white;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
}

.profile-name {
  font-size: 32px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
  font-family: 'Jaldi', sans-serif;
}

.profile-email {
  font-size: 16px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 32px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section .section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
  font-family: 'Jaldi', sans-serif;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  font-family: 'Jaldi', sans-serif;
}

.profile-input {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  transition: all 0.2s ease;
  width: 100%;
}

.profile-input:focus {
  outline: none;
  border-color: #024A14;
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
  font-size: 14px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-button {
  background: #024A14;
  color: white;
}

.save-button:hover {
  background: #01350e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.3);
}

.cancel-button {
  background: #f5f5f5;
  color: #666;
}

.cancel-button:hover {
  background: #e0e0e0;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
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
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
}

/* Responsive Design */
@media (max-width: 768px) {
  .profile-content {
    padding: 16px;
  }

  .profile-card {
    padding: 24px 20px;
  }

  .profile-header {
    margin-bottom: 24px;
    padding-bottom: 24px;
  }

  .profile-avatar-large {
    width: 80px;
    height: 80px;
    font-size: 32px;
    margin-bottom: 16px;
  }

  .profile-name {
    font-size: 24px;
  }

  .profile-email {
    font-size: 14px;
  }

  .profile-details {
    gap: 24px;
  }

  .detail-section .section-title {
    font-size: 18px;
  }

  .profile-actions {
    flex-direction: column;
  }

  .save-button,
  .cancel-button {
    width: 100%;
  }

  .page-title {
    font-size: 22px;
  }
}

@media (max-width: 480px) {
  .profile-card {
    padding: 20px 16px;
  }

  .profile-avatar-large {
    width: 60px;
    height: 60px;
    font-size: 24px;
  }

  .profile-name {
    font-size: 20px;
  }

  .detail-section .section-title {
    font-size: 16px;
  }
}
</style>

