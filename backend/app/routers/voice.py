from fastapi import APIRouter, UploadFile, File, Form
import subprocess, tempfile
import torch
from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
import io
import numpy as np
import librosa
from pathlib import Path

router = APIRouter(prefix="/voice", tags=["voice"])

# Device & dtype configuration
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# Initialize pipelines as None (lazy loading)
thai_pipe = None
english_pipe = None

def get_thai_pipe():
    """Lazy load Thai Whisper model"""
    global thai_pipe
    if thai_pipe is None:
        print("Loading Thai Whisper model...")
        thai_pipe = pipeline(
            task="automatic-speech-recognition",
            model="nectec/Pathumma-whisper-th-large-v3",
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=30,
            batch_size=8,
        )
        thai_pipe.model.config.forced_decoder_ids = thai_pipe.tokenizer.get_decoder_prompt_ids(
            language="th",
            task="transcribe"
        )
        print("Thai Whisper model loaded successfully")
    return thai_pipe

def get_english_pipe():
    """Lazy load English Whisper model"""
    global english_pipe
    if english_pipe is None:
        print("Loading English Whisper model...")
        english_pipe = pipeline(
            task="automatic-speech-recognition",
            model="distil-whisper/distil-large-v3",
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=30,
            batch_size=8,
        )
        english_pipe.model.config.forced_decoder_ids = english_pipe.tokenizer.get_decoder_prompt_ids(
            language="en",
            task="transcribe"
        )
        print("English Whisper model loaded successfully")
    return english_pipe

try:
    # Load English paraphrasing model
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

def paraphrase(text, n=3):
    if not T5_AVAILABLE or not t5_tokenizer or not t5_model:
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
