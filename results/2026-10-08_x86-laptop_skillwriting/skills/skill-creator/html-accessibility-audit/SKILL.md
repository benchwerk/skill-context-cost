---
name: html-accessibility-audit
description: Audit an HTML page or snippet for accessibility problems (WCAG 2.2) and report each finding with the offending element and a concrete fix. Covers missing or poor alt text, heading order, form labels, colour contrast, keyboard focus and operability, and ARIA misuse. Use this skill whenever the user asks to check, review, audit, or lint HTML, a template, or a component for accessibility, a11y, WCAG, screen reader support, or keyboard navigation, even if they don't use the word "audit".
---

# HTML Accessibility Audit

Review the given HTML (a file, a pasted snippet, or a template/component file) and produce a findings report. Each finding names the element and gives a fix the author can paste in. Static review cannot prove a page is accessible, so say what you could not verify rather than implying a clean bill of health.

## Process

1. Read the whole file(s) first. If the page pulls in CSS (inline `<style>`, linked local stylesheets), read those too, since contrast, focus outlines and `display:none` live there. If the markup is a framework template (JSX, Vue, etc.), audit the rendered intent and note that dynamic content was not seen.
2. Run each check below. Use Grep for quick sweeps (`<img`, `<input`, `role=`, `tabindex`, `outline`), but read the surrounding markup before reporting, because a grep hit is not a finding until you've confirmed it.
3. Report using the output format at the end. Do not edit the user's files unless asked; offer the fixes in the report.

## Checks

### 1. Images and non-text content (WCAG 1.1.1)
- `<img>` with no `alt` attribute: error. Decorative images need `alt=""`, informative ones need a short description of purpose, not "image of...".
- Alt text that is a filename, "image", "photo", or repeats adjacent text.
- `<input type="image">`, `<area>`, and `<svg>` that convey meaning need a text alternative (`alt`, `<title>` with `role="img"` and `aria-labelledby`, or `aria-label`). Decorative SVG gets `aria-hidden="true"`.
- Icon-only buttons/links (icon font, background image) with no accessible name.
- Meaningful `<video>`/`<audio>`: flag missing captions `<track>` or transcript as "needs manual check".

