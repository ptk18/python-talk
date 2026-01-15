from fastapi import APIRouter, UploadFile, File, Form
import subprocess, tempfile
import threading
import os
import torch
from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
import io
import numpy as np
import librosa
from pathlib import Path

from app.services import get_model_manager

router = APIRouter(prefix="/voice", tags=["voice"])

# Device & dtype configuration
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# Separate locks for each model (fixes thread lock contention)
_thai_lock = threading.Lock()
_english_lock = threading.Lock()
_t5_lock = threading.Lock()
_models_prewarmed = False

# Model instances (managed separately with double-checked locking)
thai_pipe = None
english_pipe = None

# Feature flag for model manager integration
USE_MODEL_MANAGER = os.getenv("FEATURE_MODEL_MANAGER", "true").lower() == "true"


def _create_thai_pipeline():
    """Factory function to create Thai Whisper pipeline."""
    print("Loading Thai Whisper model...")
    pipe = pipeline(
        task="automatic-speech-recognition",
        model="nectec/Pathumma-whisper-th-large-v3",
        torch_dtype=torch_dtype,
        device=device,
        chunk_length_s=30,
        batch_size=8,
    )
    pipe.model.config.forced_decoder_ids = pipe.tokenizer.get_decoder_prompt_ids(
        language="th",
        task="transcribe"
    )
    print("Thai Whisper model loaded successfully")
    return pipe


def _create_english_pipeline():
    """Factory function to create English Whisper pipeline."""
    print("Loading English Whisper model...")
    pipe = pipeline(
        task="automatic-speech-recognition",
        model="distil-whisper/distil-large-v3",
        torch_dtype=torch_dtype,
        device=device,
        chunk_length_s=30,
        batch_size=8,
    )
    pipe.model.config.forced_decoder_ids = pipe.tokenizer.get_decoder_prompt_ids(
        language="en",
        task="transcribe"
    )
    print("English Whisper model loaded successfully")
    return pipe


def _register_models():
    """Register models with the model manager."""
    if USE_MODEL_MANAGER:
        manager = get_model_manager()
        manager.register(
            name="whisper_thai",
            loader=_create_thai_pipeline,
            size_mb=3000  # ~3GB
        )
        manager.register(
            name="whisper_english",
            loader=_create_english_pipeline,
            size_mb=1500  # ~1.5GB
        )
        print("[voice] Models registered with ModelManager")


# Register models on module load
_register_models()


def get_thai_pipe():
    """
    Lazy load Thai Whisper model with double-checked locking.
    Uses separate lock from English model to prevent contention.
    """
    global thai_pipe

    if USE_MODEL_MANAGER:
        return get_model_manager().get("whisper_thai")

    # Double-checked locking pattern (fast path without lock)
    if thai_pipe is not None:
        return thai_pipe

    with _thai_lock:
        # Check again inside lock
        if thai_pipe is None:
            thai_pipe = _create_thai_pipeline()
        return thai_pipe


def get_english_pipe():
    """
    Lazy load English Whisper model with double-checked locking.
    Uses separate lock from Thai model to prevent contention.
    """
    global english_pipe

    if USE_MODEL_MANAGER:
        return get_model_manager().get("whisper_english")

    # Double-checked locking pattern (fast path without lock)
    if english_pipe is not None:
        return english_pipe

    with _english_lock:
        # Check again inside lock
        if english_pipe is None:
            english_pipe = _create_english_pipeline()
        return english_pipe


def prewarm_models():
    """Pre-warm all Whisper models at startup to avoid cold start latency"""
    global _models_prewarmed
    if _models_prewarmed:
        return {"status": "already_warmed"}

    print("\n" + "="*50)
    print("PRE-WARMING WHISPER MODELS...")
    print("="*50)

    import time
    start = time.time()

    # Load English model (most commonly used)
    print("\n[1/2] Loading English model...")
    eng_start = time.time()
    get_english_pipe()
    print(f"  ✓ English model ready ({time.time() - eng_start:.1f}s)")

    # Load Thai model
    print("\n[2/2] Loading Thai model...")
    thai_start = time.time()
    get_thai_pipe()
    print(f"  ✓ Thai model ready ({time.time() - thai_start:.1f}s)")

    _models_prewarmed = True
    total_time = time.time() - start

    print("\n" + "="*50)
    print(f"ALL MODELS PRE-WARMED IN {total_time:.1f}s")
    print("="*50 + "\n")

    return {"status": "warmed", "time": total_time}


@router.post("/prewarm")
async def prewarm_voice_models():
    """API endpoint to pre-warm voice models"""
    return prewarm_models()


