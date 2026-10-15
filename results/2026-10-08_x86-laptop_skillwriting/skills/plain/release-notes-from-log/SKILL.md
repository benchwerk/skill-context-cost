---
name: release-notes-from-log
description: Turn the git log between two tags into user-facing release notes, grouped into breaking changes, features and fixes, in plain language, skipping chores and merge commits. Use when the user asks for release notes, a changelog, or "what changed" between two tags or versions (e.g. v1.2.0..v1.3.0).
---

# Release notes from a git log

Produce release notes for end users (not developers) from the commits between two tags.

## Inputs

- Two refs: the older tag (`FROM`) and the newer tag (`TO`). If the user gives only one, use the previous tag as `FROM` (`git describe --tags --abbrev=0 TO^`). If they give none, use the latest two tags (`git tag --sort=-v:refname | head -2`). Infer; don't ask unless no tags exist.
- Verify both refs exist with `git rev-parse --verify FROM TO` and report clearly if not.

## Steps

1. Collect commits, excluding merges:
   ```
   git log FROM..TO --no-merges --format="%h%x09%s%x09%b%x1e"
   ```
   Subject and body both matter: bodies hold `BREAKING CHANGE:` footers and issue/PR references.
2. Classify each commit:
   - **Breaking**: `!` after the type (`feat!:`), a `BREAKING CHANGE:` footer, or wording like "removed", "renamed", "no longer", "requires", "drops support" that changes existing behavior, config, API or CLI flags.
   - **Feature**: `feat`, "add", "support", "introduce", or any new user-visible capability.
   - **Fix**: `fix`, "resolve", "correct", "crash", "regression", or any user-visible bug fix.
   - **Skip**: `chore`, `ci`, `build`, `test`, `style`, `refactor` (unless it changes behavior), `docs` of internal nature, dependency bumps, version bumps, formatting, reverts that cancel out within the range, and merge commits. Also skip commits whose effect users cannot see.
   - Untyped commits: judge by content. If genuinely unclear, prefer skipping over guessing; mention the count of skipped/uncertain commits at the end only if it is more than a few.
3. Merge duplicates: several commits on one change (a feature plus follow-up fixes to it, or a fix plus its revert and reapply) become one entry.
4. Rewrite each entry in plain language:
   - Describe what the user can now do, or what was wrong and is now right, not how the code changed.
   - One sentence, present or past tense consistently (past: "Fixed…", "Added…"). No file names, function names, or commit jargon unless the user would type them (commands, flags, settings).
   - Keep issue/PR numbers in parentheses if present, e.g. `(#123)`.
   - For breaking changes, add what the user must do: "Rename `--foo` to `--bar`."
5. Output in this order, omitting empty sections:

```
# Release TO (YYYY-MM-DD)

## ⚠️ Breaking changes
- …

## New features
- …

## Fixes
- …
```

Breaking changes always come first. Use the tag's date (`git log -1 --format=%as TO`). Order entries within a section by user impact, most important first.

## Rules

- Never invent behavior not supported by the commit message or diff. If a message is too vague to describe, check `git show --stat <hash>` or the diff briefly; if still unclear, skip it.
- Don't include author names, hashes, or internal ticket IDs.
- If every commit is skipped, say so: "No user-facing changes in this range."
- Print the notes in the reply; write to a file (e.g. `RELEASE_NOTES.md`) only if asked.
