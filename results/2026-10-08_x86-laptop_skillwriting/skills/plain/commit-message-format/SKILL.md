---
name: commit-message-format
description: Write a git commit message from a staged diff. Use when the user asks for a commit message, wants to commit staged changes, or asks to summarize a staged diff as a commit. Produces an imperative subject under 50 characters, a blank line, and a body wrapped at 72 characters that explains why.
---

# Commit Message Format

Write a commit message for the currently staged changes.

## Steps

1. Run `git diff --staged` (add `--stat` for an overview). If nothing is staged, say so and stop; do not guess from unstaged changes.
2. Read the diff to understand what changed and, more importantly, why. Use `git log -n 10 --oneline` to pick up the repo's conventions (e.g. a `feat:` prefix or scope tags) and follow them if present.
3. Write the message in the format below.
4. Output the message in a code block. Commit only if the user asked you to.

## Format

```
<subject>

<body>
```

### Subject
- Imperative mood: "Add", "Fix", "Remove", not "Added" or "Adds".
- Under 50 characters (aim for 40-49; count them).
- No trailing period.
- Capitalize the first word, unless the repo's convention says otherwise.
- Describe the change as a whole, not a file list.

### Blank line
- Exactly one blank line between subject and body.

### Body
- Wrap every line at 72 characters or fewer.
- Explain why the change is needed: the problem, motivation, or constraint. The diff already shows what changed, so mention what only where it is not obvious.
- Note notable trade-offs, alternatives rejected, or side effects.
- Use plain paragraphs separated by blank lines; bullets are fine for discrete items.
- Reference issues at the end if known (e.g. `Fixes #123`). Never invent issue numbers.
- Skip the body only for truly trivial changes (typo, formatting); then output just the subject.

## Example

```
Cache user lookups in the session middleware

Every request hit the database to reload the user, which added about
40 ms to p95 latency under load. Cache the result for the lifetime of
the request so repeated lookups reuse it.

The cache is per-request only, so no invalidation is needed.
```

## Checklist before answering
- Subject < 50 chars, imperative, no period.
- Blank line after subject.
- No body line > 72 chars.
- Body says why, not just what.
