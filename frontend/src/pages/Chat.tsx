import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./styles/Chat.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import RunIcon from "../assets/run.svg";
import ChatIcon from "../assets/chat.svg";
import UploadIcon from "../assets/upload_file.svg";
import Voice from "../assets/voice.svg";
import VoiceWhite from "../assets/voice-white.svg";
import { useTheme } from "../theme/ThemeProvider";

export default function Chat() {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [isChatActive, setIsChatActive] = useState(false);
    const [message, setMessage] = useState("");
    const codeSnippet = `def reverse_string(s: str) -> str:\n    """Return the reverse of the input string."""\n    return s[::-1]\n\nif __name__ == "__main__":\n    print(reverse_string("scorpio"))  # oiprocos`;
    const turtleCodeSnippet = `import turtle\n\ndef draw_spiral() -> None:\n    """Draw a colorful spiral using turtle graphics."""\n    colors = ["red", "orange", "yellow", "green", "blue", "purple"]\n    t = turtle.Turtle()\n    t.speed(10)\n    \n    for i in range(100):\n        t.color(colors[i % len(colors)])\n        t.forward(i * 2)\n        t.left(60)\n    \n    turtle.done()\n\nif __name__ == "__main__":\n    draw_spiral()`;
    const voiceIcon = theme === "dark" ? VoiceWhite : Voice;

    const handleChatToggle = () => {
        setIsChatActive(!isChatActive);
    };

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (message.trim()) {
            console.log("Sending message:", message);
            // TODO: Send message logic
            setMessage("");
        }
    };

    const handleRun = () => {
        navigate("/run");
    };

    return (
        <div className="chat__viewport">
            {/* Top bar */}
            <Navbar />

            {/* Chat panel */}
            <main className="chat__panel">
                {/* Scroll area with messages */}
                <section className="chat__scroll">
                    {/* Assistant message 1 */}
                    <div className="chat__row chat__row--left">
                        <div className="chat__avatar-container">
                            <img src={Snake} alt="Scorpio" className="chat__avatar" />
                            <div className="chat__name chat__name--left">Scorpio</div>
                        </div>
                        <div className="chat__bubble">Hello! I'm Scorpio. How can I help you today?</div>
                        <span className="chat__time">23.10</span>
                    </div>

                    {/* User message 1 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.12</span>
                        <div className="chat__bubble">Write a Python function to reverse a string.</div>
                        <div className="chat__avatar-container">
                            <img src={User} alt="User" className="chat__avatar" />
                            <div className="chat__name chat__name--right">User</div>
                        </div>
                    </div>

                    {/* Assistant message 2 */}
                    <div className="chat__row chat__row--left">
                        <div className="chat__avatar-container">
                            <img src={Snake} alt="Scorpio" className="chat__avatar" />
                            <div className="chat__name chat__name--left">Scorpio</div>
                        </div>
                        <div className="chat__bubble">
                            Here is a typed version with a docstring:
                            <div className="chat__code">
                                <button
                                    className="chat__copy-btn"
                                    aria-label="Copy code"
                                    onClick={() => navigator.clipboard.writeText(codeSnippet)}
                                >
                                    {/* simple copy icon */}
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
                                        <rect x="4" y="4" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                                    </svg>
                                </button>
                                <pre>
                                    <code>{codeSnippet}</code>
                                </pre>
                            </div>
                        </div>
                        <span className="chat__time">23.15</span>
                    </div>

                    {/* User message 2 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.18</span>
                        <div className="chat__bubble">Great. Add type hints and a short docstring.</div>
                        <div className="chat__avatar-container">
                            <img src={User} alt="User" className="chat__avatar" />
                            <div className="chat__name chat__name--right">User</div>
                        </div>
                    </div>

                    {/* Assistant message 3 */}
                    <div className="chat__row chat__row--left">
                        <div className="chat__avatar-container">
                            <img src={Snake} alt="Scorpio" className="chat__avatar" />
                            <div className="chat__name chat__name--left">Scorpio</div>
                        </div>
                        <div className="chat__bubble">Done. I also included a quick example call to verify the output.</div>
                        <span className="chat__time">23.20</span>
                    </div>

                    {/* User message 3 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.22</span>
                        <div className="chat__bubble">Perfect, thanks! That works.</div>
                        <div className="chat__avatar-container">
                            <img src={User} alt="User" className="chat__avatar" />
                            <div className="chat__name chat__name--right">User</div>
                        </div>
                    </div>

                    {/* User message 4 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.25</span>
                        <div className="chat__bubble">Can you create a Python program that shows turtle graphics output?</div>
                        <div className="chat__avatar-container">
                            <img src={User} alt="User" className="chat__avatar" />
                            <div className="chat__name chat__name--right">User</div>
                        </div>
                    </div>

                    {/* Assistant message 4 */}
                    <div className="chat__row chat__row--left">
                        <div className="chat__avatar-container">
                            <img src={Snake} alt="Scorpio" className="chat__avatar" />
                            <div className="chat__name chat__name--left">Scorpio</div>
                        </div>
                        <div className="chat__bubble">
                            Sure! Here's a colorful spiral using turtle graphics. When you run it, a window will open showing the turtle drawing:
                            <div className="chat__code">
                                <button
                                    className="chat__copy-btn"
                                    aria-label="Copy code"
                                    onClick={() => navigator.clipboard.writeText(turtleCodeSnippet)}
                                >
                                    {/* simple copy icon */}
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
                                        <rect x="4" y="4" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                                    </svg>
                                </button>
                                <pre>
                                    <code>{turtleCodeSnippet}</code>
                                </pre>
                            </div>
                        </div>
                        <span className="chat__time">23.27</span>
                    </div>
                </section>
            </main>

            {/* Footer actions */}
            <footer className="chat__footer">
                <div className="chat__actions">
                    <button className="btn btn--run" onClick={handleRun}>
                        Run <img src={RunIcon} alt="" />
                    </button>
                    <button
                        className={`btn ${isChatActive ? "btn--active" : ""}`}
                        onClick={handleChatToggle}
                    >
                        Chat <img src={ChatIcon} alt="" />
                    </button>
                    <button className="btn btn--upload">
                        Upload File <img src={UploadIcon} alt="" />
                    </button>
                </div>
            </footer>

            {/* Chat input container (shown when chat is active) */}
            {isChatActive && (
                <div className="chat__input-container">
                    <img
                        src={voiceIcon}
                        alt="Start voice input"
                        className="chat__mic chat__mic--small"
                    />
                    <form className="chat__input-form" onSubmit={handleSend}>
                        <input
                            type="text"
                            className="chat__input"
                            placeholder="Type your message..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            autoFocus
                        />
                        <button
                            type="submit"
                            className="chat__send-btn"
                        >
                            Send
                        </button>
                    </form>
                </div>
            )}

            {/* Floating voice button (shown when chat is inactive) */}
            {!isChatActive && (
                <img
                    src={voiceIcon}
                    alt="Start voice input"
                    className="chat__mic"
                />
            )}
        </div>
    );
}
