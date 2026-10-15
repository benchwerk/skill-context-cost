---
name: html-accessibility-audit
description: Audit an HTML page or snippet for accessibility problems (missing alt text, heading order, form labels, colour contrast, keyboard focus, ARIA misuse) and report each finding with the element and a concrete fix. Use when the user asks for an accessibility, a11y, or WCAG review of HTML, a template, or a component.
---

# HTML accessibility audit

Review the HTML the user points at (a file path, a pasted snippet, or a rendered template) and report accessibility problems. Each finding names the element and gives the fix. Static analysis only: say so where a check needs a browser or real colour values.

## Process

1. Read the target file(s). If given a directory, audit `.html`, `.htm`, and template files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.erb`, `.njk`) that contain markup. Follow linked or inline CSS only as far as needed for contrast and focus checks.
2. Run every check below. Do not skip a category because the first one produced findings.
3. Report using the output format at the end. Cite line numbers when the source is a file.

## Checks

### 1. Text alternatives
- `<img>` without an `alt` attribute: error. Fix: add a meaningful `alt`.
- Decorative images (spacers, icons beside text that repeats it): should have `alt=""`, not a missing `alt`.
- Weak alt text: filenames (`alt="IMG_0412.jpg"`), "image of", "picture", or text that duplicates adjacent text.
- `<input type="image">`, `<area>`, and `<svg role="img">` need `alt` / `aria-label` / `<title>`.
- Icon-only buttons and links (`<button><i class="icon-x"></i></button>`) need an accessible name via `aria-label` or visually hidden text.
- `<video>`/`<audio>`: note missing captions (`<track kind="captions">`) or transcript.

### 2. Document structure and headings
- Missing `lang` on `<html>`; empty or missing `<title>`.
- Heading order: flag skipped levels (h2 followed by h4), a missing `h1` or multiple unrelated `h1`s, and headings chosen for visual size rather than structure. Fix by changing the level and styling with CSS.
- Empty headings.
- Missing landmarks: no `<main>`, navigation not in `<nav>`, multiple `<nav>`s without distinguishing `aria-label`s. Page lacks a skip link when there is repeated header navigation.
- Layout tables, or data tables without `<th>`, `scope`, or `<caption>`.
- Links: empty links, "click here" / "read more" without context, `<a>` without `href` used as a button.

### 3. Forms
- Every `<input>`, `<select>`, `<textarea>` needs a programmatic label: `<label for>` matching an `id`, a wrapping `<label>`, `aria-label`, or `aria-labelledby`. A `placeholder` alone is not a label.
- Duplicate `id`s that break `for`/`aria-labelledby` references.
- Related controls (radio/checkbox groups) should be in `<fieldset>` with `<legend>`.
- Required fields: `required` or `aria-required`, plus a visible indication that is not colour alone.
- Error messages should be linked with `aria-describedby` and `aria-invalid="true"`; dynamic errors should live in a `role="alert"` or `aria-live` region.
- Missing or wrong `autocomplete` on personal-data fields (name, email, address, etc.).
- Buttons: `<button>` or `<input type="submit">` must have text or a name; `<div onclick>` pretending to be a button is a keyboard finding too.

### 4. Colour contrast (notes)
Exact contrast needs computed colours, so give notes rather than certainties unless both colours are literal in the source.
- Compute the ratio when foreground and background are both literal. Thresholds (WCAG 2.x AA): 4.5:1 normal text, 3:1 large text (18.66px bold or 24px regular and up), 3:1 for UI component boundaries and focus indicators.
- Flag likely-risk patterns even when not computable: light grey text (`#999` on white is about 2.8:1, which fails), text over images or gradients, placeholder text, disabled-looking text that is actually active, and white text on mid-tone brand colours.
- Flag information conveyed by colour alone (red/green status, links distinguished only by colour inside body text).
- Suggest a specific passing replacement colour where possible, for example `#767676` is the lightest grey that passes on white.

