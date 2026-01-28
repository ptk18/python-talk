import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import translate_v2 as translate
import httpx

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

# Feature flag for fallback (can be disabled if needed)
ENABLE_TRANSLATION_FALLBACK = os.environ.get("FEATURE_TRANSLATION_FALLBACK", "true").lower() == "true"

# LibreTranslate API URL (can be self-hosted or use public instance)
LIBRETRANSLATE_URL = os.environ.get("LIBRETRANSLATE_URL", "https://libretranslate.com/translate")

# Common Thai turtle/coding commands with English translations
# This cache provides instant translations without API calls
THAI_COMMAND_CACHE = {
    # Movement commands
    "เดินหน้า": "move forward",
    "ถอยหลัง": "move backward",
    "ไปข้างหน้า": "go forward",
    "ถอยกลับ": "go backward",
    "เดิน": "move",

    # Turning commands
    "เลี้ยวซ้าย": "turn left",
    "เลี้ยวขวา": "turn right",
    "หมุนซ้าย": "rotate left",
    "หมุนขวา": "rotate right",
    "หัน": "turn",

    # Drawing commands
    "วาดวงกลม": "draw circle",
    "วาดสี่เหลี่ยม": "draw square",
    "วาดสามเหลี่ยม": "draw triangle",
    "วาดเส้น": "draw line",
    "วาด": "draw",

    # Pen commands
    "ยกปากกา": "pen up",
    "วางปากกา": "pen down",
    "ยกปากกาขึ้น": "lift pen up",
    "วางปากกาลง": "put pen down",

    # Color commands
    "เปลี่ยนสี": "change color",
    "สีแดง": "red color",
    "สีน้ำเงิน": "blue color",
    "สีเขียว": "green color",
    "สีเหลือง": "yellow color",
    "สีส้ม": "orange color",
    "สีม่วง": "purple color",
    "สีดำ": "black color",
    "สีขาว": "white color",

    # Position commands
    "กลับบ้าน": "go home",
    "ไปที่": "go to",
    "ไปตำแหน่ง": "go to position",

    # Control commands
    "หยุด": "stop",
    "ล้าง": "clear",
    "รีเซ็ต": "reset",
    "ซ่อน": "hide",
    "แสดง": "show",

    # Speed commands
    "เร็วขึ้น": "faster",
    "ช้าลง": "slower",
    "ความเร็ว": "speed",

    # Common phrases with numbers
    "เดินหน้า 100": "move forward 100",
    "เลี้ยวซ้าย 90": "turn left 90",
    "เลี้ยวขวา 90": "turn right 90",
    "วาดวงกลม 50": "draw circle 50",
}


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
    fallback_used: Optional[str] = None  # None, "cache", "libretranslate", "passthrough"


async def translate_with_libretranslate(
    text: str, source: str, target: str
) -> Optional[str]:
    """
    Fallback translation using LibreTranslate API.
    Can use public instance or self-hosted.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LIBRETRANSLATE_URL,
                json={
                    "q": text,
                    "source": source,
                    "target": target,
                    "format": "text"
                },
                timeout=5.0
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("translatedText")
    except Exception as e:
        print(f"[Translation] LibreTranslate fallback failed: {e}")
    return None


def translate_with_google(text: str, source_lang: str, target_lang: str) -> dict:
    """
    Primary translation using Google Cloud Translation API.
    Returns dict with translated_text and detected source_lang.
    """
    client = translate.Client()

    # Detect language if source is auto
    actual_source = source_lang
    if source_lang == "auto":
        detection = client.detect_language(text)
        actual_source = detection["language"]
        print(f"[Translation] Detected language: {actual_source} (confidence: {detection.get('confidence', 'N/A')})")

    # Translate the text
    result = client.translate(
        text,
        source_language=actual_source,
        target_language=target_lang,
        format_="text"
    )

    return {
        "translated_text": result["translatedText"],
        "source_lang": actual_source
    }


def check_cache(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Check if translation exists in cache for common commands.
    Supports exact match and partial match for commands with numbers.
    """
    if source_lang != "th" or target_lang != "en":
        return None

    normalized = text.strip()

    # Exact match
    if normalized in THAI_COMMAND_CACHE:
        return THAI_COMMAND_CACHE[normalized]

    # Try partial match for commands with numbers
    # e.g., "เดินหน้า 150" should match "เดินหน้า" pattern
    for thai_cmd, english_cmd in THAI_COMMAND_CACHE.items():
        if normalized.startswith(thai_cmd + " "):
            # Extract the number/rest and append to English translation
            rest = normalized[len(thai_cmd):].strip()
            return f"{english_cmd} {rest}"

    return None


