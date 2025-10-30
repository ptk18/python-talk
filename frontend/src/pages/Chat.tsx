import Navbar from "../components/Navbar";
import "./styles/Chat.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import RunIcon from "../assets/run.svg";
import ChatIcon from "../assets/chat.svg";
import UploadIcon from "../assets/upload_file.svg";
import Voice from "../assets/voice.svg";

export default function Chat() {
    const codeSnippet = `def reverse_string(s: str) -> str:\n    """Return the reverse of the input string."""\n    return s[::-1]\n\nif __name__ == "__main__":\n    print(reverse_string("scorpio"))  # oiprocos`;
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
                </section>
            </main>

            {/* Footer actions */}
            <footer className="chat__footer">
                <div className="chat__actions">
                    <button className="btn btn--run">
                        Run <img src={RunIcon} alt="" />
                    </button>
                    <button className="btn">
                        Chat <img src={ChatIcon} alt="" />
                    </button>
                    <button className="btn btn--upload">
                        Upload File <img src={UploadIcon} alt="" />
                    </button>
                </div>
            </footer>

            {/* Floating voice button */}
            <img
                src={Voice}
                alt="Start voice input"
                className="chat__mic"
            />
        </div>
    );
}
