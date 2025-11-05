from fastapi import APIRouter, UploadFile, File, Form
import whisper
import subprocess, tempfile
import torch
import platform
from transformers import T5ForConditionalGeneration, T5Tokenizer, MarianMTModel, MarianTokenizer
import pyttsx3

router = APIRouter(prefix="/voice", tags=["voice"])

# Load models with error handling
try:
    # Load Whisper model
    whisper_model = whisper.load_model("base")
    print("Whisper model loaded successfully")
except Exception as e:
    print(f"Failed to load Whisper model: {e}")
    whisper_model = None

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

# Initialize pyttsx3 with error handling
try:
    # On macOS, try to use the 'nsss' driver specifically
    if platform.system() == "Darwin":  # macOS
        try:
            tts_engine = pyttsx3.init('nsss')
        except:
            tts_engine = pyttsx3.init()
    else:
        tts_engine = pyttsx3.init()
    
    tts_engine.setProperty('rate', 150)
    TTS_AVAILABLE = True
    print("TTS engine initialized successfully")
except Exception as e:
    print(f"Warning: pyttsx3 initialization failed: {e}")
    print("Text-to-speech functionality will be disabled.")
    tts_engine = None
    TTS_AVAILABLE = False

# Cache Marian translation models
translation_models = {}

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
    if TTS_AVAILABLE and tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
    else:
        print(f"TTS not available. Would speak: {text}")

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(...)
):
    if not whisper_model:
        return {"error": "Whisper model not available"}
    
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
