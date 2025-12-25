## Language-Preserving Multi-Language Voice Pipeline (Thai Support)

### Goal

Upgrade the existing dual-engine Speech-to-Text (STT) and Text-to-Speech (TTS) system to **natively support Thai and other languages**, while preserving the user’s spoken language end-to-end and translating **only when required for internal logic**.

---

## High-Level Principles

1. Preserve the **original spoken language** as long as possible
2. Detect language automatically during STT
3. Make paraphrasing **language-aware**
4. Translate only for:

   * command parsing
   * LLM logic
5. Respond and speak in the **user’s original language**

---

## Task 1 — Language Detection in STT (Backend)

### Files

* `backend/voice.py`
* `backend/google_speech.py`

### Instructions

1. Extract detected language from STT engines:

   * Whisper: `result["language"]`
   * Google Speech: `languageCode` or confidence-based detection

2. Include detected language in STT response

### Output Contract

```json
{
  "text": "เปิดไฟในห้องนั่งเล่น",
  "language": "th",
  "alternatives": [],
  "confidence": 0.92
}
```

### Acceptance Criteria

* Thai speech returns `"language": "th"`
* English speech returns `"language": "en"`
* No forced translation occurs at this stage

---

## Task 2 — Remove Default Thai → English Translation

### Files

* `backend/voice.py`

### Instructions

1. Remove automatic MarianMT translation for non-English input
2. Preserve original text for UI display
3. Only translate when explicitly requested by downstream logic

### Acceptance Criteria

* Thai input remains Thai in API response
* No translation occurs unless explicitly invoked

---

## Task 3 — Language-Aware Paraphrasing (Replace T5)

### Files

* `backend/voice.py`
* LLM integration module (Claude / OpenAI / Gemini)

### Instructions

1. Replace English-only T5 paraphraser with LLM-based paraphrasing
2. Prompt the LLM using the detected language

### Prompt Template

```
Paraphrase the following sentence in {{language}}.
Keep the meaning and intent identical.
Generate 3 short alternatives.

Sentence:
{{text}}
```

### Acceptance Criteria

* Thai input → Thai paraphrases
* English input → English paraphrases
* Mixed language preserved naturally

---

## Task 4 — API Contract Upgrade (Backend → Frontend)

### Files

* `backend/*`
* `frontend/api.ts`

### Instructions

1. Update all STT responses to include `language`
2. Propagate `language` through API layers

### Type Definition

```ts
type VoiceTranscriptionResponse = {
  text: string
  language: string
  alternatives: string[]
  confidence?: number
}
```

### Acceptance Criteria

* Frontend receives `language` consistently
* No breaking changes in existing flows

---

## Task 5 — Frontend Language State Management

### Files

* `frontend/voiceService.ts`
* `frontend/Workspace.tsx`

### Instructions

1. Store detected language in frontend state
2. Bind message input text and language together
3. Do not auto-rewrite text into English

### Acceptance Criteria

* Thai speech appears as Thai in input box
* Language state updates per interaction

---

## Task 6 — Language-Aware Text-to-Speech (TTS)

### Files

* `frontend/voiceService.ts`
* `backend/google_speech.py`

### Instructions

#### Google TTS

Select voice dynamically:

```ts
if (lang === "th") voice = "th-TH-Standard-A"
if (lang === "en") voice = "en-US-Standard-D"
```

#### Browser TTS Fallback

```ts
utterance.lang = detectedLanguage
```

### Acceptance Criteria

* Thai text spoken with Thai pronunciation
* English text spoken with English voice
* No English phonetics for Thai text

---

## Task 7 — Internal Translation Boundary (Command Logic)

### Files

* Command parser / LLM executor

### Instructions

1. If internal logic requires English:

   * Translate Thai → English internally
2. Never expose intermediate English text to UI
3. Translate responses back to original language before TTS

### Acceptance Criteria

* Commands work regardless of input language
* UI always remains in user’s language

---

## Task 8 — Mixed-Language Support

### Instructions

1. Allow mixed Thai + English input
2. Detect dominant language
3. Preserve original sentence structure

### Acceptance Criteria

* “เปิดไฟ living room” works correctly
* No token loss or forced normalization

---

## Final Validation Checklist

* [ ] Thai STT works in both engines
* [ ] Language returned in API
* [ ] Paraphrases respect original language
* [ ] TTS uses correct voice
* [ ] English is only used internally when required
* [ ] UI always shows user’s language

---

## Success Definition

The system behaves as a **language-preserving voice assistant** where:

* Users speak naturally in Thai or English
* The system understands and executes commands correctly
* Responses are spoken and displayed in the same language

