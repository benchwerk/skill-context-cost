---
name: release-notes-from-log
description: Turn the git log between two tags into user-facing release notes grouped into breaking changes, features and fixes, in plain language, skipping chores and merge commits. Use when the user asks for release notes, a changelog, or "what changed" between two tags or versions.
---

# Release notes from a git log

Write release notes for end users from the commits between two tags.

## Inputs

You need two tags: the previous release (`FROM`) and the new one (`TO`). Take them from the user's message. If only the new tag is given, use the nearest earlier tag: `git describe --tags --abbrev=0 TO^`. If no tags are given, use the latest two from `git tag --sort=-v:refname`, and say which you used.

## Steps

1. Collect commits, excluding merges, with full messages:

   ```
   git log FROM..TO --no-merges --format='%h%x09%s%n%b%n---'
   ```

   Verify both tags exist first (`git rev-parse --verify FROM TO`); if one is missing, report it and stop.

2. Classify each commit:
   - **Breaking change**: a `!` after the type (`feat!:`), a `BREAKING CHANGE:` footer, or a body/subject that removes or renames something public, changes defaults, or requires user action (config, API, CLI flags, migrations).
   - **Feature**: new user-visible capability (`feat`, "add", "support", "introduce").
   - **Fix**: corrects user-visible wrong behavior (`fix`, "fix", "resolve", "correct").
   - **Skip**: `chore`, `ci`, `build`, `test`, `style`, `refactor` without visible effect, dependency bumps, version bumps, release commits, formatting, docs typos, reverts of unreleased work, and merge commits. If a "chore" clearly changes user-visible behavior (for example a dependency bump that fixes a known user-facing bug), include it under the right group.
   - Commits that don't follow conventional-commit style: judge by the diff summary (`git show --stat <hash>`) when the message is unclear.

3. Merge duplicates: several commits about one change become one bullet. A fix to something added in the same range is part of the feature, not a separate fix.

4. Rewrite every kept item in plain language:
   - Describe what the user can now do, or what no longer goes wrong, not how the code changed.
   - No commit hashes, file names, internal function names, or ticket jargon in the bullet. Keep a PR or issue number in parentheses if the log has one, e.g. `(#123)`.
   - One sentence, present tense or past tense consistently, starting with a verb or the affected area.
   - For breaking changes, say what changed, who is affected, and what to do instead.

## Output format

Order sections as below. Omit any section with no items. Breaking changes always come first.

```
# Release notes: TO

## Breaking changes
- **Area:** What changed and what you need to do. 

## Features
- ...

## Fixes
- ...
```

If there are no user-facing changes at all, output a single line saying so rather than inventing content.

Keep the order inside each section by importance, most significant first. Do not add sections for chores, internal changes, or contributors unless asked.

After the notes, add one short line listing how many commits were skipped as non-user-facing, so the user can ask to see them.
