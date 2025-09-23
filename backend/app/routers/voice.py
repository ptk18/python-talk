from fastapi import APIRouter, UploadFile, File, Form
import whisper
import subprocess, tempfile
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer, MarianMTModel, MarianTokenizer
import pyttsx3

router = APIRouter(prefix="/voice", tags=["voice"])

# Load Whisper model
whisper_model = whisper.load_model("base")

# Load English paraphrasing model
t5_model_name = "Vamsi/T5_Paraphrase_Paws"
t5_tokenizer = T5Tokenizer.from_pretrained(t5_model_name)
t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name)

# Initialize pyttsx3
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

# Cache Marian translation models
translation_models = {}

def paraphrase(text, n=3):
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

def translate_to_english(text, src_lang):
    """Translate non-English text to English using MarianMT"""
    if src_lang not in translation_models:
        model_name = f"Helsinki-NLP/opus-mt-{src_lang}-en"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        translation_models[src_lang] = (tokenizer, model)
    else:
        tokenizer, model = translation_models[src_lang]
    
    batch = tokenizer([text], return_tensors="pt", padding=True)
    gen = model.generate(**batch)
    return tokenizer.decode(gen[0], skip_special_tokens=True)

def speak_text(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(...)
):
    try:
        audio_bytes = await file.read()

        with tempfile.NamedTemporaryFile(suffix=".webm") as temp_in, \
             tempfile.NamedTemporaryFile(suffix=".wav") as temp_wav:

            temp_in.write(audio_bytes)
            temp_in.flush()

            subprocess.run(
                ["ffmpeg", "-i", temp_in.name, "-ar", "16000", "-ac", "1", temp_wav.name, "-y"],
                check=True, capture_output=True
            )

            audio = whisper.load_audio(temp_wav.name)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)
            options = whisper.DecodingOptions(language=language)
            result = whisper.decode(whisper_model, mel, options)
            text = result.text.strip()

        if not text:
            return {"error": "Empty transcription"}

        # Translate if needed
        text_en = text
        if language != "en":
            try:
                text_en = translate_to_english(text, language)
            except Exception:
                text_en = "[Translation failed]"

        # Generate 3 paraphrases
        alternatives = paraphrase(text_en, n=3)

        # Speak English text
        speak_text(f"You said: {text_en}")

        return {"text": text_en, "alternatives": alternatives, "original": text}

    except Exception as e:
        return {"error": str(e)}
