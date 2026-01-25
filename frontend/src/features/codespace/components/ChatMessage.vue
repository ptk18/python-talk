<template>
  <div style="display: flex; flex-direction: column; margin-bottom: 12px;">
    <div
      :class="['chat-message', message.sender === 'user' ? 'chat-message--right' : 'chat-message--left']"
      :style="{ alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start' }"
    >
      <div v-if="message.sender !== 'user'" class="chat-message__avatar-container">
        <img :src="scorpioIcon" alt="Scorpio" class="chat-message__avatar" />
        <div class="chat-message__name chat-message__name--left">Scorpio</div>
      </div>
      <span v-if="message.sender === 'user'" class="chat-message__time chat-message__time--left">
        {{ formatTime(message.timestamp) }}
      </span>
      <div class="chat-message__bubble">
        <div v-if="message.content.includes('```')" class="chat-message__code">
          <pre><code>{{ message.content.replace(/```[\s\S]*?\n|```/g, '') }}</code></pre>
        </div>
        <template v-else>
          {{ message.content }}
        </template>
      </div>
      <div v-if="message.sender === 'user'" class="chat-message__avatar-container">
        <img :src="userIcon" alt="User" class="chat-message__avatar" />
        <div class="chat-message__name chat-message__name--right">{{ userName }}</div>
      </div>
      <span v-if="message.sender !== 'user'" class="chat-message__time">
        {{ formatTime(message.timestamp) }}
      </span>
    </div>
  </div>
</template>

<script>
import { formatTime } from '@/shared/utils/formatters'
import scorpioIcon from '@/assets/scorpio.svg'
import userIcon from '@/assets/user.svg'

export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      required: true
    },
    userName: {
      type: String,
      default: 'User'
    }
  },
  setup() {
    return {
      formatTime,
      scorpioIcon,
      userIcon
    }
  }
}
</script>

<style scoped>
.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 70%;
  animation: fadeIn 0.3s ease;
}

.chat-message--left {
  align-self: flex-start;
}

.chat-message--right {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-message__avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.chat-message__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-message__name {
  font-size: 11px;
  color: #999;
  font-family: 'Jaldi', sans-serif;
}

.chat-message__name--left,
.chat-message__name--right {
  text-align: center;
}

.chat-message__bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-family: 'Jaldi', sans-serif;
  font-size: 14px;
  word-wrap: break-word;
  white-space: pre-line;
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.chat-message--right .chat-message__bubble {
  background: var(--color-navy);
  color: white;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}

.chat-message__code {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.chat-message__code pre {
  margin: 0;
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.chat-message__time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  font-family: 'Jaldi', sans-serif;
}

.chat-message__time--left {
  align-self: flex-end;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
