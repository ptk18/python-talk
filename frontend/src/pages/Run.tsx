import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import "./styles/Run.css";
import { speak } from "../utils/tts";

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
    const [isTurtleCode, setIsTurtleCode] = useState<boolean | null>(null);
    const [showTurtlePrompt, setShowTurtlePrompt] = useState(false);
    const [wsStatus, setWsStatus] = useState('disconnected');
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
    const TURTLE_BASE = import.meta.env.VITE_WS_BASE_URL;
    const GUI_BASE = "wss://161.246.5.67:5050";
    const PI_API_BASE = "https://161.246.5.67:8001";
    const location = useLocation();
    const { conversationId: rawConversationId, executable, file_name } = location.state || {};
    
    // Use provided conversationId or fallback to "test123" for testing
    const conversationId = rawConversationId || "test123";

    useEffect(() => {
  console.log("Run.tsx received:", { conversationId, executable, file_name });
}, [conversationId, executable, file_name]);

    // WebSocket connection for turtle graphics streaming
    useEffect(() => {
        if (!isTurtleCode || !conversationId) return;

        console.log('Setting up WebSocket for turtle graphics...', { isTurtleCode, conversationId });
        
        // const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL;
        const WS_BASE_URL = "wss://161.246.5.67:5050";
        console.log('WS_BASE_URL:', WS_BASE_URL);

        if (!WS_BASE_URL) {
            console.error('VITE_WS_BASE_URL not configured');
            return;
        }        
        const wsUrl = `wss://161.246.5.67:5050/subscribe/${conversationId}`;
        console.log('WebSocket URL:', wsUrl);
        
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected for turtle graphics');
            setWsStatus('connected');
        };

        ws.onmessage = (event) => {
            console.log('Received WebSocket message for turtle graphics');
            setWsStatus('receiving');
            const image = event.data; // base64 string
            const videoElement = document.getElementById('turtle-video') as HTMLImageElement;
            if (videoElement) {
                videoElement.src = 'data:image/jpeg;base64,' + image;
                console.log('Updated turtle video element');
            } else {
                console.error('Turtle video element not found');
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setWsStatus('error');
        };

        ws.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            setWsStatus('disconnected');
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                console.log('Closing WebSocket connection');
                ws.close();
            }
        };
    }, [isTurtleCode, conversationId]);



