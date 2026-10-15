---
name: html-accessibility-audit
description: Audit an HTML page or file for accessibility problems (missing alt text, heading order, form labels, colour contrast, keyboard focus, ARIA misuse) and report each finding with the element and a concrete fix. Use when the user asks for an accessibility, a11y, WCAG or screen-reader review of HTML, templates, or components.
---

# HTML Accessibility Audit

Review the given HTML (a file path, a pasted snippet, or a rendered template/component) against WCAG 2.2 A/AA and report findings as element + fix pairs.

## Process

1. **Locate the markup.** Read the file(s) the user names. If given a directory, glob for `*.html`, `*.htm`, and templates (`*.vue`, `*.jsx`, `*.tsx`, `*.svelte`, `*.erb`, `*.njk`) and audit those. If only a URL is given, fetch it if a fetch tool is available; otherwise say that you need the source.
2. **Check each category below** by reading the markup and any linked/inline CSS. Do not guess at what you cannot see; mark it "needs verification" instead.
3. **Report** using the output format. Keep to what is actually in the code.

## Checks

### 1. Text alternatives (WCAG 1.1.1)
- `<img>` with no `alt` attribute → error. Decorative images need `alt=""`; informative ones need a meaningful description.
- Alt text that is a filename, "image", "photo", or repeats adjacent text.
- `<input type="image">`, `<area>`, and `<svg role="img">` lacking a name (`alt`, `aria-label`, or `<title>`).
- Icon-only links/buttons with no accessible name (e.g. `<a><i class="icon"></i></a>`).
- Decorative inline SVG should have `aria-hidden="true"`.
- `<video>`/`<audio>` without captions/transcript (`<track kind="captions">`), noted as needing verification.

### 2. Document structure and headings (1.3.1, 2.4.1, 2.4.2, 3.1.1)
- Missing `<html lang>`, missing or empty `<title>`.
- Heading levels that skip (h1 → h3), multiple or zero `<h1>`, headings chosen for size rather than structure, empty headings.
- Missing landmarks: `<main>` (exactly one), `<nav>`, `<header>`, `<footer>`; multiple `<nav>` without distinguishing `aria-label`.
- No skip link when there is repeated navigation before main content.
- Layout tables, or data tables missing `<th scope>` / `<caption>`.
- Lists faked with `<br>` or `<div>`s.

### 3. Forms (1.3.1, 3.3.1, 3.3.2, 4.1.2, 1.3.5)
- `<input>`, `<select>`, `<textarea>` without an associated `<label for>`, wrapping `<label>`, `aria-label`, or `aria-labelledby`. A `placeholder` alone is not a label.
- `for`/`id` mismatches and duplicate `id`s.
- Related controls (radio/checkbox groups) missing `<fieldset>`/`<legend>`.
- Required fields indicated only by colour or `*`; suggest `required` / `aria-required` plus text.
- Error messages not linked via `aria-describedby`, not announced (`role="alert"` / `aria-live`), or `aria-invalid` missing.
- Personal-data fields missing `autocomplete` tokens (name, email, tel, etc.).
- Buttons: `<div>`/`<span>` used as buttons; `<button>` with no text; `<input type="submit">` with empty `value`.

### 4. Colour contrast (1.4.3, 1.4.6, 1.4.11, 1.4.1)
Contrast cannot be fully measured from source, so give notes, not verdicts.
- When foreground and background colours are both visible in CSS/inline styles, compute the ratio (relative luminance per WCAG) and report it. Thresholds: 4.5:1 normal text, 3:1 large text (≥24px, or ≥18.66px bold) and UI components/focus indicators.
- Flag likely risks: light grey text, text over images/gradients, placeholder colour, disabled-looking but active controls, white on brand colours.
- Information conveyed by colour alone (red/green status, links distinguished only by colour with no underline).
- Mark these as "verify with a contrast checker or browser devtools" when values come from variables or cannot be resolved.

