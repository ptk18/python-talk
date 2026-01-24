import { ref } from 'vue';
import { fileAPI } from '@py-talk/shared';

const currentFile = ref('');
const currentCode = ref('');
const files = ref([]);

export function useFile() {
  const setCurrentFile = (filename) => {
    currentFile.value = filename;
  };

  const setCurrentCode = (code) => {
    currentCode.value = code;
  };

  const loadFiles = async (conversationId) => {
    try {
      const response = await fileAPI.listFiles(conversationId);
      files.value = response.files || [];
    } catch (err) {
      console.error('Failed to load files:', err);
      files.value = [];
    }
  };

  const loadFile = async (conversationId, filename) => {
    try {
      const response = await fileAPI.getFile(conversationId, filename);
      currentFile.value = filename;
      currentCode.value = response.code || '';
    } catch (err) {
      console.error('Failed to load file:', err);
      currentCode.value = '';
    }
  };

  const saveFile = async (conversationId, filename, code) => {
    try {
      await fileAPI.saveFile(conversationId, filename, code);
    } catch (err) {
      console.error('Failed to save file:', err);
      throw err;
    }
  };

  const deleteFile = async (conversationId, filename) => {
    try {
      await fileAPI.deleteFile(conversationId, filename);
      await loadFiles(conversationId);
    } catch (err) {
      console.error('Failed to delete file:', err);
      throw err;
    }
  };

  const clearFileState = () => {
    currentFile.value = '';
    currentCode.value = '';
    files.value = [];
  };

  return {
    currentFile,
    currentCode,
    files,
    setCurrentFile,
    setCurrentCode,
    loadFiles,
    loadFile,
    saveFile,
    deleteFile,
    clearFileState,
  };
}
