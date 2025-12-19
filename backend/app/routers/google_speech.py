from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os
import tempfile
from pathlib import Path
import io

router = APIRouter(prefix="/google-speech", tags=["google-speech"])

# Check if Google Cloud credentials are available
GOOGLE_CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "google-credentials.json"
GOOGLE_AVAILABLE = GOOGLE_CREDENTIALS_PATH.exists()

if GOOGLE_AVAILABLE:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(GOOGLE_CREDENTIALS_PATH)
    try:
        from google.cloud import texttospeech
        from google.cloud import speech
        GOOGLE_LIBS_AVAILABLE = True
    except ImportError:
        print("Warning: Google Cloud libraries not installed. Install with: pip install google-cloud-speech google-cloud-texttospeech")
        GOOGLE_LIBS_AVAILABLE = False
else:
    GOOGLE_LIBS_AVAILABLE = False
    print(f"Warning: Google credentials not found at {GOOGLE_CREDENTIALS_PATH}")


@router.get("/status")
async def google_speech_status():
    """Check if Google Speech API is available and configured"""
    return {
        "available": GOOGLE_AVAILABLE and GOOGLE_LIBS_AVAILABLE,
        "credentials_found": GOOGLE_AVAILABLE,
        "libraries_installed": GOOGLE_LIBS_AVAILABLE,
        "message": "Google Speech API is ready" if (GOOGLE_AVAILABLE and GOOGLE_LIBS_AVAILABLE) else "Google Speech API not configured"
    }


@router.post("/text-to-speech")
async def google_text_to_speech(text: str):
    """
    Convert text to speech using Google Cloud Text-to-Speech API
    Returns audio file (MP3)
    """
    if not GOOGLE_AVAILABLE or not GOOGLE_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Speech API not available")

    print(f"[Google TTS] Request received - Text length: {len(text)} chars")

    try:
        client = texttospeech.TextToSpeechClient()
        print("[Google TTS] Client initialized successfully")

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Use English voice only
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Standard-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.3,  
            pitch=0.0,          # Normal pitch
            volume_gain_db=0.0, # Normal volume
            sample_rate_hertz=24000  # High quality audio
        )

        print(f"[Google TTS] Using voice: en-US-Standard-D")

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        audio_size = len(response.audio_content)
        print(f"[Google TTS] ✓ Speech synthesized successfully - Audio size: {audio_size} bytes")

        # Return audio as streaming response
        audio_stream = io.BytesIO(response.audio_content)

        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Content-Length": str(audio_size)
            }
        )

    except Exception as e:
        print(f"[Google TTS] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Text-to-Speech error: {str(e)}")


@router.post("/speech-to-text")
async def google_speech_to_text(
    file: UploadFile = File(...)
):
    """
    Convert audio to text using Google Cloud Speech-to-Text API
    Accepts audio file and returns transcription
    """
    if not GOOGLE_AVAILABLE or not GOOGLE_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Speech API not available")

    print(f"[Google STT] Request received - File: {file.filename}")

    try:
        client = speech.SpeechClient()
        print("[Google STT] Client initialized successfully")

        # Read audio file
        audio_bytes = await file.read()
        print(f"[Google STT] Audio file read - Size: {len(audio_bytes)} bytes")

        audio = speech.RecognitionAudio(content=audio_bytes)

        # Try multiple encoding configurations for better compatibility
        configs_to_try = [
            # Config 1: WEBM_OPUS (Chrome/Firefox default)
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model="default",
                audio_channel_count=1,
            ),
            # Config 2: OGG_OPUS
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model="default",
                audio_channel_count=1,
            ),
            # Config 3: LINEAR16 (WAV)
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
                enable_automatic_punctuation=True,
                model="default",
            ),
        ]

        # Try each configuration
        response = None
        last_error = None

        for i, config in enumerate(configs_to_try):
            try:
                print(f"[Google STT] Trying config {i+1}/{len(configs_to_try)}: {config.encoding.name}")
                response = client.recognize(config=config, audio=audio)
                if response and response.results:
                    print(f"[Google STT] ✓ Config {i+1} succeeded")
                    break  # Success, exit loop
                else:
                    print(f"[Google STT] Config {i+1} returned no results, trying next...")
            except Exception as e:
                print(f"[Google STT] ✗ Config {i+1} failed: {str(e)}")
                last_error = e
                continue  # Try next config

        if not response:
            print("[Google STT] ✗ All configurations failed")
            raise last_error or Exception("All audio encoding configurations failed")

        if not response.results:
            print("[Google STT] No speech detected in audio")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "alternatives": [],
                "original": "",
                "error": "No speech detected in audio"
            }

        # Extract transcription and confidence
        results = []

        for result in response.results:
            if not result.alternatives:
                continue

            alternative = result.alternatives[0]

            # Get confidence (might be 0.0 for streaming, use 1.0 as default for final results)
            confidence = alternative.confidence if hasattr(alternative, 'confidence') and alternative.confidence > 0 else 0.95

            results.append({
                "transcript": alternative.transcript,
                "confidence": confidence
            })

        if not results:
            print("[Google STT] No alternatives found in results")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "alternatives": [],
                "original": "",
                "error": "No transcription alternatives found"
            }

        main_result = results[0]

        # Ensure we have actual text
        if not main_result["transcript"] or not main_result["transcript"].strip():
            print("[Google STT] Empty transcript returned")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "alternatives": [],
                "original": "",
                "error": "Empty transcription"
            }

        print(f"[Google STT] ✓ Transcription successful - Text: '{main_result['transcript']}', Confidence: {main_result['confidence']:.2f}")

        return {
            "text": main_result["transcript"],
            "language": "en",
            "confidence": main_result["confidence"],
            "alternatives": [r["transcript"] for r in results[1:]] if len(results) > 1 else [],
            "original": main_result["transcript"]
        }

    except Exception as e:
        print(f"[Google STT] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Speech-to-Text error: {str(e)}")
