import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import SpeakerIcon from "../assets/speaker_icon.svg";
import { voiceService } from "../services/voiceService";
import "./styles/Setting.css";

export default function Setting() {
    const [volume, setVolume] = useState(70);
    const [lang, setLang] = useState("en");
    const [bt, setBt] = useState("none");
    const [voiceEngine, setVoiceEngine] = useState<string>('standard');

    // Apply volume changes to actual audio elements
    useEffect(() => {
        const audioElements = document.querySelectorAll<HTMLAudioElement>('audio');
        audioElements.forEach(audio => {
            audio.volume = volume / 100;
        });
        localStorage.setItem('pytalk_volume', volume.toString());
    }, [volume]);

    useEffect(() => {
        const savedEngine = localStorage.getItem('pytalk_voice_engine');
        if (savedEngine === 'google' || savedEngine === 'standard') {
            voiceService.setEngine(savedEngine);
            setVoiceEngine(savedEngine);
        } else {
            setVoiceEngine('standard');
        }

        const savedVolume = localStorage.getItem('pytalk_volume');
        if (savedVolume) {
            setVolume(Number(savedVolume));
        }
    }, []);

    const handleVoiceEngineChange = async (engine: string) => {
        setVoiceEngine(engine);
        voiceService.setEngine(engine as 'standard' | 'google');

        if (engine === 'google') {
            const isAvailable = await voiceService.checkGoogleAvailability();

            if (!isAvailable) {
                alert('Google Speech API is not available. Falling back to Standard Voice (Female).');
                setVoiceEngine('standard');
                voiceService.setEngine('standard');
                voiceService.speak("Falling back to standard voice");
                return;
            }

            try {
                await voiceService.speak("Voice engine switched to Google Speech. Male voice activated.");
                alert('Voice engine switched to Google Speech (Male Voice)');
            } catch (error) {
                alert('Error switching to Google Speech. Falling back to Standard Voice.');
                setVoiceEngine('standard');
                voiceService.setEngine('standard');
            }
        } else {
            voiceService.speak("Voice engine switched to Standard Voice. Female voice activated.");
            setTimeout(() => {
                alert('Voice engine switched to Standard Voice (Female Voice)');
            }, 500);
        }
    };

    return (
        <div className="setting__viewport">
            {/* Top bar */}
            <Navbar />

            {/* Panel shell */}
            <main className="setting__main">
                <h1 className="setting__title">Settings</h1>

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

                    {/* Row: PyTalk Voice */}
                    <div className="row">
                        <div className="row__label">PyTalk Voice</div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <div className="select">
                                <select
                                    value={voiceEngine}
                                    onChange={(e) => handleVoiceEngineChange(e.target.value)}
                                    aria-label="Voice Engine"
                                >
                                    <option value="standard">Standard Voice (Female)</option>
                                    <option value="google">Google Speech (Male)</option>
                                </select>
                            </div>
                            <button
                                onClick={() => voiceService.speak("This is a test of the current voice engine.")}
                                className="test-voice-button"
                            >
                                Test Voice
                            </button>
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
