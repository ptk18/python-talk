# PyTalk Workspace – Multi-File Code Editor Improvement Plan

## Goal

Improve the Workspace Code Editor so users can view and edit multiple files related to a conversation (like a lightweight VS Code experience), while ensuring **only `runner.py` is executed** when the Run button is clicked.

---

## 1. Add Left Side File Panel (VS Code–Style)

* Add a **left-side vertical panel** inside the Code Editor area.
* The panel should contain:

  * **File icon button only** (no text label)
* When the file icon is clicked:

  * A **file list panel** slides in or pops up from the left
  * Panel shows all files associated with the current conversation

---

## 2. Show Conversation Files in File Panel

* The file panel must list **only files belonging to the active conversation**.
* Example for current conversation:

  * `calculator.py`
  * `runner.py`
* Do not show unrelated project files.
* Each file item should:

  * Be clickable
  * Open the file content in the Code Editor

---

## 3. Support Multi-File Viewing & Editing

* User must be able to:

  * Open any listed file in the editor
  * Edit file contents
  * Save changes
  * Undo / redo edits
* Only one file is active in the editor at a time.
* Switching files should:

  * Update editor content
  * Preserve unsaved changes if applicable (simple state handling)

---

## 4. Runner Execution Rule (Important)

* When the **Run** button is clicked:

  * **Always execute `runner.py`**
  * Ignore which file is currently open in the editor
* Other files (e.g. `calculator.py`) are:

  * Editable
  * Importable
  * **Never directly executed**

---

## 5. Editor Controls Behavior

* Existing editor controls (save, undo, redo) should:

  * Apply to the currently open file
* Run button behavior must:

  * Be fixed to `runner.py`
  * Not change based on active editor tab/file

---

## 6. UI Behavior Rules

* File panel:

  * Hidden by default
  * Toggled by clicking the file icon
* Keep layout clean and minimal.
* Do not add:

  * Tabs at the top
  * File tree nesting
  * Advanced VS Code features

---

## 7. Code Quality Constraints

* Keep implementation simple.
* Reuse existing editor logic where possible.
* No extra abstractions.
* No emojis.
* No unnecessary comments.
* Follow KISS principle strictly.

---

## Expected Result

* Workspace shows a VS Code–like file switcher (icon + pop-up panel).
* User can view and edit all conversation files.
* `runner.py` is always the execution entry point.
* Code Editor behavior is predictable and clean.
* No impact on other pages or voice features.

