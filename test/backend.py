from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import torch
from transformers import pipeline
import io
import numpy as np
import librosa
from pathlib import Path

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Device & dtype
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# Initialize pipelines
thai_pipe = None
english_pipe = None

def get_thai_pipe():
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
    return thai_pipe

def get_english_pipe():
    global english_pipe
    if english_pipe is None:
        print("Loading English Whisper model...")
        english_pipe = pipeline(
            task="automatic-speech-recognition",
            # model="openai/whisper-large-v3",
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
    return english_pipe

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file = Path(__file__).parent / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(...)
):
    import time
    start_time = time.time()

    try:
        # Read audio file
        audio_bytes = await audio.read()
        io_time = time.time()
        print(f"[TIMING] Audio read: {io_time - start_time:.2f}s")

        # Save to temporary file (librosa needs a file path for webm)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            # Load audio with librosa
            audio_array, sampling_rate = librosa.load(
                tmp_path,
                sr=16000  # Whisper uses 16kHz
            )
            load_time = time.time()
            print(f"[TIMING] Audio load: {load_time - io_time:.2f}s")
        finally:
            # Clean up temp file
            import os
            os.unlink(tmp_path)

        # Select appropriate pipeline
        if language == "thai":
            pipe = get_thai_pipe()
        else:
            pipe = get_english_pipe()

        model_load_time = time.time()
        print(f"[TIMING] Model load: {model_load_time - load_time:.2f}s")

        # Transcribe with optimizations
        prediction = pipe(
            {"array": audio_array, "sampling_rate": sampling_rate},
            return_timestamps=False,
            generate_kwargs={
                "language": "th" if language == "thai" else "en",
                "task": "transcribe",
                "num_beams": 1,  # Faster greedy decoding instead of beam search
            }
        )["text"]

        transcribe_time = time.time()
        total_time = transcribe_time - start_time
        print(f"[TIMING] Transcription: {transcribe_time - model_load_time:.2f}s")
        print(f"[TIMING] TOTAL: {total_time:.2f}s")

        return JSONResponse({
            "success": True,
            "transcription": prediction,
            "language": language,
            "timing": {
                "total": round(total_time, 2),
                "audio_read": round(io_time - start_time, 2),
                "audio_load": round(load_time - io_time, 2),
                "model_load": round(model_load_time - load_time, 2),
                "transcription": round(transcribe_time - model_load_time, 2)
            }
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during transcription:\n{error_details}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