### 5. Keyboard and focus
- Positive `tabindex` values (`tabindex="3"`): fix by removing and fixing DOM order.
- `tabindex="-1"` on controls that should be reachable.
- Click handlers on non-interactive elements (`<div onclick>`, `<span onclick>`) without `role`, `tabindex="0"`, and key handlers; fix by using `<button>` or `<a href>`.
- CSS removing focus styles: `outline: none` / `outline: 0` without a replacement `:focus-visible` style. Focus indicator needs at least 3:1 contrast against adjacent colours.
- `autofocus` that moves focus unexpectedly; `accesskey` conflicts.
- Modals, menus, and dialogs: need focus moved in on open, trapped while open, and returned on close; `Escape` should close. Prefer `<dialog>` with `showModal()`.
- Hover-only interactions (`:hover` menus, `onmouseover`) with no keyboard/focus equivalent.
- Hidden-content traps: `display:none` / `hidden` content that remains focusable through `visibility` tricks or off-screen positioning.
- Missing `:focus-visible` on custom controls; target size under 24x24 CSS px.

### 6. ARIA misuse
Rule of thumb: no ARIA is better than bad ARIA, and native HTML beats ARIA.
- Redundant roles: `<button role="button">`, `<nav role="navigation">`, `<a href role="link">`.
- Conflicting roles: `<h2 role="button">`, `<ul role="menu">` without menu semantics, `role="presentation"` on focusable elements.
- Invalid or misspelled `role` or `aria-*` attributes; invalid values (`aria-hidden="yes"`, `aria-expanded="1"`).
- `aria-hidden="true"` on or around focusable elements (focus lands on something invisible to screen readers).
- `aria-labelledby` / `aria-describedby` / `aria-controls` pointing to an `id` that does not exist.
- Required owned elements or states missing: `role="tab"` without `tablist`/`tabpanel` and `aria-selected`; `role="checkbox"` without `aria-checked`; `role="combobox"` without `aria-expanded` and `aria-controls`; `role="listbox"`/`option` without keyboard behaviour; `role="img"` without a name.
- `aria-label` on elements that do not support naming (generic `div`/`span` without a role).
- `aria-live` regions that are inserted at the same time as their content (they must exist before the update).
- Custom widgets with ARIA roles but no keyboard handling (arrow keys, Home/End, Escape per the ARIA Authoring Practices pattern).

## Severity

- **Critical**: blocks a task for some users (unlabelled form control, keyboard-inaccessible control, focus trap, `aria-hidden` on focusable content, missing alt on informative image).
- **Serious**: major barrier with a workaround (skipped headings, contrast failure, focus outline removed, broken ARIA reference).
- **Moderate**: degraded experience (redundant roles, vague link text, missing landmarks).
- **Minor / note**: best-practice and items needing manual verification.

## Output format

Start with a one-line summary: files audited and counts per severity. Then group findings by category in the order above, most severe first within each group. Use this shape for every finding:

```
[Critical] Form labels — line 42
Element: <input type="email" id="email" placeholder="Email">
Problem: No programmatic label; placeholder disappears on input and is not a reliable accessible name.
Fix: <label for="email">Email</label>
     <input type="email" id="email" autocomplete="email">
WCAG: 1.3.1, 3.3.2, 4.1.2
```

Rules for the report:
- Always include the actual element (trimmed to the relevant opening tag) and a concrete corrected snippet, not general advice.
- Collapse identical issues into one finding listing all affected lines (for example, "12 images missing alt: lines 10, 14, ...") with one example fix.
- Cite the WCAG 2.2 success criterion for each finding.
- End with **Needs manual verification**: a short list of what static analysis cannot confirm (computed contrast, actual screen reader output, focus order in the rendered page, dynamic behaviour), and **What passed**: one line naming categories with no findings.
- If nothing is found in a category, say so; never invent findings. If the input is a fragment, note that page-level checks (title, lang, landmarks) were skipped.

If the user asks for fixes to be applied, edit the file with the corrections above and re-list what changed. Otherwise do not modify the audited files.
