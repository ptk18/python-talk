# Google Speech API POC Setup Guide

## Quick Setup Steps

### 1. Install Dependencies
```bash
pip install -r google_speech_requirements.txt
```

### 2. Setup Google Cloud Credentials

#### Option A: Using existing Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Enable APIs:
   - [Enable Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com)
   - [Enable Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)

4. Create Service Account:
   - Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Click "Create Service Account"
   - Name: `py-talk-speech-api`
   - Role: `Owner` or `Cloud Speech Administrator`
   - Click "Create and Continue"
   - Click "Done"

5. Generate Key:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Save the downloaded file as `google-credentials.json` in project root

#### Option B: Quick Start (New Account with $300 credits)
1. Go to https://cloud.google.com/free
2. Sign up with your KMITL .edu email
3. Get **$300 free credits** (no credit card needed during trial)
4. Follow steps 3-5 from Option A

### 3. Set Environment Variable
```bash
# On macOS/Linux
export GOOGLE_APPLICATION_CREDENTIALS="/Users/ptk/ptk/kmitl-senior-yr/py-talk/google-credentials.json"

# On Windows (PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\google-credentials.json"

# Or add to your .bashrc/.zshrc for permanent setup
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-credentials.json"' >> ~/.zshrc
```

### 4. Run the POC
```bash
# Run full demo (TTS -> STT round-trip)
python google_speech_poc.py

# Test STT with your own audio file
python google_speech_poc.py path/to/your/audio.mp3
```

## Expected Output

```
============================================================
Google Cloud Speech API - Complete Demo
============================================================

============================================================
Testing Text-to-Speech (TTS)
============================================================
Input text: 'Hello! This is a test of Google Cloud Text to Speech API...'
Calling Google TTS API...
✓ SUCCESS: Audio saved to 'poc_output.mp3'
  Voice: en-US-Standard-C
  Language: en-US
  Format: MP3

============================================================
Testing Speech-to-Text (STT)
============================================================
Input audio: 'poc_output.mp3'
Calling Google STT API...
✓ SUCCESS: Transcription complete

Transcription Results:
------------------------------------------------------------
  Transcript: Hello! This is a test of Google Cloud Text to Speech API...
  Confidence: 98.50%

============================================================
Round-trip Comparison
============================================================
Original:    'Hello! This is a test...'
Transcribed: 'Hello! This is a test...'
✓ Perfect match!

============================================================
Demo Complete!
============================================================
```

## Testing Different Voices

Edit `google_speech_poc.py` line 50-52 to try different voices:

### Standard Voices (Cheaper - $4/1M characters)
```python
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Standard-A",  # Male
    # name="en-US-Standard-C",  # Female
    # name="en-US-Standard-D",  # Male
)
```

### WaveNet Voices (Premium - $16/1M characters)
```python
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Wavenet-A",  # Male, very natural
    # name="en-US-Wavenet-C",  # Female, very natural
    # name="en-US-Wavenet-F",  # Female, very natural
)
```

### Neural2 Voices (Latest - $16/1M characters)
```python
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Neural2-A",  # Male, most natural
    # name="en-US-Neural2-C",  # Female, most natural
)
```

## Cost Estimate for This POC

- **TTS**: ~100 characters = $0.0004 (Standard) or $0.0016 (WaveNet)
- **STT**: ~5 seconds = $0.002
- **Total per run**: ~$0.003 (less than 1 cent)

With **$300 credits**, you can run this demo ~100,000 times!

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not set"
- Make sure you exported the environment variable in the same terminal session
- Check the path is absolute, not relative

### Error: "API has not been used in project"
- Enable the APIs in Google Cloud Console (see step 3)
- Wait 1-2 minutes for APIs to activate

### Error: "Permission denied"
- Make sure your service account has the correct roles
- Try using "Owner" role for testing

### Error: "Audio encoding error"
- Make sure audio file is in supported format (MP3, WAV, FLAC)
- Check sample rate matches the config (24000 for MP3)

## Next Steps

After testing the POC:
1. ✓ Verify audio quality is better than pyttsx3
2. ✓ Check transcription accuracy
3. → Integrate into `backend/app/routers/voice.py`
4. → Update frontend to handle new voice quality
5. → Monitor costs in Google Cloud Console

## Integration Preview

To integrate into your backend:
```python
# Replace in voice.py:
# - whisper.transcribe() → google speech.recognize()
# - pyttsx3.say() → google texttospeech.synthesize_speech()
```

See GoogleSpeechAPI.md for full cost analysis and integration guide.
