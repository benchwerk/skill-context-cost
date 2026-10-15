---
name: changelog-entry
description: Write a changelog entry for a code change in Keep a Changelog format. Use when the user asks for a changelog entry, release note, or "what changed" summary for a diff, commit, branch, or PR.
---

# Changelog Entry

Turn a code change into a short changelog entry in [Keep a Changelog](https://keepachangelog.com) format.

## Steps

1. Identify the change. Use what the user gave you (diff, commit, branch, PR, description). If nothing was given, read the current uncommitted diff or the latest commit.
2. Decide what a user of the software would notice. Skip pure refactors, test-only changes, and formatting unless they alter behavior.
3. Sort each item into one group:
   - **Added**: new features or capabilities
   - **Changed**: modified behavior of existing features
   - **Fixed**: bug fixes
   - **Removed**: features, options, or APIs taken out
4. Write the entry using the format below.

## Format

```markdown
## <Short heading>

### Added
- <One line>

### Changed
- <One line>

### Fixed
- <One line>

### Removed
- <One line>
```

## Rules

- The heading is short (about 3-8 words) and names the change, not a version number or date, unless the user supplies one.
- Include only the groups that have items. Omit empty groups. Keep the order Added, Changed, Fixed, Removed.
- One line per item. No sub-bullets, no multi-sentence items.
- Use present tense and an active verb: "Adds dark mode toggle", "Fixes crash when the config file is empty", "Removes the deprecated `--legacy` flag".
- Describe the effect for the user, not the implementation. Prefer "Fixes slow search on large projects" over "Replaces nested loop with a hash map".
- Never include internal ticket or issue numbers (e.g. `JIRA-123`, `ABC-45`, `#1234`), and don't mention them in the heading. Drop them even if they appear in commit messages or branch names.
- Don't invent changes. Only list what the change actually does. If something is unclear, describe it conservatively.
- Output only the entry, with no preamble. If the user asked for it to be saved, add it to the file they name (under Unreleased in `CHANGELOG.md` if one exists and none was named).

## Example

```markdown
## Faster project search

### Added
- Adds a `--include` option to limit search to matching paths

### Changed
- Searches ignore files listed in `.gitignore` by default

### Fixed
- Fixes a crash when searching an empty directory

### Removed
- Removes the deprecated `--legacy-index` flag
```
