---
name: commit-message-format
description: Write a git commit message from a staged diff. Use when the user asks for a commit message, or wants to commit staged changes. Produces an imperative subject under 50 characters, a blank line, and a body wrapped at 72 characters that explains why.
---

# Commit message format

Write a commit message for the currently staged changes.

## Steps

1. Run `git diff --staged` to read the staged changes. If nothing is staged, say so and stop.
2. Work out what changed and, more importantly, why it was needed.
3. Write the message in the format below.

## Format

```
<subject>

<body>
```

### Subject

- Imperative mood: "Add", "Fix", "Remove", not "Added" or "Adds".
- Under 50 characters.
- No trailing period.
- Capitalize the first word.
- Say what the commit does, specifically.

### Blank line

Always leave exactly one blank line between subject and body.

### Body

- Wrap every line at 72 characters.
- Explain why the change was made: the problem, the motivation, the trade-offs.
  The diff already shows what changed, so mention it only as needed for context.
- Separate paragraphs with blank lines.
- Omit the body only for trivial changes where the subject says everything.

## Example

```
Retry failed uploads with exponential backoff

Uploads to the storage service failed outright on transient 503s,
forcing users to restart large transfers by hand. Retrying up to
five times with exponential backoff absorbs these short outages
without hammering the service.
```

## Checks before answering

- Subject length is under 50 characters.
- Subject has no trailing period.
- Line 2 is blank.
- No body line exceeds 72 characters.

Output only the commit message, ready to paste, unless the user asks to commit, in which case pass it to `git commit`.
