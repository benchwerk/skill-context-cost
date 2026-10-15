---
name: csv-cleaning-plan
description: Inspect a CSV file and write a cleaning plan before changing anything. Covers column types, missing values, duplicates, inconsistent casing and date formats, with the exact fix for each issue. Never modifies the original file. Use when the user asks to profile, audit, or plan the cleanup of a CSV, or before cleaning a messy CSV.
---

# CSV cleaning plan

Produce a written plan for cleaning a CSV. Do not clean it. The original file must stay byte-for-byte unchanged.

## Rules

- Read-only on the source CSV. Never open it for writing, never run in-place tools (`sed -i`, `to_csv` to the same path, etc.).
- Write the plan to a new file next to the CSV, named `<csv-name>.cleaning-plan.md`, unless the user names another path. Never overwrite an existing file without saying so.
- Any inspection script must be read-only, and its output goes to the plan or the terminal only.
- Every issue in the plan needs evidence (counts, column name, 2-5 example values with row numbers) and an exact fix that someone could run without further decisions. If a fix needs a judgment call, give a recommended default and list the alternatives.
- Do not apply the fixes. End by asking whether to execute the plan.

## Steps

1. **Locate the file.** Use the path the user gave. If it is missing or ambiguous, look for `*.csv` in the working directory and pick the only candidate; if there are several, list them in the plan and proceed with the most recently modified, stating that choice.
2. **Record file facts.** Size, row count, encoding (check for a BOM and for non-UTF-8 bytes), delimiter, quote character, line endings, header present or not, ragged rows (rows whose field count differs from the header). Use Python (`csv`, plus `pandas` if available, reading with `dtype=str` and `keep_default_na=False` so nothing is silently coerced) or a shell equivalent.
3. **Profile each column.** For every column: inferred type, non-empty count, distinct count, min/max (numeric/date), top 5 values with counts, and the type issues below.
4. **Detect issues** in each category in the next section.
5. **Write the plan** using the template below.
6. **Verify the original is untouched** (compare size and modified time, or a hash taken before and after) and say so in the plan.

## Issue checks and fixes

### Column types
- Infer from the values: integer, decimal, boolean, date/datetime, categorical, free text, identifier.
- Flag mixed types (e.g. `12`, `n/a`, `1,200`), numbers stored with currency symbols, thousands separators or percent signs, and identifiers with leading zeros (zip codes, SKUs) that must stay text.
- Fix: state target type per column and the parse rule, e.g. "strip `$` and `,`, cast to decimal(12,2)"; "keep as string, zero-pad to 5".

### Missing values
- Count true blanks plus placeholder tokens: `NA`, `N/A`, `null`, `none`, `-`, `?`, `unknown`, whitespace-only, `0` or `1900-01-01` where clearly a sentinel.
- Report per column count and percent, and whether missingness looks related to other columns.
- Fix per column, one of: normalize to empty, drop rows (only if the column is essential and few rows are affected), fill with a stated constant/median/mode, or leave and flag. Give the recommended choice and why.

### Duplicates
- Exact duplicate rows (all columns), duplicates on the likely key column(s), and near-duplicates after trimming and case-folding.
- Report group counts and example row numbers.
- Fix: the dedupe key, which row to keep (first, last, most complete), and what to do with conflicting values in the dropped rows.

### Inconsistent casing and whitespace
- For categorical and text columns, find values that collide after `strip().casefold()` (e.g. `NY`, `ny`, `New York `), plus leading/trailing/double spaces.
- Fix: the exact normalization (trim, collapse whitespace, lower/upper/title case) and an explicit mapping table for each variant set, e.g. `ny, NY, New York -> NY`.

### Date formats
- Detect each format in use per date column (`YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, `Mon D, YYYY`, two-digit years, with or without time or timezone), with counts.
- Resolve ambiguity (`03/04/2024`) by looking for unambiguous values in the same column (a day > 12); if still ambiguous, say so and state the assumption.
- Flag impossible dates and out-of-range outliers.
- Fix: target format (default ISO 8601 `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SSZ` with time), the parse order per format, and what to do with unparseable values (set empty and list them).

### Other issues worth noting briefly
Outliers, negative values where impossible, header problems (duplicate or blank names, inconsistent naming style), embedded newlines, mojibake, and columns that are entirely empty or constant.

## Plan template

```markdown
# Cleaning plan: <file>

Generated <date>. Source file not modified (<size>, <hash or mtime>).

## Summary
<rows> rows x <cols> columns. <N> issues: <short list by severity>.

## File format
Encoding, delimiter, quoting, line endings, header, ragged rows, with fix if any.

## Column overview
| Column | Inferred type | Target type | Non-empty | Distinct | Issues |
|---|---|---|---|---|---|

## Issues and fixes
### 1. <short title> (<column>, severity high/med/low)
- Evidence: <counts, examples with row numbers>
- Fix: <exact rule or code>
- Decision needed: <only if any, with recommended default>

## Suggested order of operations
1. Fix encoding/delimiter/ragged rows
2. Trim whitespace and normalize placeholders to empty
3. Normalize casing and map variants
4. Parse dates and cast types
5. Handle missing values
6. Deduplicate (last, so earlier normalization exposes duplicates)

## Reproducible script
A pandas (or shell) script that applies every fix and writes to a NEW file `<name>.cleaned.csv`. Not run.
```

## Finish

Report to the user: the plan's path, the issue count, and any decisions they need to make. Confirm the original file is unchanged. Do not run the cleaning script unless the user asks.
