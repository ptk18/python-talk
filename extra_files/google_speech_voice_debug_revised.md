# PyTalk Global Voice Mode Persistence Fix 

## Goal

Ensure the selected **PyTalk Voice mode** (Standard Female or Google Speech Male) is remembered and applied **globally across the app**, including page navigation and refreshes, not only inside the Settings page.

---

## Problem Summary (Current Bug)

* Voice switching **works only inside Settings page**
* When user navigates to other pages:

  * App falls back to **Standard Female Voice**
* This means:

  * Voice engine state is **local to Settings page**
  * Other pages do **not read the selected voice mode**
* Result: UI says one thing, actual voice behavior uses default

---

## Core Fix Strategy

Make **voice mode a global, persistent state**, not a page-level state.

---

## 1. Introduce a Single Global Voice Engine Source of Truth

* Create ONE authoritative source for the current voice engine:

  * Example values:

    * `"standard_female"`
    * `"google_male"`
* This source must be accessible by:

  * Settings page
  * Home page
  * Any component that triggers TTS

---

## 2. Persist Voice Mode Selection

* When user switches PyTalk Voice in Settings:

  * Save the selected voice mode to persistent storage

    * `localStorage` (preferred for now)
    * OR backend user preference (optional, later)
* Example:

  * Key: `pytalk_voice_engine`
  * Value: `standard_female` or `google_male`

---

## 3. Load Voice Mode on App Startup (Critical)

* On **app initialization** (not just Settings page):

  * Read persisted voice mode
  * Apply it immediately to `voiceService`
* This must happen:

  * Before any TTS call
  * Before user navigates between pages
* If no saved value exists:

  * Default to **Standard Female Voice**
  * Save it as the initial value

---

## 4. Sync All Pages With the Global Voice State

* Any page that uses TTS must:

  * Use the global voice engine
  * Never assume defaults
* Remove any logic like:

  * “If not on Settings page, use standard voice”
* Voice routing must depend ONLY on:

  * Global voice engine state

---

## 5. Update Settings Page to Reflect Global State

* On Settings page load:

  * Read the global voice engine
  * Set dropdown value accordingly
* Do NOT:

  * Hardcode dropdown default
  * Override global state unintentionally

---

## 6. Apply Voice Engine Switch Globally (Not Test-Only)

* When user switches voice mode:

  * Update global state
  * Persist it
  * Update `voiceService`
* Test Voice button must:

  * Use the same global engine
  * Not bypass or override it

---

## 7. Navigation Safety Check

* After switching voice mode:

  * Navigate to another page (Home, Profile, etc.)
  * Trigger TTS
  * Confirm the selected engine is used
* No fallback to default unless:

  * Google Speech fails

---

## 8. Failure & Fallback Rules

* If Google Speech API fails:

  * Automatically fallback to Standard Female Voice
  * Update global state
  * Notify user once
* App must never:

  * Be silent
  * Desync UI vs actual voice

---

## Expected Result

* Voice mode selection persists across:

  * Page navigation
  * Page refresh
* All pages use the selected voice engine
* Settings page always reflects the real active voice
* No hidden fallback to Standard Female Voice unless necessary
* Voice behavior matches user choice everywhere


