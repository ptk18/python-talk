import { ref, computed } from 'vue';

const user = ref(null);
const token = ref(null);

const savedUser = localStorage.getItem('auth_user');
const savedToken = localStorage.getItem('auth_token');

if (savedUser) {
  user.value = JSON.parse(savedUser);
}
if (savedToken) {
  token.value = savedToken;
}

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value);

  const login = (userData, authToken) => {
    user.value = userData;
    token.value = authToken || null;

    localStorage.setItem('auth_user', JSON.stringify(userData));
    if (authToken) {
      localStorage.setItem('auth_token', authToken);
    }
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
  };
}
