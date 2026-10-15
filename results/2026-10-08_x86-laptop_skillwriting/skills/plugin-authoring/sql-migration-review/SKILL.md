---
name: sql-migration-review
description: Review a SQL migration for deployment risk. Use when the user asks to review, check, or sign off on a database migration, schema change, or DDL file. Flags table locks on large tables, missing rollback, NOT NULL columns without defaults, data-dropping statements, and index creation without CONCURRENTLY. Returns a short verdict list ordered by severity.
---

# SQL Migration Review

Review the migration the user points to (a file path, a pasted script, or the migration in the current diff). Read the whole migration, including any down/rollback section or paired down file. Do not run it.

## Checks

Look for each of these, in this order of severity:

1. **Dropping data** (CRITICAL): `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `DELETE`/`UPDATE` without a `WHERE`, column type changes that narrow or convert data, renames that code still reads under the old name. Note whether a backup or an expand/contract split exists.
2. **NOT NULL column without a default** (HIGH): `ADD COLUMN ... NOT NULL` with no `DEFAULT`, or `SET NOT NULL` on an existing column with no backfill. This fails on non-empty tables or forces a full scan under lock. On older engines (Postgres < 11, MySQL without instant DDL) a default also rewrites the table, so say so when the engine is known.
3. **Locks on large tables** (HIGH): `ALTER TABLE` that rewrites or scans the table (type changes, adding a column with a volatile default, `SET NOT NULL`, adding a foreign key or check constraint without `NOT VALID`), `LOCK TABLE`, and big backfills in the same transaction as DDL. Suggest the safe form (`NOT VALID` then `VALIDATE CONSTRAINT`, batched backfill, `lock_timeout`).
4. **Index creation without CONCURRENTLY** (MEDIUM, HIGH if the table is large or hot): `CREATE INDEX` or `CREATE UNIQUE INDEX` without `CONCURRENTLY` (Postgres) blocks writes. Also flag `CONCURRENTLY` used inside a transaction block, which fails. For other engines, note the online equivalent (`ALGORITHM=INPLACE, LOCK=NONE`, `ONLINE`).
5. **Missing rollback** (MEDIUM): no down migration, an empty one, or one that cannot restore dropped data. Say whether the change is reversible.

Also mention briefly anything else that clearly risks an outage (for example mixing schema and data changes in one transaction), but keep the five checks primary.

## Unknowns

Table size and engine are often not in the migration. Do not ask; state the assumption (for example "assuming Postgres, table is large") and say which findings change if it is wrong.

## Output format

Start with one line: `Verdict: BLOCK`, `Verdict: FIX BEFORE MERGE`, or `Verdict: OK`. Use BLOCK for any CRITICAL, FIX BEFORE MERGE for any HIGH or MEDIUM, OK only if nothing was found.

Then a list ordered from most to least severe, one item per finding, each a single line plus an optional one-line fix:

```
Verdict: BLOCK

1. [CRITICAL] line 12 - DROP COLUMN users.legacy_email destroys data with no backup. Fix: stop reading it first, drop in a later release.
2. [HIGH] line 5 - ADD COLUMN status NOT NULL has no DEFAULT. Fix: add nullable, backfill in batches, then SET NOT NULL.
3. [MEDIUM] line 20 - CREATE INDEX without CONCURRENTLY blocks writes on orders. Fix: CREATE INDEX CONCURRENTLY, outside a transaction.
4. [MEDIUM] no down migration. Fix: add one, or document it as irreversible.
```

Rules:
- Keep it short: no preamble, no restating the SQL, no section for checks that passed beyond a closing line like `No issues found for: ...` when useful.
- Cite the line number or statement for each finding.
- Do not edit the migration unless the user asks.
