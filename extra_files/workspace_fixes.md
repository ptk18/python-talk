# PyTalk Workspace UI Polish Plan 

## Goal

Improve clarity and usability of the Workspace page by replacing the Send button with a clean icon and making the left-side method list easier to read.

---

## 1. Replace “Send” Text Button with 2D Send Icon

### Current Issue

* The **Send** button uses a text label.
* It looks heavier than the rest of the UI and breaks visual consistency.

### Required Change

* Replace the **Send** text button with a **2D flat send icon**.
* Icon style:

  * Flat
  * 2D
  * Simple (paper-plane or arrow style)
* Behavior:

  * Clicking the icon sends the message (same as current Send button)
* Keep:

  * Button size
  * Button position
  * Keyboard behavior (Enter to send, if supported)

### Do Not

* Add text next to the icon
* Add animations or effects

---

## 2. Improve Readability of Left-Side “Available Methods” Panel

### Current Issue

* Method names in the left panel are:

  * Too pale
  * Slightly too small
  * Hard to read against the background

### Required Change

* Make method list text:

  * Slightly **brighter**
  * Slightly **bolder**
* Increase readability without changing layout.

### Styling Guidelines

* Increase:

  * Text color contrast
  * Font weight (e.g. regular → medium or semibold)
* Optional:

  * Slight font size increase (very small adjustment)
* Do not:

  * Change spacing
  * Add icons
  * Change list structure

---

## 3. Scope & Constraints

* Workspace page only.
* No backend changes.
* No new logic.
* No emojis.
* No unnecessary comments.
* Follow KISS principle.

---

## Expected Result

* Send action uses a clean, modern icon instead of text.
* Left-side method list is clearly readable at a glance.
* Workspace UI feels more polished and consistent.

