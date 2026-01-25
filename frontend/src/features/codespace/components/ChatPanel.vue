<template>
  <main class="chat-panel">
    <section class="chat-panel__scroll">
      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :user-name="userName"
      />
    </section>

    <footer class="chat-panel__footer">
      <div class="chat-panel__input-container">
        <VoiceInput
          :is-recording="isRecording"
          @click="$emit('mic-click')"
        />

        <form class="chat-panel__form" @submit.prevent="handleSubmit">
          <input
            type="text"
            class="chat-panel__input"
            :placeholder="placeholder"
            v-model="inputValue"
          />
          <button type="submit" class="chat-panel__send-btn" aria-label="Send message">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"/>
            </svg>
          </button>
        </form>
      </div>
    </footer>
  </main>
</template>

<script>
import { ref, watch } from 'vue'
import ChatMessage from './ChatMessage.vue'
import VoiceInput from './VoiceInput.vue'

export default {
  name: 'ChatPanel',
  components: {
    ChatMessage,
    VoiceInput
  },
  props: {
    messages: {
      type: Array,
      default: () => []
    },
    userName: {
      type: String,
      default: 'User'
    },
    isRecording: {
      type: Boolean,
      default: false
    },
    placeholder: {
      type: String,
      default: 'Type your message...'
    },
    modelValue: {
      type: String,
      default: ''
    }
  },
  emits: ['send', 'mic-click', 'update:modelValue'],
  setup(props, { emit }) {
    const inputValue = ref(props.modelValue)

    watch(() => props.modelValue, (newVal) => {
      inputValue.value = newVal
    })

    watch(inputValue, (newVal) => {
      emit('update:modelValue', newVal)
    })

    const handleSubmit = () => {
      if (inputValue.value.trim()) {
        emit('send', inputValue.value.trim())
        inputValue.value = ''
      }
    }

    return {
      inputValue,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid var(--color-border);
  min-width: 0;
  min-height: 0;
  max-height: 100%;
}

.chat-panel__scroll {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.chat-panel__footer {
  border-top: 1px solid var(--color-border);
  padding: 24px;
  background: var(--color-bg);
}

.chat-panel__input-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-panel__form {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-panel__input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid var(--color-border);
  border-radius: 24px;
  font-size: var(--font-size-body);
  font-family: var(--font-family);
  transition: all 0.2s ease;
  outline: none;
}

.chat-panel__input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.chat-panel__send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-primary);
  color: white;
  flex-shrink: 0;
}

.chat-panel__send-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: scale(1.05);
}

.chat-panel__send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.chat-panel__scroll::-webkit-scrollbar {
  width: 8px;
}

.chat-panel__scroll::-webkit-scrollbar-track {
  background: transparent;
}

.chat-panel__scroll::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.chat-panel__scroll::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}
</style>
