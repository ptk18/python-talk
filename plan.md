# Workspace UX – Clickable “Other Ways to Say It” Suggestions

## Goal

Improve user experience by allowing alternative sentence suggestions to be **clickable** and **auto-filled** into the message input box, so users don’t need to copy, paste, or retype.

---

## Current Behavior

* User clicks **“▶ Other ways to say it”**
* A list of alternative sentences is shown
* Sentences are read-only
* User must manually copy or retype a sentence to use it

---

## Desired Behavior

### 1. Make Suggestion Sentences Clickable

* Each alternative sentence in the list should be **clickable**
* Use the entire sentence row as the click target
* Cursor should indicate clickability (pointer)

---

### 2. Auto-Fill Input Box on Click

* When a user clicks a suggestion:

  * Automatically place the clicked sentence into the **“Type your message…”** input field
* The input field should:

  * Replace the current text (if any)
  * Gain focus so the user can immediately edit

---

### 3. Allow Editing Before Sending

* After auto-filling:

  * User can edit the text
  * User can replace it by clicking another suggestion
  * Message is **not sent automatically**
* Sending only happens when the user:

  * Clicks the send button
  * Or presses Enter (if supported)

---

### 4. No Side Effects

* Clicking a suggestion must **not**:

  * Execute the command
  * Trigger TTS
  * Trigger backend calls
* It should only update the input field text

---

## UI & Behavior Rules

* No new buttons
* No popups
* No animations
* No layout changes
* Keep existing “Show / Hide” behavior

---

## Scope & Constraints

* Workspace page only
* Frontend-only change
* Reuse existing input state
* Keep code simple (KISS)
* No emojis
* No unnecessary comments

---

## Expected Result

* Suggestions feel interactive and useful
* User can try different phrasing quickly
* No copy-paste needed
* UX feels smoother and more natural