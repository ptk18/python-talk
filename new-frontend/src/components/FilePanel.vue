<template>
  <div class="file-panel">
    <button
      class="file-panel__toggle"
      @click="isOpen = !isOpen"
      :title="isOpen ? 'Close file panel' : 'Open file panel'"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-if="!isOpen">Files</span>
    </button>

    <div v-if="isOpen" class="file-panel__dropdown">
      <div class="file-panel__header">
        <h3>Files</h3>
        <button @click="handleCreateFile" class="file-panel__create-btn" title="Create new file">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="file-panel__list">
        <div
          v-for="file in files"
          :key="file"
          :class="['file-panel__item', { 'file-panel__item--active': file === currentFile }]"
          @click="handleFileClick(file)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9l-7-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 2v7h7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="file-panel__filename">{{ file }}</span>
          <button
            v-if="file !== 'runner.py'"
            @click.stop="handleDeleteFile(file)"
            class="file-panel__delete-btn"
            title="Delete file"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import { useFile } from '../composables/useFile';
import { voiceService } from '../services/voiceService';

export default {
  name: 'FilePanel',
  props: {
    conversationId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const { files, currentFile, loadFiles, loadFile, deleteFile } = useFile();
    const isOpen = ref(false);

    watch(() => props.conversationId, async (newId) => {
      if (newId) {
        await loadFiles(newId);
      }
    }, { immediate: true });

    const handleFileClick = async (filename) => {
      try {
        await loadFile(props.conversationId, filename);
        isOpen.value = false;
      } catch (err) {
        console.error('Failed to load file:', err);
      }
    };

    const handleCreateFile = async () => {
      const filename = prompt('Enter new file name (e.g., my_module.py):');
      if (!filename) return;

      if (!filename.endsWith('.py')) {
        alert('File must have .py extension');
        return;
      }

      if (files.value.includes(filename)) {
        alert('File already exists');
        return;
      }

      try {
        const { saveFile } = useFile();
        await saveFile(props.conversationId, filename, '');
        await loadFiles(props.conversationId);
        await loadFile(props.conversationId, filename);
        voiceService.speak('File created successfully');
      } catch (err) {
        console.error('Failed to create file:', err);
        voiceService.speak('Failed to create file');
      }
    };

    const handleDeleteFile = async (filename) => {
      if (!confirm(`Delete ${filename}?`)) return;

      try {
        await deleteFile(props.conversationId, filename);
        voiceService.speak('File deleted successfully');
      } catch (err) {
        console.error('Failed to delete file:', err);
        voiceService.speak('Failed to delete file');
      }
    };

    return {
      isOpen,
      files,
      currentFile,
      handleFileClick,
      handleCreateFile,
      handleDeleteFile,
    };
  }
};
</script>

<style scoped>
.file-panel {
  position: relative;
  margin-right: 1rem;
}

.file-panel__toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--primary-color, #024A14);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.file-panel__toggle:hover {
  background: var(--primary-dark, #013610);
}

.file-panel__dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  min-width: 250px;
  max-height: 400px;
  overflow-y: auto;
  z-index: 10;
}

.file-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
}

.file-panel__header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.file-panel__create-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--primary-color, #024A14);
  padding: 0.25rem;
  display: flex;
  align-items: center;
  transition: transform 0.2s;
}

.file-panel__create-btn:hover {
  transform: scale(1.1);
}

.file-panel__list {
  padding: 0.5rem 0;
}

.file-panel__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.2s;
  color: #333;
}

.file-panel__item:hover {
  background: #f5f5f5;
}

.file-panel__item--active {
  background: #e8f5e9;
  color: var(--primary-color, #024A14);
  font-weight: 600;
}

.file-panel__filename {
  flex: 1;
  font-size: 14px;
}

.file-panel__delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #d32f2f;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.file-panel__item:hover .file-panel__delete-btn {
  opacity: 1;
}

.file-panel__delete-btn:hover {
  color: #b71c1c;
}
</style>