### 2. Document structure and headings (1.3.1, 2.4.1, 2.4.2, 3.1.1)
- Missing `lang` on `<html>`, missing or empty `<title>`.
- Heading levels skipping (h1 to h3), multiple or zero `<h1>`, headings chosen for size rather than structure, empty headings.
- Fake headings: bold `<div>`/`<p>` styled to look like headings. Fake lists/tables built from `<br>` or divs.
- Missing landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`), duplicated landmarks of the same type with no distinguishing `aria-label`.
- No skip link when there is a large block of navigation before main content.
- Layout tables, or data tables lacking `<th>` with `scope`, and `<caption>` where helpful.
- Links: empty links, "click here"/"read more" with no distinguishing context, `<a>` without `href` used as a button.

### 3. Form labels and errors (1.3.1, 3.3.1, 3.3.2, 4.1.2)
- Each `<input>`, `<select>`, `<textarea>` needs a programmatic name: `<label for>` matching an `id`, a wrapping `<label>`, `aria-label`, or `aria-labelledby`. `placeholder` alone is not a label.
- Labels whose `for` points to a nonexistent or duplicate `id`.
- Duplicate `id` values anywhere (breaks label and ARIA references).
- Related radios/checkboxes without `<fieldset>`/`<legend>`.
- Required fields indicated only by colour or an asterisk with no text or `required`/`aria-required`.
- Missing `autocomplete` on common personal-data fields (name, email, address, password) (1.3.5).
- Error messages not associated with fields (`aria-describedby`, `aria-invalid`), or not announced (`role="alert"` / live region).
- Buttons with no text/name; `<input type="submit">` with empty `value`.

### 4. Colour contrast (1.4.3, 1.4.11, 1.4.1)
Static review can only compute contrast when both colours are literally present in the CSS. For those pairs, compute the WCAG ratio: relative luminance L = 0.2126R + 0.7152G + 0.0722B on linearised sRGB channels (c/255 <= 0.03928 ? c/12.92 : ((c/255+0.055)/1.055)^2.4); ratio = (L1+0.05)/(L2+0.05).
- Thresholds: 4.5:1 normal text, 3:1 large text (>= 24px, or >= 18.66px bold), 3:1 for UI component boundaries and focus indicators.
- Report the computed ratio and a nearby compliant colour as the fix.
- Where colours come from variables, images, gradients, opacity, or runtime theming, do not guess: list as "contrast notes: verify with a tool" and name the selector.
- Flag information conveyed by colour alone (e.g. red text as the only error cue, links distinguished from text only by colour).
- Light-grey placeholder and disabled-looking text on white is a common failure worth checking.

### 5. Keyboard and focus (2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.4.11)
- `outline: none` / `outline: 0` / `:focus { outline... }` removal without a replacement visible focus style.
- Click handlers (`onclick`) on non-interactive elements (`div`, `span`, `li`) with no `role`, `tabindex="0"` and key handling. Best fix: use a real `<button>` or `<a href>`.
- Positive `tabindex` values (`tabindex="3"`): break natural order; use `0` or `-1` and fix DOM order.
- `tabindex="0"` on elements that are not interactive, adding useless tab stops.
- Focusable elements hidden from view (`display:none` is fine; off-screen or `aria-hidden="true"` containing focusable children is not).
- `<a href="#">` or `href="javascript:..."` acting as buttons.
- Modals/menus/custom widgets: check for focus management (move focus in, trap while open, restore on close, Escape closes) and flag as manual check if the script is not available.
- Hover-only content (tooltips/menus on `:hover` with no `:focus` equivalent).
- Auto-focus, auto-advancing carousels, or autoplaying media without pause control.
- Touch/pointer target size under 24x24 CSS px for obvious cases (2.5.8).

### 6. ARIA misuse (4.1.2, 1.3.1)
The first rule of ARIA: prefer native HTML. Bad ARIA is worse than none because it overrides what assistive tech would have inferred.
- Redundant or conflicting roles: `<button role="button">`, `<nav role="navigation">`, `<a role="button">` without keyboard support, `<h2 role="tab">`.
- Invalid role names, invalid `aria-*` attributes or values (typos, `aria-hidden="yes"`).
- `aria-hidden="true"` on focusable elements or on large containers that hold content users need.
- `aria-label` on elements where it is ignored (`div`/`span` with no role) or that contradicts visible text (label should start with the visible text, 2.5.3).
- `aria-labelledby` / `aria-describedby` / `aria-controls` pointing at missing ids.
- Required owned elements/states missing: `role="tab"` without `tablist`/`tabpanel` and `aria-selected`; `role="menu"` used for ordinary navigation; `role="listbox"`/`option`, `combobox` without `aria-expanded`/`aria-controls`; custom checkbox/switch without `aria-checked`; toggles without `aria-expanded`/`aria-pressed`.
- `role="presentation"`/`none` on elements that are focusable or carry meaning (e.g. a table with headers).
- Live regions: `aria-live="assertive"` overuse; `role="alert"` on content present at page load.
- Static `aria-*` state that never updates (`aria-expanded="false"` hard-coded on a widget that opens): flag as manual check.

## Severity

- **Critical**: blocks a task for some users (unlabelled form control, keyboard-inaccessible control, focus removed, missing accessible name on a button/link, aria-hidden focusable).
- **Serious**: significant barrier or clear WCAG A/AA failure (missing alt, heading structure broken, contrast below threshold, invalid ARIA).
- **Moderate**: degrades experience or best practice (redundant roles, vague link text, missing landmarks).
- **Needs manual check**: cannot be decided from static markup.

## Output format

Start with a one-paragraph summary: what was audited, counts by severity, and the top two or three issues to fix first. Then list findings grouped by severity. Use this entry template for each:

```
### [Severity] Short title: WCAG x.x.x (level)
- Element: `<img src="hero.jpg" class="banner">` (file:line if known)
- Problem: what is wrong and who it affects
- Fix:
  <img src="hero.jpg" class="banner" alt="Team collaborating around a whiteboard">
```

Rules for the entries:
- Quote the real element, trimmed to the relevant attributes, with file and line number when available. Never invent markup that is not in the source.
- The fix is concrete corrected code or CSS, not advice like "add a label". If the right text depends on content you can't know (e.g. alt text), supply a sensible placeholder and say it needs the author's wording.
- Collapse repeats: when the same issue occurs many times (30 images lacking alt), show one example, list the count and line numbers, and give one fix pattern.
- End with a **Needs manual check** list (contrast from non-literal colours, focus order in scripted widgets, screen-reader announcements, captions) and a **Passed checks** line listing categories with no problems found, so the reader knows what was covered.
- If nothing is wrong in a category, say so briefly. Do not pad the report with speculative issues.
