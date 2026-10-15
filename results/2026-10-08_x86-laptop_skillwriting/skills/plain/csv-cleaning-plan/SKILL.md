---
name: csv-cleaning-plan
description: Inspect a CSV file and write a cleaning plan before changing anything. Profiles column types, missing values, duplicates, inconsistent casing and mixed date formats, and gives the exact fix for each issue. Use when the user asks to audit, profile, check, or plan the cleanup of a CSV or tabular text file, or says "what's wrong with this CSV". The original file is never modified.
---

# CSV Cleaning Plan

Produce a written plan describing what is wrong with a CSV and exactly how to fix each problem. **Do not modify, overwrite, or reformat the original file.** Do not apply the fixes unless the user asks afterward.

## Ground rules

- Read-only on the source file. Run inspection with scripts that only read it (pandas, Python `csv`, or shell tools). Never write back to it, never use in-place flags (`sed -i`, `to_csv(same_path)`).
- Write the plan to a new file next to the CSV: `<csv-name>.cleaning-plan.md`, unless the user names another location. Never overwrite an existing file there; add a numeric suffix if needed.
- Load every column as text first (`pandas.read_csv(path, dtype=str, keep_default_na=False)`), so inspection does not silently coerce values. Infer types yourself from the strings.
- Report counts and example row numbers, not guesses. Row numbers are 1-based data rows plus the header, so they match what the user sees in a spreadsheet; state this.

## Procedure

1. **File-level facts**: encoding (try utf-8, utf-8-sig for a BOM, then cp1252/latin-1), delimiter, quoting, line endings, header presence, row and column count, ragged rows (rows with a different field count), blank lines, duplicate or blank column names, leading/trailing whitespace in headers.
2. **Per-column profile**, for every column: inferred type, non-empty count, distinct count, min/max (or shortest/longest for text), top 5 values with counts, and a few sample values.
3. **Missing values**: count empties and placeholder tokens (`NA`, `N/A`, `null`, `none`, `-`, `?`, `0000-00-00`, `999`, `-1`, whitespace-only). Report per column with percent. Flag columns that are more than 50% missing and columns that should be required (ids, keys).
4. **Duplicates**: exact duplicate rows; duplicates on the likely key column(s); near-duplicates after normalizing case, whitespace, and punctuation. List the row numbers in each group and which one to keep.
5. **Casing and text consistency**: values that collide once case/whitespace/accents are normalized (`NY`, `ny`, `New York `), mixed title/upper/lower within categorical columns, stray internal whitespace, inconsistent spelling variants. List each variant group with counts and the canonical form.
6. **Dates**: identify date columns, then classify each value's format (`YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, `D-Mon-YY`, with time/without, timezone, epoch). Report the format mix with counts. For slash dates, determine whether day-first or month-first is used by looking for values where the first part is greater than 12 (or the second is); if ambiguous, say so and require a decision rather than guessing. Also flag impossible dates, two-digit years, and out-of-range values.
7. **Type problems**: numbers with currency symbols, thousands separators, or trailing units; percent strings; booleans in mixed forms (`Y/yes/TRUE/1`); numeric ids with leading zeros that must stay text (zip codes, phone numbers); mixed types in one column; outliers and impossible values (negative ages, future birth dates).
8. **Cross-column checks** where obvious: start date after end date, totals that do not match parts, a code that maps to several labels.

## Output format for the plan

Use this structure:

```
# Cleaning plan: <file name>
Source: <path> (unchanged) | Rows: N | Columns: N | Encoding / delimiter: ...

## Summary
<3-6 lines: biggest problems and the estimated number of rows affected>

## Issues
| # | Column | Issue | Rows affected | Example (row: value) | Exact fix | Needs decision? |
|---|--------|-------|---------------|----------------------|-----------|-----------------|

## Column types (target schema)
| Column | Current | Target type | Notes |

## Decisions needed from you
<each ambiguity with options and a recommended default>

## Suggested order of operations
<numbered steps; e.g. fix encoding -> trim whitespace -> normalize placeholders to empty -> normalize casing -> parse dates -> cast types -> dedupe>

## Verification checks after cleaning
<row count expected, null counts expected, uniqueness of key, date range>
```

### Writing "Exact fix"

Every issue needs a concrete, reproducible fix, not "clean the column". Examples:

- Trim: `df[col] = df[col].str.strip()`
- Placeholders to missing: replace `{"N/A","NA","null","-",""}` with empty in `phone`.
- Casing: map every variant of `state` to uppercase two-letter codes; list the mapping table explicitly for any non-mechanical cases (`"New York" -> "NY"`).
- Dates: parse `signup_date` with the formats found, in this order, writing `YYYY-MM-DD` (ISO 8601); rows 14, 92 are ambiguous and need a decision.
- Types: strip `$` and `,` from `amount`, cast to decimal with 2 places; keep `zip` as text, left-padded to 5 digits.
- Duplicates: drop rows 31 and 77 (exact copies of rows 30 and 76); for key `email` conflicts, keep the row with the latest `updated_at`.

For each fix say what should happen when the value cannot be handled (set to empty and log, or leave and flag), and never propose silently dropping data without stating the row count.

Where it helps, include a short runnable snippet at the end of the plan that implements all fixes and writes to a **new** file (`<name>.cleaned.csv`), clearly labeled as not yet run.

## Final reply to the user

Give the path of the plan file, the top 3-5 issues with row counts, and the list of decisions needed. State explicitly that the original CSV was not changed. Offer to apply the plan, but do not do it unprompted.