@router.post("/text", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text from one language to another.

    Default: Thai (th) -> English (en)

    Fallback chain (when Google API fails):
    1. Local cache for common Thai commands (instant)
    2. LibreTranslate API (free/self-hosted)
    3. Pass-through with warning (last resort)
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Try cache first for Thai -> English (instant, no API call)
    cached = check_cache(request.text, request.source_lang, request.target_lang)
    if cached:
        print(f"[Translation] Cache hit: '{request.text}' -> '{cached}'")
        return TranslateResponse(
            translated_text=cached,
            original_text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=1.0,
            fallback_used="cache"
        )

    # Try Google Translation (primary)
    google_error = None
    try:
        result = translate_with_google(
            request.text,
            request.source_lang,
            request.target_lang
        )
        print(f"[Translation] Google: '{request.text}' -> '{result['translated_text']}'")
        return TranslateResponse(
            translated_text=result["translated_text"],
            original_text=request.text,
            source_lang=result["source_lang"],
            target_lang=request.target_lang,
            confidence=1.0,
            fallback_used=None
        )
    except Exception as e:
        google_error = str(e)
        print(f"[Translation] Google failed: {google_error}")

    # Fallback chain (only if enabled)
    if not ENABLE_TRANSLATION_FALLBACK:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {google_error}"
        )

    # Try LibreTranslate as fallback
    libre_result = await translate_with_libretranslate(
        request.text,
        request.source_lang,
        request.target_lang
    )
    if libre_result:
        print(f"[Translation] LibreTranslate fallback: '{request.text}' -> '{libre_result}'")
        return TranslateResponse(
            translated_text=libre_result,
            original_text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=0.8,  # Lower confidence for fallback
            fallback_used="libretranslate"
        )

    # Last resort: pass through original text with warning
    # This allows the NLP pipeline to try processing the original text
    print(f"[Translation] All translators failed, passing through: '{request.text}'")
    return TranslateResponse(
        translated_text=request.text,  # Pass through original
        original_text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        confidence=0.0,  # Zero confidence indicates no translation
        fallback_used="passthrough"
    )


@router.get("/status")
async def check_translation_status():
    """Check if translation service is available"""
    status = {
        "google": {"available": False, "message": ""},
        "libretranslate": {"available": False, "message": ""},
        "cache": {"available": True, "entries": len(THAI_COMMAND_CACHE)},
        "fallback_enabled": ENABLE_TRANSLATION_FALLBACK
    }

    # Check Google
    try:
        client = translate.Client()
        client.translate("test", target_language="en")
        status["google"] = {"available": True, "message": "Google Translation API is available"}
    except Exception as e:
        status["google"] = {"available": False, "message": str(e)}

    # Check LibreTranslate
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LIBRETRANSLATE_URL,
                json={"q": "test", "source": "en", "target": "th"},
                timeout=5.0
            )
            if response.status_code == 200:
                status["libretranslate"] = {"available": True, "message": "LibreTranslate is available"}
            else:
                status["libretranslate"] = {"available": False, "message": f"HTTP {response.status_code}"}
    except Exception as e:
        status["libretranslate"] = {"available": False, "message": str(e)}

    return status


@router.get("/cache")
async def get_translation_cache():
    """Get the list of cached Thai command translations"""
    return {
        "count": len(THAI_COMMAND_CACHE),
        "commands": THAI_COMMAND_CACHE
    }
