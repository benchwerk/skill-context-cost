---
name: commit-message-format
description: Write a git commit message from a staged diff in a strict format - imperative subject under 50 characters with no trailing period, a blank line, then a body wrapped at 72 characters that explains why the change was made. Use this skill whenever the user asks to write, draft, suggest, or fix a commit message, says "commit this", "what should my commit say", or wants a message for staged changes, even if they don't mention the format.
---

# Commit message format

Turn the staged changes into a commit message that is easy to scan in `git log` and useful to someone reading it months later.

## Steps

1. Read the staged diff with `git diff --staged` (add `--stat` for an overview). If nothing is staged, say so and ask whether to look at unstaged changes instead of inventing a message.
2. Work out the intent: what problem does this change solve, and why was this approach taken? The diff already shows *what* changed; the message's job is to capture what the diff cannot.
3. Write the message in the format below.
4. Verify the constraints (lengths, blank line, no trailing period) before presenting it.

## Format

```
<subject>

<body>
```

### Subject

- Imperative mood, as if completing "If applied, this commit will...": `Add retry to upload client`, not `Added` or `Adds`.
- Under 50 characters (aim for 49 or fewer, counting every character). Short subjects stay readable in one-line logs and tooling that truncates.
- No trailing period.
- Capitalize the first word. Be specific: `Fix off-by-one in pagination` beats `Fix bug`.

### Blank line

Exactly one empty line between subject and body. Git tools use it to separate the two.

### Body

- Wrap every line at 72 characters or fewer.
- Explain *why*: the motivation, the problem or constraint, and any tradeoff or alternative rejected. Mention user-visible or behavioral consequences when relevant.
- Do not narrate the diff line by line; reviewers can read the code.
- Use plain paragraphs separated by blank lines. Short `-` bullets are fine for a list of discrete points.
- Add issue references (e.g. `Fixes #123`) as a final line only if the user or branch name supplies one. Never invent them.
- For a trivially small change where the subject says it all, the body may be omitted, but default to including one when there is any reasoning worth recording.

## Example

```
Cache user permissions per request

Permission lookups hit the database once per check, and a single page
render could trigger dozens of them. Profiling showed this accounted
for most of the latency on the dashboard.

Cache the result on the request object so each user is queried at
most once per request. A longer-lived cache was rejected because
permission changes need to take effect immediately.
```

## Output

Present only the commit message in a code block, unless the user asked for it to be committed, in which case run `git commit` with it. If the diff contains unrelated changes, mention that it may be better split into separate commits, and still provide a message for the whole.
