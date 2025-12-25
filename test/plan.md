import torch
from transformers import pipeline
import pandas as pd

# Device & dtype
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

lang = "th"
task = "transcribe"

# ASR pipeline
pipe = pipeline(
    task="automatic-speech-recognition",
    model="nectec/Pathumma-whisper-th-large-v3",
    torch_dtype=torch_dtype,
    device=device,
)

pipe.model.config.forced_decoder_ids = pipe.tokenizer.get_decoder_prompt_ids(
    language=lang,
    task=task
)

results = []

for i, sample in enumerate(samples):
    audio_array = sample["audio"]["array"]
    sampling_rate = sample["audio"]["sampling_rate"]

    prediction = pipe(
        {"array": audio_array, "sampling_rate": sampling_rate}
    )["text"]

    results.append({
        "utt_id": sample["utterance"],
        "dialect": sample["dialect_type"],
        "reference": sample["sentence"],
        "thai_reference": sample["thai_sentence"],
        "prediction": prediction,
    })

    print(f"\nSample {i}")
    print("Reference   :", sample["sentence"])
    print("Prediction  :", prediction)


using this model, create a simple html frontend with fasapi backend 
that take voice input from user's web browser and then show the transcription 

at a button to choose English or Thai

if user chooses English, use normal Whisper model 

if user chooses Thai, use above model