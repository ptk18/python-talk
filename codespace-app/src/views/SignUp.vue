<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-logo">PyTalk</h1>
        <p class="auth-subtitle">Create your account</p>
      </div>
      
      <form @submit.prevent="handleSignUp" class="auth-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            type="email"
            id="email"
            v-model="email"
            placeholder="Enter your email"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="username">Username</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="Choose a username"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="Create a password"
            required
            class="form-input"
            minlength="6"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="confirmPassword"
            placeholder="Confirm your password"
            required
            class="form-input"
          />
        </div>
        
        <button type="submit" class="auth-button" :disabled="isLoading">
          {{ isLoading ? 'Creating Account...' : 'Sign Up' }}
        </button>
        
        <div class="auth-footer">
          <p>Already have an account? <router-link to="/login" class="auth-link">Sign in</router-link></p>
        </div>
      </form>
      
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { authAPI } from '../services/api';

export default {
  name: 'SignUp',
  setup() {
    const email = ref('');
    const username = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const error = ref('');
    const isLoading = ref(false);
    const router = useRouter();
    const { login } = useAuth();

    const handleSignUp = async () => {
      error.value = '';

      if (password.value !== confirmPassword.value) {
        error.value = 'Passwords do not match';
        return;
      }

      if (password.value.length < 6) {
        error.value = 'Password must be at least 6 characters';
        return;
      }

      isLoading.value = true;

      try {
        const res = await authAPI.signup({
          email: email.value,
          username: username.value,
          password: password.value,
        });

        login(res.user, res.access_token);
        router.push('/');
      } catch (err) {
        console.error('Signup error:', err);
        error.value = err.message || 'Signup failed. Please try again.';
      } finally {
        isLoading.value = false;
      }
    };

    return {
      email,
      username,
      password,
      confirmPassword,
      error,
      isLoading,
      handleSignUp,
    };
  }
};
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #024A14 0%, #01350e 100%);
  padding: 20px;
}

.auth-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  font-family: 'Jaro', sans-serif;
  font-size: 36px;
  color: #024A14;
  margin-bottom: 8px;
}

.auth-subtitle {
  color: #666;
  font-size: 16px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Jaldi', sans-serif;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #024A14;
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.auth-button {
  padding: 14px;
  background: #024A14;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  font-family: 'Jaldi', sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;
}

.auth-button:hover {
  background: #01350e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(2, 74, 20, 0.3);
}

.auth-button:active {
  transform: translateY(0);
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #666;
}

.auth-link {
  color: #024A14;
  text-decoration: none;
  font-weight: 600;
}

.auth-link:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: #fee;
  color: #c33;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}
</style>

