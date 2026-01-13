import { ref } from 'vue';
import { executeAPI } from '../services/api';

const code = ref('');
const conversationId = ref(null);

export function useCode() {
  const setCode = (newCode) => {
    code.value = newCode;
  };

  const setConversationId = (id) => {
    conversationId.value = id;
  };

  const syncCodeFromBackend = async () => {
    if (!conversationId.value) return;

    try {
      const response = await executeAPI.getRunnerCode(conversationId.value);
      code.value = response.code || '';
    } catch (err) {
      console.error('Failed to sync code from backend:', err);
    }
  };

  return {
    code,
    conversationId,
    setCode,
    setConversationId,
    syncCodeFromBackend,
  };
}
