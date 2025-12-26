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
                alert('Google Cloud Speech API is not configured.\n\nTo use Google Cloud Male Voice:\n1. Set up Google Cloud credentials\n2. Install google-cloud-speech and google-cloud-texttospeech packages\n3. Place credentials file in backend/google-credentials.json\n\nFalling back to Standard Voice (Female - Free).');
                setVoiceEngine('standard');
                voiceService.setEngine('standard');
                voiceService.speak("Google Cloud API not configured. Using standard voice.");
                return;
            }

            try {
                await voiceService.speak("Voice engine switched to Google Cloud Speech. Male voice activated.");
                console.log('✓ Voice engine switched to Google Cloud Speech (Male Voice)');
            } catch (error) {
                console.error('Error switching to Google Speech:', error);
                alert('Error switching to Google Cloud Speech. Falling back to Standard Voice (Female - Free).');
                setVoiceEngine('standard');
                voiceService.setEngine('standard');
            }
        } else {
            voiceService.speak("Voice engine switched to Standard Voice. Female voice activated.");
            console.log('✓ Voice engine switched to Standard Voice (Female - Free)');
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
                        <div className="row__label">
                            PyTalk Voice
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #666)', marginTop: '4px' }}>
                                {voiceEngine === 'standard' ? '🆓 Free - Browser TTS' : '☁️ Premium - Google Cloud'}
                            </div>
                        </div>
                        <div className="row__sep" />
                        <div className="row__control">
                            <div className="select">
                                <select
                                    value={voiceEngine}
                                    onChange={(e) => handleVoiceEngineChange(e.target.value)}
                                    aria-label="Voice Engine"
                                >
                                    <option value="standard">Standard Voice (Female - Free)</option>
                                    <option value="google">Google Cloud Voice (Male - Premium)</option>
                                </select>
                            </div>
                            <button
                                onClick={() => voiceService.speak("This is a test of the current voice engine.")}
                                className="test-voice-button"
                                style={{ marginLeft: '8px', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}
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
