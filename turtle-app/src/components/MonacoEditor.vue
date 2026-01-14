<template>
  <div ref="editorContainer" class="monaco-editor-container"></div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import loader from '@monaco-editor/loader';

export default {
  name: 'MonacoEditor',
  props: {
    code: {
      type: String,
      default: ''
    },
    language: {
      type: String,
      default: 'python'
    }
  },
  emits: ['update:code', 'change'],
  setup(props, { emit, expose }) {
    const editorContainer = ref(null);
    let editor = null;
    let isUpdatingFromProp = false;

    onMounted(async () => {
      const monaco = await loader.init();

      if (!editorContainer.value) return;

      editor = monaco.editor.create(editorContainer.value, {
        value: props.code,
        language: props.language,
        theme: 'vs-dark',
        automaticLayout: true,
        fontSize: 14,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        tabSize: 4,
      });

      editor.onDidChangeModelContent(() => {
        if (!isUpdatingFromProp) {
          const value = editor.getValue();
          emit('update:code', value);
          emit('change', value);
        }
      });
    });

    watch(() => props.code, (newCode) => {
      if (editor && editor.getValue() !== newCode) {
        isUpdatingFromProp = true;
        editor.setValue(newCode || '');
        isUpdatingFromProp = false;
      }
    });

    onUnmounted(() => {
      if (editor) {
        editor.dispose();
      }
    });

    const undo = () => {
      if (editor) {
        editor.trigger('keyboard', 'undo', null);
      }
    };

    const redo = () => {
      if (editor) {
        editor.trigger('keyboard', 'redo', null);
      }
    };

    const getPosition = () => {
      if (editor) {
        return editor.getPosition();
      }
      return null;
    };

    const insertText = (text, position) => {
      if (editor) {
        const range = {
          startLineNumber: position.lineNumber,
          startColumn: position.column,
          endLineNumber: position.lineNumber,
          endColumn: position.column
        };
        editor.executeEdits('', [{
          range: range,
          text: text,
          forceMoveMarkers: true
        }]);
        editor.focus();
      }
    };

    expose({ undo, redo, getPosition, insertText });

    return {
      editorContainer,
    };
  }
};
</script>

<style scoped>
.monaco-editor-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}
</style>
