import { Editor } from '@monaco-editor/react';
import { useTheme } from '../theme/ThemeProvider';

interface MonacoEditorProps {
  code: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
  height?: string;
}

export default function MonacoEditor({
  code,
  onChange,
  language = 'python',
  readOnly = false,
  height = '100%'
}: MonacoEditorProps) {
  const { theme } = useTheme();

  return (
    <Editor
      height={height}
      language={language}
      theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
      value={code}
      onChange={onChange}
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
}