@router.get("/status")
async def voice_status():
    """Check if voice models are loaded"""
    if USE_MODEL_MANAGER:
        manager = get_model_manager()
        return {
            "english_loaded": manager.is_loaded("whisper_english"),
            "thai_loaded": manager.is_loaded("whisper_thai"),
            "prewarmed": _models_prewarmed,
            "model_manager_stats": manager.get_stats()
        }

    return {
        "english_loaded": english_pipe is not None,
        "thai_loaded": thai_pipe is not None,
        "prewarmed": _models_prewarmed,
        "model_manager_enabled": False
    }


# T5 paraphrasing model with lazy loading
t5_tokenizer = None
t5_model = None
T5_AVAILABLE = False
_t5_loaded = False


def _load_t5_model():
    """Lazy load T5 paraphrasing model."""
    global t5_tokenizer, t5_model, T5_AVAILABLE, _t5_loaded

    if _t5_loaded:
        return T5_AVAILABLE

    with _t5_lock:
        if _t5_loaded:
            return T5_AVAILABLE

        try:
            print("Loading T5 paraphrasing model...")
            t5_model_name = "Vamsi/T5_Paraphrase_Paws"
            t5_tokenizer = T5Tokenizer.from_pretrained(t5_model_name, legacy=False)
            t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name)
            print("T5 paraphrasing model loaded successfully")
            T5_AVAILABLE = True
        except Exception as e:
            print(f"Failed to load T5 model: {e}")
            t5_tokenizer = None
            t5_model = None
            T5_AVAILABLE = False

        _t5_loaded = True
        return T5_AVAILABLE


def paraphrase(text, n=3):
    # Lazy load T5 model
    if not _load_t5_model():
        # Return the original text as alternatives if T5 is not available
        return [text] * n

    try:
        input_text = f"paraphrase: {text} </s>"
        encoding = t5_tokenizer([input_text], return_tensors="pt", padding=True)
        outputs = t5_model.generate(
            **encoding,
            max_length=128,
            num_return_sequences=n,
            num_beams=5,
            temperature=1.5,
            early_stopping=True
        )
        return [t5_tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
    except Exception as e:
        print(f"Paraphrasing error: {e}")
        return [text] * n


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Transcribe audio using Hugging Face Whisper models
    - English: distil-whisper/distil-large-v3 (faster, more accurate)
    - Thai: nectec/Pathumma-whisper-th-large-v3 (Thai-specific fine-tuned model)

    TTS is handled by the browser's Web Audio API on the frontend
    """
    import time
    start_time = time.time()

    try:
        # Read audio file
        audio_bytes = await file.read()
        io_time = time.time()
        print(f"[TIMING] Audio read: {io_time - start_time:.2f}s")

        # Save to temporary file (librosa needs a file path for webm)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            # Load audio with librosa (Whisper uses 16kHz)
            audio_array, sampling_rate = librosa.load(
                tmp_path,
                sr=16000
            )
            load_time = time.time()
            print(f"[TIMING] Audio load: {load_time - io_time:.2f}s")
        finally:
            # Clean up temp file
            import os
            os.unlink(tmp_path)

        # Select appropriate pipeline based on language
        if language.lower() in ["th", "thai", "ไทย"]:
            pipe = get_thai_pipe()
            lang_code = "th"
        else:
            pipe = get_english_pipe()
            lang_code = "en"

        model_load_time = time.time()
        print(f"[TIMING] Model load: {model_load_time - load_time:.2f}s")

        # Transcribe with optimizations
        prediction = pipe(
            {"array": audio_array, "sampling_rate": sampling_rate},
            return_timestamps=False,
            generate_kwargs={
                "language": lang_code,
                "task": "transcribe",
                "num_beams": 1,  # Faster greedy decoding instead of beam search
            }
        )["text"]

        transcribe_time = time.time()
        total_time = transcribe_time - start_time
        print(f"[TIMING] Transcription: {transcribe_time - model_load_time:.2f}s")
        print(f"[TIMING] TOTAL: {total_time:.2f}s")
        print(f"[Whisper] Transcription ({lang_code}): '{prediction}'")

        text = prediction.strip()

        if not text:
            return {"error": "Empty transcription", "language": lang_code}

        # Generate paraphrases only for English
        alternatives = paraphrase(text, n=3) if lang_code == "en" else [text] * 3

        return {
            "text": text,
            "language": lang_code,
            "alternatives": alternatives,
            "original": text,
            "confidence": 1.0,
            "timing": {
                "total": round(total_time, 2),
                "audio_read": round(io_time - start_time, 2),
                "audio_load": round(load_time - io_time, 2),
                "model_load": round(model_load_time - load_time, 2),
                "transcription": round(transcribe_time - model_load_time, 2)
            }
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during transcription:\n{error_details}")
        return {"error": str(e)}
