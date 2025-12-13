# PyTalk Voice Engine & TTS/STT Consistency Fix Plan 
## Goal

Make voice behavior predictable, consistent, and correct across the entire app by fixing default selection, preventing duplicate TTS playback, and ensuring both TTS and STT respect the selected voice mode.

---

## 1. Correct Default Voice on First App Load

### Current Issue

* On first load, the app immediately uses **Google Speech (Male)** if a saved value exists.
* This causes:

  * Unexpected API calls
  * Confusion between actual default vs user-selected mode

### Required Behavior

* On **first app load (fresh session)**:

  * Voice engine must default to **Standard Voice (Female)**.
  * Settings page **PyTalk Voice dropdown** must also show **Standard Voice (Female)**.
* Google Speech must **never** be activated automatically on first load.

### Fix

* Treat **Standard Voice (Female)** as the hard default.
* Only read saved voice engine **after user has explicitly switched modes before**.
* If no explicit user action has happened:

  * Force engine = `standard`
  * Sync UI dropdown to `standard`

---

## 2. Switch to Google Speech Only via Settings Page

### Required Rule

* Google Speech (Male) can be activated **only** when:

  * User visits Settings page
  * User explicitly selects Google Speech from dropdown

### Implementation Rules

* Do not auto-switch voice engine:

  * On login
  * On Home page load
  * On workspace load
* Voice engine changes must originate **only** from:

  * Settings page action handler

---

## 3. Make Voice Engine a Single Global Source of Truth

### Current Issue

* Voice engine logic appears to be triggered from multiple places.
* This causes:

  * Duplicate speech
  * Desync between pages

### Fix

* Maintain **one global voice engine state**.
* All TTS calls must:

  * Read engine from the same source
  * Never override it locally
* Remove page-level defaults or overrides.

---

## 4. Fix Duplicate TTS Playback (Critical)

### Observed Bug

* In Google Speech mode, some actions (e.g. “command appended successfully”) speak **twice**.
* Logs show multiple TTS calls for the same logical event.

### Required Fix

* Audit all TTS triggers across:

  * Workspace
  * Command execution
  * File append flow
* Ensure:

  * Each user-visible action triggers **exactly one TTS call**
* Prevent:

  * TTS being called both in service layer and UI layer
  * TTS being triggered by both state change and side effect

### Rule

* One event → one speech call → one audio playback

---

## 5. Align Google Speech Mode With Standard Voice Flow

### Requirement

* Google Speech mode must follow the **same call flow** as Standard Voice:

  * Same trigger points
  * Same conditions
  * Same lifecycle
* Only difference:

  * TTS implementation (Google API vs browser synthesis)

### Remove

* Any special-casing where Google Speech:

  * Speaks on extra lifecycle events
  * Speaks during state sync or re-render

---

## 6. Test STT Behavior for Both Voice Modes

### Required Validation

* Test Speech-to-Text (STT) in both modes:

  * Standard Voice (Web Speech API)
  * Google Speech
* Ensure:

  * STT engine switches together with TTS engine
  * No mismatch (e.g. Google TTS + browser STT)
* STT must:

  * Respect the currently selected voice mode
  * Not fall back silently without user intent

---

## 7. Persistence Rules (Simple & Safe)

* Save voice mode **only after user explicitly switches it**.
* On reload:

  * If saved mode exists → apply it
  * Else → use Standard Voice (Female)
* Never auto-save Google Speech as default without user action.

---

## 8. Code Quality Constraints (Must Follow)

* Keep implementation simple.
* No extra abstraction layers.
* No emojis.
* No unnecessary logs or comments.
* Follow KISS principle strictly.

---

## Expected Result

* App always starts with **Standard Voice (Female)** unless user previously chose otherwise.
* Settings dropdown always reflects the real active engine.
* Google Speech activates only when user selects it.
* No duplicate speech anywhere in the app.
* STT and TTS stay in sync across all pages.
* Voice behavior is stable, predictable, and clean.
