import { useState } from "react";
import Navbar from "../components/Navbar";
import SpeakerIcon from "../assets/speaker_icon.svg";
import { useTheme } from "../theme/ThemeProvider";
import "./styles/Setting.css";

export default function Setting() {
    const [volume, setVolume] = useState(70);
    const [lang, setLang] = useState("en");
    const [notif, setNotif] = useState<"on" | "off">("on");
    const { theme, toggle } = useTheme();
    const lightMode = theme === "light";
    const [bt, setBt] = useState("none");

    return (
        <div className="setting__viewport">
            {/* Top bar */}
            <Navbar rightButton={{ text: "Chat", to: "/chat" }} />

            {/* Panel shell */}
            <main className="setting__main">
                <h1 className="setting__title">Setting</h1>

                <section className="setting__card">
                    {/* Row: Sound */}
                    <div className="row">
                        <div className="row__label">Sound</div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <img src={SpeakerIcon} alt="" className="icon" aria-hidden />
                            <input
                                type="range"
                                min={0}
                                max={100}
                                value={volume}
                                onChange={(e) => setVolume(+e.target.value)}
                                aria-label="Volume"
                                className="range"
                            />
                        </div>
                    </div>

                    {/* Row: Language */}
                    <div className="row">
                        <div className="row__label">Language</div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <div className="select">
                                <select
                                    value={lang}
                                    onChange={(e) => setLang(e.target.value)}
                                    aria-label="Language"
                                >
                                    <option value="en">English</option>
                                    <option value="th">ไทย (Thai)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Row: Notification */}
                    <div className="row">
                        <div className="row__label">Notification</div>
                        <div className="row__sep" />
                        <div className="row__control row__control--radio">
                            <label className="radio">
                                <input
                                    type="radio"
                                    name="notif"
                                    checked={notif === "on"}
                                    onChange={() => setNotif("on")}
                                />
                                <span>On</span>
                            </label>
                            <label className="radio">
                                <input
                                    type="radio"
                                    name="notif"
                                    checked={notif === "off"}
                                    onChange={() => setNotif("off")}
                                />
                                <span>Off</span>
                            </label>
                        </div>
                    </div>

                    {/* Row: Mode */}
                    <div className="row">
                        <div className="row__label">Mode</div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <button
                                type="button"
                                className={`toggle ${lightMode ? "is-on" : ""}`}
                                onClick={toggle}
                                aria-pressed={lightMode}
                                aria-label="Toggle light/dark mode"
                            >
                                <span className="knob" />
                            </button>
                            <span className="modeText">{lightMode ? "Light Mode" : "Dark Mode"}</span>
                        </div>
                    </div>

                    {/* Row: Bluetooth */}
                    <div className="row row--last">
                        <div className="row__label">Bluetooth</div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <div className="select">
                                <select
                                    value={bt}
                                    onChange={(e) => setBt(e.target.value)}
                                    aria-label="Bluetooth"
                                >
                                    <option value="none">Select device…</option>
                                    <option value="earbuds">Earbuds A12</option>
                                    <option value="speaker">Home Speaker</option>
                                    <option value="keyboard">BT Keyboard</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
