import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import "./styles/turtleTest.css";
import { speak } from "../utils/tts";

const API_BASE = "https://161.246.5.67:8001";
const WS_BASE_URL = "wss://161.246.5.67:5050";

export default function TurtleTest() {
  const location = useLocation();
  const { conversationId: rawConversationId } = location.state || {};
  const conversationId = rawConversationId || "test123";
  
  const [fileName, setFileName] = useState("");
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [listening, setListening] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);

  /* -------------------- START TURTLE -------------------- */
  useEffect(() => {
    fetch(`${API_BASE}/start_turtle/${conversationId}`, {
      method: "POST",
    }).catch(console.error);
  }, [conversationId]);

  /* -------------------- WEBSOCKET -------------------- */
  useEffect(() => {
    const wsUrl = `${WS_BASE_URL}/subscribe/${conversationId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");

    ws.onmessage = (event) => {
      setWsStatus("receiving");
      const img = document.getElementById("turtle-stream") as HTMLImageElement;
      if (img) {
        img.src = "data:image/jpeg;base64," + event.data;
      }
    };

    ws.onerror = () => setWsStatus("error");
    ws.onclose = () => setWsStatus("disconnected");

    return () => ws.close();
  }, [conversationId]);

  /* -------------------- SPEECH RECOGNITION -------------------- */
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition not supported");
      return;
    }

    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);

    recognition.onresult = async (event: any) => {
      const command = event.results[0][0].transcript;
      speak(command);
      await sendCommand(command);
    };

    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  };

  /* -------------------- SEND COMMAND -------------------- */
  const sendCommand = async (command: string) => {
    try {
      await fetch(`${API_BASE}/turtle_command/${conversationId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
    } catch (err) {
      console.error("Command failed", err);
    }
  };

  /* -------------------- FILE RESET -------------------- */
  const handleSubmitFile = async () => {
    if (!fileName.trim()) return;

    await fetch(`${API_BASE}/kill/${conversationId}`, { method: "POST" });
    await fetch(`${API_BASE}/start_turtle/${conversationId}`, {
      method: "POST",
    });

    speak("New turtle session started");
    setFileName("");
  };

  return (
    <div className="turtle-test">
      <header className="turtle-header">
        <h2>🐢 Turtle Live Control</h2>

        <div className="file-row">
          <input
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
            placeholder="Session file name"
          />
          <button onClick={handleSubmitFile}>Start New</button>
        </div>
      </header>

      <div className="turtle-canvas">
        <img id="turtle-stream" alt="Turtle Stream" />
        <div className="ws-status">{wsStatus}</div>
      </div>

      <footer className="turtle-footer">
        <button
          className={`mic-btn ${listening ? "active" : ""}`}
          onClick={startListening}
        >
          🎤
        </button>
        <p>Say commands like: “move up 100”, “turn left”, “reset”</p>
      </footer>
    </div>
  );
}
