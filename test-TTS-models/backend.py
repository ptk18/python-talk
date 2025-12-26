"""
Backend API for TTS testing
Provides endpoints for Google Cloud TTS and Gemini TTS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import texttospeech
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv("../backend/app/nlp_v3/.env")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../backend/google-credentials.json"

# Initialize Google Cloud TTS client
gcloud_tts_client = texttospeech.TextToSpeechClient()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


class TTSRequest(BaseModel):
    text: str
    language: str  # 'th' or 'en'


@app.get("/")
def read_root():
    return {"message": "TTS Testing Backend API"}


@app.post("/api/tts/google-cloud")
async def google_cloud_tts(request: TTSRequest):
    """
    Google Cloud Text-to-Speech API endpoint
    """
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=request.text)

        # Build the voice request
        if request.language == "th":
            voice = texttospeech.VoiceSelectionParams(
                language_code="th-TH",
                name="th-TH-Neural2-C"  # Thai female voice
            )
        else:  # English
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-F"  # English female voice
            )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request
        response = gcloud_tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Encode audio content to base64
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')

        return {
            "success": True,
            "audio": audio_base64,
            "mime_type": "audio/mp3"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/gemini")
async def gemini_tts(request: TTSRequest):
    """
    Gemini Text-to-Speech API endpoint
    """
    try:
        # Determine voice and language instruction
        if request.language == "th":
            voice_name = "Sadaltager"  # Good for Thai
            prompt = f"Say this in Thai with clear pronunciation: {request.text}"
        else:  # English
            voice_name = "Puck"  # Good for English
            prompt = f"Say this in English with clear pronunciation: {request.text}"

        # Generate speech using Gemini TTS
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=prompt,
            config={
                "response_modalities": ['Audio'],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice_name
                        }
                    }
                }
            },
        )

        # Extract audio data
        audio_blob = response.candidates[0].content.parts[0].inline_data

        # The audio is in PCM format (audio/L16;codec=pcm;rate=24000)
        # We need to convert it to base64 for transmission
        audio_base64 = base64.b64encode(audio_blob.data).decode('utf-8')

        return {
            "success": True,
            "audio": audio_base64,
            "mime_type": audio_blob.mime_type,
            "sample_rate": 24000
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
