import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import translate_v2 as translate

router = APIRouter(prefix="/translate", tags=["Translation"])

# Set Google Cloud credentials if not already set
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    credentials_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "google-credentials.json"
    )
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        print(f"[Translation] Using credentials: {credentials_path}")
    else:
        print(f"[Translation] WARNING: Credentials not found at {credentials_path}")

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "th"
    target_lang: str = "en"

class TranslateResponse(BaseModel):
    translated_text: str
    original_text: str
    source_lang: str
    target_lang: str
    confidence: float = 1.0

@router.post("/text", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text from one language to another using Google Cloud Translation API

    Default: Thai (th) -> English (en)
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Initialize the Translation client
        client = translate.Client()

        # Detect language if source is auto
        if request.source_lang == "auto":
            detection = client.detect_language(request.text)
            detected_lang = detection["language"]
            print(f"[Translation] Detected language: {detected_lang} (confidence: {detection.get('confidence', 'N/A')})")
            request.source_lang = detected_lang

        # Translate the text
        result = client.translate(
            request.text,
            source_language=request.source_lang,
            target_language=request.target_lang,
            format_="text"
        )

        translated_text = result["translatedText"]

        print(f"[Translation] {request.source_lang} -> {request.target_lang}")
        print(f"[Translation] Original: {request.text}")
        print(f"[Translation] Translated: {translated_text}")

        return TranslateResponse(
            translated_text=translated_text,
            original_text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=1.0  # Google Translate doesn't provide confidence scores
        )

    except Exception as e:
        error_msg = str(e)
        print(f"[Translation] Error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {error_msg}"
        )

@router.get("/status")
async def check_translation_status():
    """Check if translation service is available"""
    try:
        client = translate.Client()
        # Try a simple translation to verify service is working
        client.translate("test", target_language="en")
        return {
            "available": True,
            "message": "Translation service is available"
        }
    except Exception as e:
        return {
            "available": False,
            "message": f"Translation service unavailable: {str(e)}"
        }
