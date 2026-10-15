---
name: changelog-entry
description: Write a changelog entry for a code change in Keep a Changelog format. Use this skill whenever the user asks for a changelog entry, release notes, a CHANGELOG.md update, or a summary of a diff, commit, or pull request for users, even if they don't say "Keep a Changelog".
---

# Changelog entry

Turn a code change (diff, commit, PR description, or the user's own summary) into a short changelog entry in Keep a Changelog style. Readers scan changelogs to learn what affects them, so the entry should be brief, user-facing, and consistent.

## Steps

1. Identify the change. If it isn't in the conversation, inspect it (`git diff`, `git log`, the named PR or files).
2. Decide what a user of the software would notice. Skip pure refactors, test-only changes, and internal tooling unless they change behavior.
3. Sort each item into one group:
   - **Added**: new features or capabilities
   - **Changed**: altered behavior of existing functionality
   - **Fixed**: bug fixes
   - **Removed**: features or options taken away
4. Write the entry using the format below.

## Format

```markdown
## Short heading describing the change

### Added
- Supports exporting reports as CSV.

### Fixed
- Prevents the upload dialog from closing on network errors.
```

Rules:
- Start with a short heading (about 3–8 words) that names the change. Use the version and date instead only if the user supplies them, e.g. `## [1.4.0] - 2026-10-08`.
- Use only the groups that have items, in this order: Added, Changed, Fixed, Removed. Empty groups are noise.
- One line per item, with no sub-bullets or wrapped paragraphs.
- Use present tense and describe what the software does now ("Adds…", "Fixes…", or a plain statement like "Supports…"). Pick one style and keep it consistent within the entry.
- Describe the effect on the user, not the implementation ("Fixes crash when the config file is empty", not "Adds null check in parseConfig").
- Leave out internal ticket numbers and references (JIRA-123, #456, issue links, commit hashes). They mean nothing to readers, and the user may not want them public. If a ticket ID appears in the source material, drop it and keep the description.
- Do not invent changes the evidence doesn't support. If a change is ambiguous, describe only what you can confirm.

## Output

Return only the entry as markdown, ready to paste into a CHANGELOG.md. If the user names a changelog file, insert the entry under its `Unreleased` section or at the top, matching the file's existing style.
