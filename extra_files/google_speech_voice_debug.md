# PyTalk Settings Page – Voice UI & Google Speech Fix Plan 

## Goal

Fix UI visibility issues, correct frontend state mismatches, and ensure the selected voice engine (Standard vs Google Speech) is applied consistently across app usage, refreshes, and user actions, with clear user feedback.

---

## 1. Fix “Test Voice” Button Visibility

* The **Test Voice** button is currently visually invisible / disabled-looking.
* Fix the button styling so that:

  * Text is clearly visible
  * Button has proper background and border contrast
  * Disabled vs enabled states are visually clear
* Do **not** change button placement or behavior — styling fix only.

---

## 2. Fix PyTalk Voice Default Selection (Frontend State Bug)

### Current Bug

* On first page load or refresh:

  * The app **uses Standard Female Voice correctly**
  * BUT the **PyTalk Voice dropdown incorrectly shows “Google Speech (Male)”**
* This is a **frontend state mismatch**.

### Required Fix

* On initial load:

  * PyTalk Voice dropdown must reflect the **actual active voice engine**
* Default behavior:

  * **Standard Voice (Female)** must be:

    * The active engine
    * The selected dropdown value
* Ensure:

  * Dropdown value is derived from persisted state (or default config)
  * UI never shows Google Speech unless it is actually active

---

## 3. Fix Voice Engine Switching Logic (Google Speech Not Applied)

### Current Behavior

* Selecting **Google Speech (Male)**:

  * Updates dropdown UI
  * Test Voice uses Google TTS correctly
  * BUT the main app **continues using Standard Female Voice**
* This means:

  * Voice engine switch is **not applied globally**
  * Only the test function uses Google Speech

### Required Fix

* When PyTalk Voice is changed:

  * Update the **global voice engine state**
  * Ensure **all TTS calls** use the selected engine
* Google Speech must be used consistently for:

  * Test Voice
  * Normal speaking flow
* No partial switching (test-only behavior).

---

## 4. Persist Voice Engine Selection Correctly

* User-selected PyTalk Voice must:

  * Persist across page refresh
  * Persist across navigation
* On app startup:

  * Load persisted voice preference
  * Apply it immediately
  * Sync dropdown UI with active engine
* If persistence fails:

  * Fallback safely to **Standard Voice (Female)**

---

## 5. Add User Feedback When Switching Voice Engine

* When user changes PyTalk Voice:

  * Show a clear acknowledgement:

    * Toast
    * Alert
    * Inline message
* Message examples:

  * “Voice engine switched to Standard Voice (Female)”
  * “Google Speech (Male) enabled successfully”
* Feedback must:

  * Confirm success
  * Not block UI
  * Not require page reload

---

## 6. Validate Voice Engine Routing (Debug-Level Check)

* Ensure the following logic is consistent:

  * Dropdown selection
  * Active voice engine
  * TTS execution path
* Console logs like:

  ```
  [VoiceService] Speaking with engine: google
  ```

  must match:

  * UI selection
  * Actual audible output
* Remove cases where:

  * UI says Google Speech
  * App still uses Standard Voice

---

## 7. Safety & Fallback Rules

* If Google Speech fails:

  * Automatically fallback to Standard Voice (Female)
  * Notify user with a warning
* App must **never become silent** due to engine failure.

---

## Expected Result

* Test Voice button is clearly visible and usable
* Default voice is **Standard Female**, both in logic and UI
* Google Speech selection applies globally, not test-only
* Dropdown state always matches active voice engine
* User gets feedback when switching voice modes
* Refreshing the page does not desync voice settings


