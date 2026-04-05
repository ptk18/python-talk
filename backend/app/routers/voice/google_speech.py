from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import os
import tempfile
from pathlib import Path
import io
import time

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

# Reuse clients to avoid repeated initialization overhead
_speech_client = None
_tts_client = None

def _get_speech_client():
    global _speech_client
    if _speech_client is None and GOOGLE_LIBS_AVAILABLE:
        _speech_client = speech.SpeechClient()
    return _speech_client

def _get_tts_client():
    global _tts_client
    if _tts_client is None and GOOGLE_LIBS_AVAILABLE:
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


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
async def google_text_to_speech(text: str, rate: float = 1.0, language: str = "en"):
    """
    Convert text to speech using Google Cloud Text-to-Speech API
    Returns audio file (MP3)

    Args:
        text: The text to convert to speech
        rate: Speaking rate (0.5 to 2.0, default 1.0)
        language: Language code ("en" or "th", default "en")
    """
    if not GOOGLE_AVAILABLE or not GOOGLE_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Speech API not available")

    # Validate and clamp rate
    rate = max(0.5, min(2.0, rate))

    # Select voice based on language
    voice_map = {
        "th": ("th-TH", "th-TH-Chirp3-HD-Charon", None),
        "en": ("en-US", "en-US-Standard-D", texttospeech.SsmlVoiceGender.MALE),
    }
    lang_code, voice_name, gender = voice_map.get(language.lower(), voice_map["en"])

    print(f"[Google TTS] Request received - Text length: {len(text)} chars, Rate: {rate}x, Language: {language}")

    try:
        client = _get_tts_client()
        print("[Google TTS] Client ready")

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice_params = {
            "language_code": lang_code,
            "name": voice_name,
        }
        if gender:
            voice_params["ssml_gender"] = gender
        voice = texttospeech.VoiceSelectionParams(**voice_params)

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=rate,
            pitch=0.0,          # Normal pitch
            volume_gain_db=0.0, # Normal volume
            sample_rate_hertz=24000  # High quality audio
        )

        print(f"[Google TTS] Using voice: {voice_name}, Rate: {rate}x")

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
    file: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Convert audio to text using Google Cloud Speech-to-Text API
    Accepts audio file and returns transcription
    """
    if not GOOGLE_AVAILABLE or not GOOGLE_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Speech API not available")

    # Map language codes to Google Speech API format
    language_map = {
        "en": "en-US",
        "th": "th-TH",
        "thai": "th-TH",
        "ไทย": "th-TH",
    }
    language_code = language_map.get(language.lower(), "en-US")

    print(f"[Google STT] Request received - File: {file.filename}, Language: {language} -> {language_code}")

    try:
        t_start = time.time()

        client = _get_speech_client()
        print("[Google STT] Client ready")

        # Read audio file
        audio_bytes = await file.read()
        print(f"[Google STT] Audio file read - Size: {len(audio_bytes)} bytes")

        audio = speech.RecognitionAudio(content=audio_bytes)

        # Detect encoding from content type / filename to avoid sequential fallback
        content_type = file.content_type or ""
        filename = (file.filename or "").lower()

        if "webm" in content_type or filename.endswith(".webm"):
            encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
            sample_rate = 48000
        elif "ogg" in content_type or filename.endswith(".ogg"):
            encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
            sample_rate = 48000
        elif "wav" in content_type or filename.endswith(".wav"):
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            sample_rate = None  # Let Google auto-detect from WAV header
        else:
            # Default to WEBM_OPUS (most common from browsers)
            encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
            sample_rate = 48000

        # Build config — use "latest_short" model for lower latency on short utterances
        config_params = {
            "encoding": encoding,
            "language_code": language_code,
            "enable_automatic_punctuation": True,
            "model": "latest_short",
            "audio_channel_count": 1,
        }
        if sample_rate:
            config_params["sample_rate_hertz"] = sample_rate

        config = speech.RecognitionConfig(**config_params)

        print(f"[Google STT] Using encoding={encoding.name}, model=latest_short")

        t_api_start = time.time()
        response = client.recognize(config=config, audio=audio)
        t_api_end = time.time()
        print(f"[Google STT] API call took {(t_api_end - t_api_start)*1000:.0f}ms")

        if not response:
            print("[Google STT] ✗ No response from API")
            raise Exception("No response from Google Speech API")

        if not response.results:
            print("[Google STT] No speech detected in audio")
            return {
                "text": "",
                "language": language,
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
                "language": language,
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
                "language": language,
                "confidence": 0.0,
                "alternatives": [],
                "original": "",
                "error": "Empty transcription"
            }

        t_total = (time.time() - t_start) * 1000
        print(f"[Google STT] ✓ Transcription successful ({t_total:.0f}ms total) - Text: '{main_result['transcript']}', Confidence: {main_result['confidence']:.2f}, Language: {language_code}")

        return {
            "text": main_result["transcript"],
            "language": language,
            "confidence": main_result["confidence"],
            "alternatives": [r["transcript"] for r in results[1:]] if len(results) > 1 else [],
            "original": main_result["transcript"]
        }

    except Exception as e:
        print(f"[Google STT] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Speech-to-Text error: {str(e)}")
