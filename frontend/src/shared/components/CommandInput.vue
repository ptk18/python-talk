<template>
  <section class="command-input">
    <div class="command-input__row">
      <div
        :class="['command-input__mic', { 'command-input__mic--recording': isRecording }]"
        @click="$emit('mic-click')"
      >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z"
            fill="currentColor"
          />
          <path
            d="M17 11C17 13.76 14.76 16 12 16C9.24 16 7 13.76 7 11H5C5 14.53 7.61 17.43 11 17.92V21H13V17.92C16.39 17.43 19 14.53 19 11H17Z"
            fill="currentColor"
          />
        </svg>
      </div>
      <input
        type="text"
        class="command-input__text"
        :placeholder="placeholder"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter.prevent="handleSubmit"
        :disabled="disabled"
      />
      <button
        class="command-input__run-btn"
        @click="handleSubmit"
        :disabled="isProcessing || disabled"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M5 3l14 9-14 9V3z" fill="currentColor"/>
        </svg>
      </button>
    </div>
  </section>
</template>

<script>
export default {
  name: 'CommandInput',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: 'Type a command or speak...'
    },
    isRecording: {
      type: Boolean,
      default: false
    },
    isProcessing: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'submit', 'mic-click'],
  setup(props, { emit }) {
    const handleSubmit = () => {
      if (props.modelValue.trim() && !props.isProcessing && !props.disabled) {
        emit('submit', props.modelValue.trim())
      }
    }

    return { handleSubmit }
  }
}
</script>

<style scoped>
.command-input {
  background: var(--color-surface, white);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.command-input__row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}

.command-input__mic {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.command-input__mic svg {
  width: 20px;
  height: 20px;
  color: white;
}

.command-input__mic:hover {
  background: var(--color-primary-dark, #013a10);
  transform: scale(1.05);
}

.command-input__mic--recording {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}

.command-input__text {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  transition: all 0.2s;
  background: white;
}

.command-input__text:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(2, 74, 20, 0.1);
}

.command-input__text::placeholder {
  color: #999;
  font-family: var(--font-family, 'Jaldi', sans-serif);
}

.command-input__text:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.command-input__run-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.command-input__run-btn:hover:not(:disabled) {
  background: var(--color-primary-dark, #013a10);
  transform: scale(1.05);
}

.command-input__run-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(220, 53, 69, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
}

@media (max-width: 768px) {
  .command-input__row {
    flex-wrap: wrap;
  }

  .command-input__text {
    width: 100%;
    order: -1;
    flex-basis: 100%;
  }
}
</style>
