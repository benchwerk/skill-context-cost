---
name: release-notes-from-log
description: Turn a git log between two tags (or refs) into user-facing release notes, grouped into Breaking Changes, Features, and Fixes, written in plain language, with chores and merge commits skipped. Use this skill whenever the user asks for release notes, a changelog, "what's new", or a release summary from git history, tags, or a version range (e.g. "notes for v1.2.0..v1.3.0"), even if they don't say "release notes" explicitly.
---

# Release notes from a git log

Release notes are for people who use the product, not people who work on it. The job is to translate commit history into what changed for the reader, and to make sure nobody gets surprised by something that breaks their setup.

## 1. Get the log

Identify the two tags (older `FROM`, newer `TO`). If the user gave only one, use the previous tag: `git describe --tags --abbrev=0 TO^`. If the user pasted a log, use that instead of running git.

```bash
git log FROM..TO --no-merges --format='%h%x09%s%n%b%n---'
```

`--no-merges` drops merge commits. Bodies matter: breaking changes are often flagged there (`BREAKING CHANGE:` footers) and not in the subject. If squash-merged PRs make the subject the only information, work from that.

## 2. Classify each commit

- **Breaking change**: a `!` after the type (`feat!:`), a `BREAKING CHANGE` footer, or a body/subject that removes or renames something public (commands, flags, config keys, API fields, endpoints), changes defaults, or raises minimum requirements. Judge by effect on users even when the commit isn't labeled.
- **Feature**: new capability or a meaningful improvement (`feat`, "add", "support", noticeable performance gains).
- **Fix**: bug corrections (`fix`, "resolve", "correct", security fixes).
- **Skip**: chores, CI, build, deps bumps with no user impact, refactors, tests, docs-only tweaks, formatting, version bump commits, reverts that cancel out within the range, and merge commits. If a dependency bump fixes a user-visible problem or security issue, keep it as a fix.

When a commit is ambiguous, ask what the user would notice. If nothing, skip it.

## 3. Write the entries

- Describe the outcome for the user, not the implementation. "Exports no longer fail on files with spaces in the name" beats "fix path quoting in exporter".
- One line each, plain language, no jargon, no commit hashes, no conventional-commit prefixes, no scope tags unless they help the reader find their area.
- Merge related commits into a single entry (a feature plus its follow-up fixes is one feature).
- For each breaking change, say what changed, who is affected, and what to do (the migration step). Infer it from the diff or body; if the right action isn't knowable from the log, say so rather than inventing one.
- Credit PR numbers or issue links only if the log already contains them and the user wants them; keep them at line end.

## 4. Output format

Breaking changes come first because they are the entries that cost readers time if missed. Omit any section that is empty.

```markdown
# <Project> <TO version>

## Breaking changes
- **<What changed>.** <Who is affected>. To upgrade: <action>.

## Features
- <Plain-language description>

## Fixes
- <Plain-language description>
```

If there are no breaking changes, don't include the heading or write "none"; just begin with Features. Order entries within a section by importance to users, not by date.

After the notes, add a brief line listing how many commits were skipped as internal, plus any ambiguous commits you were unsure about, so the user can overrule you.
