import Navbar from "../components/Navbar";
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
                        <div className="chat__bubble">{/* assistant text */}</div>
                        <span className="chat__time">23.10</span>
                    </div>

                    {/* User message 1 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.12</span>
                        <div className="chat__bubble">{/* user text */}</div>
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
                        <div className="chat__bubble">{/* assistant text */}</div>
                        <span className="chat__time">23.15</span>
                    </div>

                    {/* User message 2 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.18</span>
                        <div className="chat__bubble">{/* user text */}</div>
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
                        <div className="chat__bubble">{/* assistant text */}</div>
                        <span className="chat__time">23.20</span>
                    </div>

                    {/* User message 3 */}
                    <div className="chat__row chat__row--right">
                        <span className="chat__time chat__time--left">23.22</span>
                        <div className="chat__bubble">{/* user text */}</div>
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
