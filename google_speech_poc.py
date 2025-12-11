#!/usr/bin/env python3
"""
Google Speech API POC - Text-to-Speech and Speech-to-Text Demo
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    credentials_path = Path(__file__).parent / "google-credentials.json"
    if credentials_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
        print(f"✓ Using credentials: {credentials_path}")
    else:
        print("ERROR: google-credentials.json not found")
        sys.exit(1)
else:
    print(f"✓ Using credentials: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

try:
    from google.cloud import texttospeech
    from google.cloud import speech
except ImportError:
    print("ERROR: Google Cloud libraries not installed")
    print("Please run: pip install google-cloud-speech google-cloud-texttospeech")
    sys.exit(1)


def play_audio(audio_file: str):
    """Play audio file using system default player"""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", audio_file], check=True)
        elif system == "Windows":
            subprocess.run(["start", audio_file], shell=True, check=True)
    except Exception as e:
        print(f"Could not play audio: {e}")


def test_text_to_speech(text: str, output_file: str = "output.mp3", play: bool = True):
    """Convert text to speech and optionally play it"""
    print(f"\n[TTS] Converting: '{text}'")

    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Standard-C"
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(output_file, "wb") as out:
            out.write(response.audio_content)

        print(f"✓ Audio saved: {output_file}")

        if play:
            print("🔊 Playing audio...")
            play_audio(output_file)

        return output_file

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return None


def test_speech_to_text(audio_file: str):
    """Convert audio file to text"""
    print(f"\n[STT] Transcribing: {audio_file}")

    if not Path(audio_file).exists():
        print(f"✗ Audio file not found")
        return None

    try:
        client = speech.SpeechClient()

        with open(audio_file, "rb") as audio:
            content = audio.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=24000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        response = client.recognize(config=config, audio=audio)

        if not response.results:
            print("✗ No speech detected")
            return None

        full_transcript = " ".join([
            result.alternatives[0].transcript
            for result in response.results
        ])

        avg_confidence = sum([
            result.alternatives[0].confidence
            for result in response.results
        ]) / len(response.results)

        print(f"✓ Transcript: {full_transcript}")
        print(f"  Confidence: {avg_confidence:.2%}")

        return full_transcript

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return None


def run_full_demo():
    """Run complete TTS -> STT round-trip demo"""
    print("\n" + "="*50)
    print("Google Cloud Speech API - POC Demo")
    print("="*50)

    test_text = "Hello! This is a test of Google Cloud Text to Speech API. It sounds much more natural than traditional speech synthesis."

    audio_file = test_text_to_speech(test_text, "poc_output.mp3", play=True)

    if not audio_file:
        print("\n✗ TTS failed")
        return

    transcribed_text = test_speech_to_text(audio_file)

    if transcribed_text:
        print(f"\n{'='*50}")
        print("Comparison:")
        print(f"  Original:    {test_text}")
        print(f"  Transcribed: {transcribed_text}")

        if test_text.lower().strip() == transcribed_text.lower().strip():
            print("✓ Perfect match!")
        else:
            print("→ Minor differences (normal)")

    print(f"\n{'='*50}")
    print("Demo Complete!")
    print(f"{'='*50}")


def test_with_custom_audio(audio_path: str):
    """Test STT with custom audio file"""
    print(f"\nTesting custom audio: {audio_path}")
    test_speech_to_text(audio_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_with_custom_audio(sys.argv[1])
    else:
        run_full_demo()
