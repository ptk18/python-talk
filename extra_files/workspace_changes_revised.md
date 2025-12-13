# Workspace Code Editor – File Panel Position Fix 

## Goal

Ensure the **file list popup** triggered by the file icon appears **inside the Code Editor area**, not in the far-left global panel.

---

## Problem Summary

* Clicking the **file icon in the Code Editor header** currently opens the file list on the **left-side global panel**.
* This is incorrect behavior.
* The file list should be **contextual to the Code Editor**, not the app layout.

---

## Required Behavior

* When the **file icon in the Code Editor header** is clicked:

  * The file list popup must appear:

    * Anchored to the **Code Editor**
    * Overlaying or sliding out **from the editor’s left edge**
* The popup must:

  * Stay visually inside the Code Editor container
  * Not affect or shift the global left panel
  * Close when clicking outside or toggling the icon again

---

## Fix Instructions

### 1. Scope the File Popup to Code Editor Only

* Move the file popup component so it is:

  * Rendered **inside the Code Editor component**
  * Not shared with or controlled by the global layout
* The popup should be positioned **relative to the Code Editor container**, not the page root.

---

### 2. Correct Positioning Logic

* Use **relative positioning** on the Code Editor wrapper.
* Use **absolute positioning** for the file popup:

  * Left-aligned within the editor
  * Vertically aligned under the editor header
* Do not attach the popup to:

  * The app sidebar
  * The main layout container
  * The document body

---

### 3. Separate Editor File Icon from Global Panels

* Ensure the file icon click handler:

  * Toggles only the **editor file popup**
  * Does not reuse state or logic from the global left panel
* Editor file popup state must be **local to the Code Editor**.

---

### 4. No Behavior Changes

* Do not change:

  * Which files are shown
  * File switching logic
  * Runner execution rules
* This is a **placement-only fix**.

---

## Expected Result

* Clicking the file icon opens a popup **inside the Code Editor area**
* Global left panel remains unchanged
* UI behaves like a VS Code editor sidebar, not an app-wide panel
* No layout shifting or unexpected side effects