useEffect(() => {
    console.log("API_BASE", import.meta.env.VITE_API_BASE_URL)
    console.log("GUI_BASE", GUI_BASE)
  const fetchCode = async () => {
    if (!conversationId) return;

    try {
    //   const res = await fetch(`${API_BASE}/conversations/${conversationId}/single`);
    //   const convo = await res.json();
    //   setCode(convo.code);
      const res = await fetch(`${API_BASE}/get_runner_code?conversation_id=${conversationId}`);
      const convo = await res.json();
      setCode(convo.code);
    } catch (err) {
      console.error("Failed to load conversation code:", err);
      setCode("");
    }
    // setOutput("placeholder")

//     const res = await fetch(`${API_BASE}/rerun_command?conversation_id=${conversationId}`, {
//   method: "POST",
//   headers: { "Accept": "application/json" },
// });
// const data = await res.json();
setOutput("Output will appear here...");

  };

  fetchCode();
}, [conversationId]);



    const handleRunTurtle = async () => {
    setIsRunning(true);
    setOutput("Running turtle graphics...\n");

    try {
        console.log("========== TURTLE RUN START ==========");

        /* ---------------- STEP 1: GET runner.py ---------------- */
        console.log("[STEP 1] Fetching runner.py");

        const runnerRes = await fetch(
            `${API_BASE}/get_runner_code?conversation_id=${conversationId}`
        );

        if (!runnerRes.ok) {
            throw new Error("Failed to fetch runner.py");
        }

        const runnerData = await runnerRes.json();
        const runnerCode = runnerData.code;

        console.log("[STEP 1 OK] runner.py received");
        console.log("runner.py preview:\n", runnerCode);

        /* ---------------- STEP 1.5: PATCH runner.py SCREEN SETUP ---------------- */
        console.log("[STEP 1.5] Patching runner.py screen setup");

        let patchedRunnerCode = runnerCode;

        // Only patch if turtle is used and screen setup not already present
        if (
            patchedRunnerCode.includes("turtle") &&
            !patchedRunnerCode.includes("screen.setup(")
        ) {
            // inject AFTER object creation (safe spot)
            patchedRunnerCode = patchedRunnerCode.replace(
                /(obj\s*=\s*.*\n)/,
                `$1\n# --- injected screen setup ---\n` +
                `import turtle as t\n` +
                `screen = t.Screen()\n` +
                `screen.setup(800, 800, 50, 50)\n` +
                `screen.screensize(700, 700)\n` +
                `# --- end injected screen setup ---\n`
            );

            console.log("[STEP 1.5 OK] Screen setup injected into runner.py");
        } else {
            console.log("[STEP 1.5 SKIPPED] Screen setup already exists or turtle not detected");
        }

        // IMPORTANT: use patchedRunnerCode from now on
        /* ---------------- STEP 2: GET turtle module ---------------- */
        console.log("[STEP 2] Fetching turtle class file");

        const turtleRes = await fetch(
            `${API_BASE}/conversations/${conversationId}/single`
        );

        if (!turtleRes.ok) {
            throw new Error("Failed to fetch turtle code");
        }

        const turtleData = await turtleRes.json();
        const turtleCode = turtleData.code;
        const turtleFileName = turtleData.file_name; 
        // expected: turtle_simplehome.py

        console.log("[STEP 2 OK] Turtle file received");
        console.log("Filename:", turtleFileName);
        console.log("Turtle code preview:\n", turtleCode.substring(0, 300));

        /* ---------------- STEP 2.5: FIX MODULE NAME MISMATCH ---------------- */
        console.log("[STEP 2.5] Fixing filename mismatch if needed");

        // extract module name from runner.py import
        const importMatch = patchedRunnerCode.match(
            /from\s+([a-zA-Z0-9_]+)\s+import|import\s+([a-zA-Z0-9_]+)/
        );

        let finalTurtleFileName = turtleFileName;

        if (importMatch) {
            const importedModule = importMatch[1] || importMatch[2];
            const expectedFileName = `${importedModule}.py`;

            if (expectedFileName !== turtleFileName) {
                console.warn(
                    `[FIX] Renaming ${turtleFileName} → ${expectedFileName}`
                );
                finalTurtleFileName = expectedFileName;
            }
        }

        console.log("[STEP 2.5 OK] Final turtle filename:", finalTurtleFileName);


        /* ---------------- STEP 3: BUILD FILES ---------------- */
        console.log("[STEP 3] Building files payload");

        const files: Record<string, string> = {
            "runner.py": patchedRunnerCode,
            [finalTurtleFileName]: turtleCode,
        };

        console.log("[FILES TO SEND]", Object.keys(files));

        /* ---------------- STEP 4: SEND TO PI ---------------- */
        console.log("[STEP 4] Sending files to Pi");

        const piRes = await fetch(
            `${PI_API_BASE}/runturtle/${conversationId}`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ files }),
            }
        );

        if (!piRes.ok) {
            const text = await piRes.text();
            throw new Error(`Pi error ${piRes.status}: ${text}`);
        }

        const piData = await piRes.json();
        console.log("[STEP 4 OK] Pi response:", piData);

        setIsTurtleCode(true);
        setOutput("Turtle graphics started.\n");
        speak("Turtle graphics started");

        console.log("========== TURTLE RUN SUCCESS ==========");

    } catch (err) {
        console.error("========== TURTLE RUN FAILED ==========");
        console.error(err);
        setOutput("Error executing turtle graphics.\n");
        speak("Please try again");
    } finally {
        setIsRunning(false);
    }
};



    const handleRunNormalCode = async () => {
        setIsRunning(true);
        setOutput("Running code...\n\n");

        try {
            const res = await fetch(`${API_BASE}/rerun_command?conversation_id=${conversationId}`, {
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
            speak("Your output is ready, Sir");
        } catch (err) {
            console.error("Failed to execute command:", err);
            setOutput("Error executing command.\n");
            speak("Please try again");
        } finally {
            setIsRunning(false);
        }
    };

    const handleRun = async () => {
        if (!code.trim()) {
            const errorMsg = "Error: Code editor is empty. Please enter some Python code.";
            setOutput(errorMsg + "\n");
            speak("Code editor is empty. Please enter some Python code");
            return;
        }

        // Show turtle code prompt if user hasn't decided yet
        if (isTurtleCode === null) {
            setShowTurtlePrompt(true);
            speak("Is this turtle code?");
            return;
        }

        if (isTurtleCode) {
            await handleRunTurtle();
        } else {
            await handleRunNormalCode();
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
            {/* Turtle Code Prompt Modal */}
            {showTurtlePrompt && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: 'white',
                        padding: '30px',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                        maxWidth: '400px'
                    }}>
                        <h3 style={{ marginTop: 0 }}>Is this Turtle Code?</h3>
                        <p>Does this code use Python turtle graphics?</p>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                            <button
                                onClick={() => {
                                    setIsTurtleCode(true);
                                    setShowTurtlePrompt(false);
                                    handleRunTurtle();
                                }}
                                style={{
                                    flex: 1,
                                    padding: '10px',
                                    backgroundColor: '#4CAF50',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer'
                                }}
                            >
                                Yes, Turtle Code
                            </button>
                            <button
                                onClick={() => {
                                    setIsTurtleCode(false);
                                    setShowTurtlePrompt(false);
                                    // Run normal code
                                    handleRunNormalCode();
                                }}
                                style={{
                                    flex: 1,
                                    padding: '10px',
                                    backgroundColor: '#f44336',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer'
                                }}
                            >
                                No, Normal Code
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Top bar with back button */}
            <header className="run__header">
                <button className="run__back-btn" onClick={handleBack}>
                    ← Back to Chat
                </button>
                <button
                    style={{
                        padding: '8px 16px',
                        backgroundColor: '#ff9800',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        marginLeft: '10px'
                    }}
                    onClick={() => {
                        setIsTurtleCode(null);
                        setShowTurtlePrompt(true);
                        speak("Is this turtle code?");
                    }}
                >
                    Is this turtle code?
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
                        {isTurtleCode ? (
                            <div style={{ 
                                width: '100%', 
                                height: '100%', 
                                display: 'flex', 
                                flexDirection: 'column',
                                alignItems: 'center', 
                                justifyContent: 'center',
                                backgroundColor: '#f5f5f5',
                                border: '2px dashed #ccc',
                                borderRadius: '8px'
                            }}>
                                <div style={{ marginBottom: '10px', color: '#666' }}>
                                    🐢 Turtle Graphics Stream
                                </div>
                                <img
                                    id="turtle-video"
                                    style={{ 
                                        maxWidth: '100%', 
                                        maxHeight: '80%',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        backgroundColor: 'white'
                                    }}
                                    alt="Turtle graphics stream"
                                    onError={(e) => console.error('Image load error:', e)}
                                    onLoad={() => console.log('Turtle image loaded successfully')}
                                />
                                <div style={{ marginTop: '10px', fontSize: '12px', color: '#999' }}>
                                    WebSocket Status: <span style={{ 
                                        color: wsStatus === 'connected' ? 'green' : 
                                              wsStatus === 'receiving' ? 'blue' : 
                                              wsStatus === 'error' ? 'red' : 'orange' 
                                    }}>
                                        {wsStatus}
                                    </span>
                                    {wsStatus === 'connected' && ' (Ready for stream)'}
                                    {wsStatus === 'receiving' && ' (Receiving images)'}
                                </div>
                            </div>
                        ) : (
                            <pre>{output || "Output will appear here..."}</pre>
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
}