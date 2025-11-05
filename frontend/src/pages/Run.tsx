import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import "./styles/Run.css";

const DEFAULT_CODE = `# Write your Python code here
def hello_world():
    print("Hello, World!")
    return "Success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")`;

export default function Run() {
    const navigate = useNavigate();
    const [code, setCode] = useState(DEFAULT_CODE);
    const [output, setOutput] = useState("");
    const [isRunning, setIsRunning] = useState(false);
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
    const location = useLocation();
    const { conversationId, executable, file_name } = location.state || {};

    useEffect(() => {
  console.log("Run.tsx received:", { conversationId, executable, file_name });
}, [conversationId, executable, file_name]);



useEffect(() => {
    console.log("API_BASE", API_BASE)
  const fetchCode = async () => {
    if (!conversationId) return;

    try {
    //   const res = await fetch(`${API_BASE}/conversations/${conversationId}/single`);
    //   const convo = await res.json();
    //   setCode(convo.code);
      const res = await fetch(`${API_BASE}/api/get_runner_code?conversation_id=${conversationId}`);
      const convo = await res.json();
      setCode(convo.code);
    } catch (err) {
      console.error("Failed to load conversation code:", err);
      setCode("");
    }
    // setOutput("placeholder")

    const res = await fetch(`${API_BASE}/api/rerun_command?conversation_id=${conversationId}`, {
  method: "POST",
  headers: { "Accept": "application/json" },
});
const data = await res.json();
setOutput(data.output);

  };

  fetchCode();
}, [conversationId]);



    const handleRun = async () => {
        if (!code.trim()) {
            setOutput("Error: Code editor is empty. Please enter some Python code.\n");
            return;
        }

        setIsRunning(true);
        setOutput("Running code...\n\n");

        try {
      const res = await fetch(`${API_BASE}/api/rerun_command?conversation_id=${conversationId}`, {
  method: "POST",
  headers: { "Accept": "application/json" },
});

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`);
      }

      const data = await res.json();
      console.log("Execute command response:", data);

      // Show backend output (if available)
      if (data.output) {
        setOutput(data.output);
      } else {
        setOutput("No output returned from execute_command.\n");
      }

      // Optionally use backend code result
      // if (data.code) setCode(data.code);

    } catch (err) {
      console.error("Failed to execute command:", err);
      setOutput("Error executing command.\n");
    } finally {
            setIsRunning(false);
        }
    };

    const handleBack = () => {
  if (conversationId) {
    navigate(`/chat?conversationId=${conversationId}`);
  } else {
    navigate("/chat");
  }
};

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
        } catch (err) {
            console.error("Failed to copy code:", err);
        }
    };

    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setCode(text);
        } catch (err) {
            console.error("Failed to paste code:", err);
        }
    };

    const handleClear = () => {
        setCode("");
    };

    return (
        <div className="run__viewport">
            {/* Top bar with back button */}
            <header className="run__header">
                <button className="run__back-btn" onClick={handleBack}>
                    ← Back to Chat
                </button>
            </header>

            {/* Main content: Code editor and output */}
            <main className="run__main">
                {/* Left side: Code editor */}
                <section className="run__editor-section">
                    <div className="run__editor-header">
                        <h2>Code</h2>
                        <button
                            className="run__execute-btn"
                            onClick={handleRun}
                            disabled={isRunning}
                        >
                            {isRunning ? "Running..." : "Run Code"}
                        </button>
                    </div>
                    <div className="run__editor-wrapper">
                        <div className="run__editor-toolbar">
                            <button
                                className="run__toolbar-btn"
                                onClick={handleCopy}
                                aria-label="Copy code"
                                title="Copy code"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
                                    <rect x="4" y="4" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                                </svg>
                            </button>
                            <button
                                className="run__toolbar-btn"
                                onClick={handlePaste}
                                aria-label="Paste code"
                                title="Paste code"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <rect x="8" y="2" width="8" height="4" rx="1" stroke="currentColor" strokeWidth="2" />
                                </svg>
                            </button>
                            <button
                                className="run__toolbar-btn"
                                onClick={handleClear}
                                aria-label="Clear code"
                                title="Clear code"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        </div>
                        <textarea
                            className="run__editor"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                            placeholder="Enter your Python code here..."
                            spellCheck={false}
                        />
                    </div>
                </section>

                {/* Right side: Output */}
                <section className="run__output-section">
                    <div className="run__output-header">
                        <h2>Output</h2>
                        <button
                            className="run__clear-btn"
                            onClick={() => setOutput("")}
                        >
                            Clear
                        </button>
                    </div>
                    <div className="run__output">
                        <pre>{output || "Output will appear here..."}</pre>
                    </div>
                </section>
            </main>
        </div>
    );
}

