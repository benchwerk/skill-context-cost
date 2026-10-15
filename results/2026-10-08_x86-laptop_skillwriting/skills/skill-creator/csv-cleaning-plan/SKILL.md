---
name: csv-cleaning-plan
description: Inspect a CSV file and produce a written data-cleaning plan BEFORE any cleaning happens, without modifying the original file. Covers column types, missing values, duplicate rows, inconsistent casing, and mixed date formats, with the exact fix for each issue. Use this skill whenever the user wants to audit, profile, review, or "look at" a CSV, asks how to clean or tidy a CSV, mentions messy data, dupes, blank cells, bad dates, or inconsistent capitalization in a .csv file, or wants a plan before transforming data, even if they never say "cleaning plan".
---

# CSV Cleaning Plan

Produce a reviewable plan that says what is wrong with a CSV and exactly how to fix each problem. The plan comes first so the user can approve or adjust it before any data changes. This skill is strictly read-only on the source file.

## Ground rules

- Never modify, overwrite, rename, or reformat the original CSV. Open it read-only.
- Do not write a cleaned copy. Only the plan is produced, unless the user separately asks to apply it afterwards.
- Save the plan as `<csv-basename>-cleaning-plan.md` next to where the user is working (not inside the CSV's folder if that could be unwanted; default to the current directory). Also summarize the headline findings in chat.
- Base every claim on measured evidence (counts, row numbers, sample values). Do not guess from column names alone.

## Step 1: Inspect

Load the file with a tool that does not guess aggressively. In pandas, read everything as strings first (`dtype=str, keep_default_na=False`) so nothing is silently coerced, then analyze. Record:

- Row and column count, delimiter, encoding, header presence, and any BOM.
- Per column: inferred type, non-empty count, distinct count, 5 sample values, min/max length.

If the file is large, profile the full file with streaming or chunked reads rather than a sample, since duplicates and rare bad values hide in the tail. A short script is fine; run it from a scratch location, not by editing the CSV.

## Step 2: Check each issue category

**Column types.** For each column, decide the intended type (integer, decimal, boolean, date/datetime, categorical, free text, identifier). Flag values that break that type (e.g. `N/A` or `$1,200` in a numeric column, leading zeros in IDs such as ZIP codes that must stay text). Report the count and examples of offending values.

**Missing values.** Count true blanks plus placeholder tokens: `NA`, `N/A`, `null`, `NULL`, `none`, `-`, `?`, whitespace-only, `0` or `1900-01-01` where clearly a sentinel. Report per-column percentage. Choose a fix per column based on meaning, not by default:
- Key/ID missing: flag rows for review or drop.
- Numeric: leave null, or impute (median/mean/constant), stating why.
- Categorical: set to an explicit `Unknown`, or leave null.
- Column mostly empty (>~80%): recommend dropping or confirming with the owner.

**Duplicates.** Check both exact duplicate rows and duplicates on the likely key (ID, email, or name+date). Also check duplicates after normalizing case and whitespace, since those are the ones that slip through. Report counts and a few example row numbers. State the keep rule (first, last, most complete row, most recent by a date column) and why.

**Inconsistent casing and spacing.** For text and categorical columns, group values by `strip().casefold()` and list groups with more than one spelling (e.g. `NYC`, `nyc`, `New York`). Flag leading/trailing/double whitespace. Give the target form per column (lowercase for emails, Title Case for names, UPPER for codes) and a mapping table for variants that normalization will not merge.

**Date formats.** Detect each distinct pattern per date column (`2024-03-05`, `03/05/2024`, `5 Mar 24`, with/without time, timezone). Count rows per pattern. Call out ambiguity explicitly: `03/05/2024` could be March 5 or May 3. Resolve it with evidence (any value with a day > 12 in the same column, source locale) or mark it as needing a user decision. Target format: ISO 8601 (`YYYY-MM-DD`, or full datetime with timezone) unless the user states otherwise. List unparseable values separately.

Also note anything else notable you run across (negative values where impossible, outliers, mixed units, stray header rows, trailing totals), but keep the focus on the five categories above.

## Step 3: Write the plan

Use this structure:

```markdown
# Cleaning plan: <file name>

## Snapshot
Rows, columns, encoding, delimiter, headline issue counts. State that the original is untouched.

## Column overview
| Column | Detected type | Intended type | Missing | Distinct | Issues |

## Issues and fixes
For each issue, in priority order (most rows affected or most damaging first):
### N. <short title>  (column(s), rows affected)
- **Evidence:** counts and 3-5 example values/row numbers
- **Fix:** exact, reproducible action (e.g. `df["state"] = df["state"].str.strip().str.upper()`; "parse `signup_date` with formats `%m/%d/%Y` then `%Y-%m-%d`, output `%Y-%m-%d`")
- **Risk / decision needed:** anything ambiguous, or "none"

## Execution order
Numbered order to apply fixes (trim whitespace -> normalize placeholders to null -> fix casing -> parse dates/types -> dedupe), with why the order matters. Deduplicate last so normalization can reveal hidden duplicates.

## Open questions
Decisions only the user can make.

## Safety
Apply the plan to a copy written to a new filename; keep the original as the source of truth.
```

Make each fix concrete enough that someone could execute it without re-analyzing the data: name the column, the exact rule, the target format, and the row counts expected to change. Where a mapping is needed, include the full mapping table.

## Step 4: Hand off

Tell the user where the plan is saved, list the top issues with counts, list the open questions, and ask whether to apply the plan to a new copy. Do not apply it unprompted.
