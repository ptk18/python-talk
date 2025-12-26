import { Editor } from '@monaco-editor/react';
import { useTheme } from '../theme/ThemeProvider';
import { useRef, useImperativeHandle, forwardRef, useEffect } from 'react';

interface MonacoEditorProps {
  code: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
  height?: string;
}

export interface MonacoEditorRef {
  undo: () => void;
  redo: () => void;
  getValue: () => string | undefined;
}

const MonacoEditor = forwardRef<MonacoEditorRef, MonacoEditorProps>(({
  code,
  onChange,
  language = 'python',
  readOnly = false,
  height = '100%'
}, ref) => {
  const { theme } = useTheme();
  const editorRef = useRef<any>(null);
  const isUpdatingFromProps = useRef(false);

  useImperativeHandle(ref, () => ({
    undo: () => {
      editorRef.current?.trigger('keyboard', 'undo', null);
    },
    redo: () => {
      editorRef.current?.trigger('keyboard', 'redo', null);
    },
    getValue: () => {
      return editorRef.current?.getValue();
    }
  }));

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  // Update editor content when code prop changes from outside
  useEffect(() => {
    if (editorRef.current && code !== editorRef.current.getValue()) {
      isUpdatingFromProps.current = true;
      const position = editorRef.current.getPosition();
      editorRef.current.setValue(code);
      if (position) {
        editorRef.current.setPosition(position);
      }
      isUpdatingFromProps.current = false;
    }
  }, [code]);

  const handleChange = (value: string | undefined) => {
    // Only call onChange if the change came from user interaction, not from props update
    if (!isUpdatingFromProps.current) {
      onChange(value);
    }
  };

  return (
    <Editor
      height={height}
      language={language}
      theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
      defaultValue={code}
      onChange={handleChange}
      onMount={handleEditorDidMount}
      options={{
        readOnly,
        minimap: { enabled: true },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        insertSpaces: true,
        wordWrap: 'on',
        formatOnPaste: true,
        formatOnType: true,
      }}
    />
  );
});

MonacoEditor.displayName = 'MonacoEditor';

export default MonacoEditor;
