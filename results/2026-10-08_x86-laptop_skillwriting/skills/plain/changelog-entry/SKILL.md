---
name: changelog-entry
description: Write a changelog entry for a code change in Keep a Changelog format. Use when the user asks for a changelog entry, release note, or CHANGELOG.md update for a diff, commit, branch, or PR.
---

# Changelog Entry

Write a changelog entry for a code change in Keep a Changelog format.

## Steps

1. Identify the change. Use what the user gave you (diff, commit, PR, description). If none, inspect the working tree or recent commits with `git diff` / `git log`.
2. Decide what a user of the software would notice. Skip pure refactors, test-only changes, and internal tooling unless they change behavior.
3. Write the entry using the format below.
4. If the user names a CHANGELOG file, add the entry under `## [Unreleased]`. Otherwise output the entry only.

## Format

```markdown
## [Short heading]

### Added
- Item

### Changed
- Item

### Fixed
- Item

### Removed
- Item
```

## Rules

- **Heading:** short (about 2-6 words), describes the change as a whole. If adding to an existing changelog, use `## [Unreleased]` and put the short heading as a one-line summary beneath it only if helpful.
- **Groups:** only Added, Changed, Fixed, Removed, in that order. Omit any group with no items; never leave an empty group.
- **One line per item:** a single bullet, no sub-bullets, no wrapped paragraphs.
- **Present tense:** "Adds", "Changes", "Fixes", "Removes" style verbs are fine, but be consistent. Prefer the plain form that reads naturally under the group, e.g. "Export button saves files as CSV" or "Fixes crash when the config file is empty". Do not use past tense ("Added", "Fixed").
- **No internal ticket numbers:** drop references such as `JIRA-123`, `ABC-45`, `#1234` issue/PR numbers, and internal tracker links.
- **User-facing wording:** describe the effect, not the implementation. Avoid file names, function names, and commit-speak unless the audience is developers of a library API.
- **Accuracy:** only list what the change actually does. Do not invent items to fill groups.
- Put breaking changes under Changed or Removed and say so briefly in the line (e.g. "Removes the `--legacy` flag").

## Example

```markdown
## Faster search and CSV export

### Added
- Exports search results to CSV from the results page

### Changed
- Search results load in pages of 50 instead of all at once

### Fixed
- Fixes a crash when the search query is empty

### Removed
- Removes the deprecated `--legacy-search` flag
```