### 5. Keyboard and focus (2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.4.11)
- `outline: none` / `outline: 0` on `:focus` with no replacement `:focus-visible` style.
- Click handlers (`onclick`) on non-interactive elements (`div`, `span`, `li`) with no `tabindex="0"`, role, and key handler; prefer a native `<button>` or `<a href>`.
- Positive `tabindex` values (`tabindex="3"`) → remove; use DOM order.
- `tabindex="-1"` on elements that should be reachable.
- `<a>` without `href` used as a button; `href="#"` or `javascript:` links.
- Modals/menus/dialogs with no focus management hint (focus trap, Escape to close, focus return); use `<dialog>` or note for verification.
- Hover-only content (tooltips, menus) with no focus equivalent.
- Content hidden with `display:none`/`visibility:hidden` while still containing focusable elements, or `aria-hidden="true"` on a container with focusable descendants.
- Autoplaying or moving content with no pause control.

### 6. ARIA misuse (4.1.2, 1.3.1) — "no ARIA is better than bad ARIA"
- Redundant roles: `<button role="button">`, `<nav role="navigation">`, `<ul role="list">` (unless list styling removes semantics deliberately).
- Invalid/unknown roles or attributes; `aria-*` values of the wrong type (e.g. `aria-expanded="yes"`).
- Role without required attributes or children: `role="tab"` outside `tablist`, `role="checkbox"` without `aria-checked`, `role="slider"` without value attributes, `role="combobox"` without `aria-expanded`/`aria-controls`.
- `aria-label` on elements where it is not supported (`div`/`span` with no role) or overriding visible text so the accessible name no longer contains the visible label (2.5.3).
- `aria-labelledby` / `aria-describedby` / `aria-controls` pointing to ids that do not exist.
- `role="presentation"`/`none` on focusable or semantic elements; `aria-hidden="true"` on focusable elements.
- Native element overridden with a conflicting role (`<h2 role="button">`, `<a role="menuitem">` without a menu).
- `aria-live` regions set to `assertive` without need; `role="alert"` on static content.
- Custom widgets (tabs, accordion, menu, combobox) built with ARIA but missing keyboard behaviour; prefer native `<details>`, `<button>`, `<select>`.

### 7. Other quick wins
- `<meta name="viewport">` with `user-scalable=no` or `maximum-scale<2` (1.4.4).
- Link text such as "click here"/"read more" with no context; identical link text pointing to different URLs; links opening new windows without warning (`target="_blank"` without notice).
- `<iframe>` without `title`.
- Text sized in fixed `px` that blocks resize; `<blink>`, `<marquee>`.
- Target size under 24×24 CSS px for small controls (2.5.8).

## Output format

Start with a one-line summary: files audited and counts by severity. Then group findings by severity — **Critical** (blocks use by assistive-tech/keyboard users), **Serious**, **Moderate**, **Needs verification** — and use this shape for each:

```
### [Severity] Short title — WCAG x.y.z
- Element: `<img src="hero.jpg" class="banner">` (file:line if known)
- Problem: what is wrong and who it affects.
- Fix: `<img src="hero.jpg" class="banner" alt="Team collaborating around a whiteboard">`
```

Rules:
- Always quote the offending element (trimmed if long) and give a concrete corrected snippet, not generic advice.
- Group repeated identical issues into one finding and list the occurrences (e.g. "12 images; first three shown").
- Distinguish confirmed defects from items that need runtime or manual checking (contrast from variables, focus order, screen-reader announcements, focus traps).
- End with a short "What passed" line for categories with no issues, and a note that automated/static review catches only part of WCAG; recommend a manual keyboard pass and a screen-reader spot check (NVDA/VoiceOver), plus axe or Lighthouse for runtime confirmation.
- If the user asks you to fix the issues, apply the fixes with minimal edits and keep visual design unchanged unless contrast requires a colour change (propose the nearest passing colour).
