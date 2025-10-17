import "./styles/Chat.css";
import Snake from "../assets/scorpio.svg";
import User from "../assets/user.svg";
import RunIcon from "../assets/run.svg";
import ChatIcon from "../assets/chat.svg";
import UploadIcon from "../assets/upload_file.svg";
import Voice from "../assets/voice.svg";

export default function Chat() {
    return (
        <div className="chat__viewport">
            {/* Top bar */}
            <header className="chat__navbar">
                <div className="chat__logo">PyTalk</div>
                <nav className="chat__links">
                    <a href="/" className="is-active">Home</a>
                    <a href="/setting">Setting</a>
                    <a href="/profile">Profile</a>
                </nav>
            </header>

            {/* Chat panel */}
            <main className="chat__panel">
                {/* Left assistant column */}
                <div className="chat__side chat__side--left">
                    <img src={Snake} alt="Scorpio" className="chat__avatar" />
                    <div className="chat__name chat__name--left">Scorpio</div>
                </div>

                {/* Scroll area with messages */}
                <section className="chat__scroll">
                    {/* Assistant bubble (left) */}
                    <div className="chat__row chat__row--left">
                        <div className="chat__bubble">{/* assistant text */}</div>
                        <span className="chat__time">23.10</span>
                    </div>

                    <div style={{ height: 140 }} />

                    {/* User bubble (right) */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.12</span>
                        <div className="chat__bubble">{/* user text */}</div>
                    </div>
                </section>

                {/* Right user column */}
                <div className="chat__side chat__side--right">
                    <img src={User} alt="User" className="chat__avatar" />
                    <div className="chat__name chat__name--right">User</div>
                </div>
            </main>

            {/* Footer actions */}
            <footer className="chat__footer">
                <div className="chat__actions">
                    <button className="btn btn--run">
                        run <img src={RunIcon} alt="" />
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
