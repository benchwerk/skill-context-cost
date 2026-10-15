---
name: sql-migration-review
description: Review a SQL migration file or diff for deployment risk, including table locks on large tables, missing rollback/down migration, NOT NULL columns without defaults, data-dropping statements, and index creation without CONCURRENTLY. Use when the user asks to review, check, or sanity-check a migration, or shares ALTER/CREATE/DROP statements headed for a database.
---

# SQL Migration Review

Review the migration the user points to (a file, a diff, or pasted SQL). If none is given, look for the newest migration files in the working tree or the current diff.

## Process

1. Read the whole migration, plus its paired down/rollback file if the framework uses one (e.g. `down.sql`, `-- +goose Down`, Alembic `downgrade()`, Rails `down`, Flyway `U__` undo).
2. Identify the database engine (Postgres, MySQL, etc.) from syntax or project config. If unclear, assume PostgreSQL and say so.
3. Check each category below. Where table size matters and is unknown, flag the risk conditionally ("if `orders` is large") rather than asking.

## Checks

**Data loss (Critical)**
- `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `DELETE`/`UPDATE` without `WHERE`
- Column type changes that narrow or convert data, or renames that break running app code
- Dropping constraints/indexes the app relies on

**Locks on large tables (High)**
- Postgres: `ALTER TABLE` forms that rewrite the table or take `ACCESS EXCLUSIVE` (type change, `SET NOT NULL` scan, adding a FK or CHECK without `NOT VALID`, adding a column with a volatile default on PG < 11)
- MySQL: `ALGORITHM=COPY` operations or DDL without `ALGORITHM=INPLACE/INSTANT`
- Large backfills (`UPDATE` over a whole table) in the same transaction as DDL
- Missing `lock_timeout` / `statement_timeout` for DDL on hot tables

**Index creation without CONCURRENTLY (High)**
- Postgres `CREATE INDEX` / `CREATE UNIQUE INDEX` without `CONCURRENTLY` on an existing table (blocks writes). Note that `CONCURRENTLY` cannot run inside a transaction block, so the migration tool may need transactions disabled for that file.
- Same for `DROP INDEX` without `CONCURRENTLY`.
- Not an issue for a table created in the same migration.

**NOT NULL without default (High)**
- `ADD COLUMN ... NOT NULL` with no `DEFAULT`, which fails on any table with rows
- `ALTER COLUMN ... SET NOT NULL` with no prior backfill, or on a large table without the safe pattern (add `CHECK ... NOT VALID`, validate, then set NOT NULL)

**Missing rollback (Medium)**
- No down/undo migration, or a down that is empty, incomplete, or cannot restore dropped data
- Irreversible steps should be called out as such, with the safe alternative (backup, expand/contract)

**Other (Low)** — only if noticed: non-idempotent statements (`IF NOT EXISTS` missing), mixed schema and data changes in one migration, missing index on a new foreign key.

## Output

Keep it short. Start with a one-line overall verdict: **BLOCK**, **FIX BEFORE MERGE**, or **OK**. Then a list ordered by severity (Critical, High, Medium, Low), one line per finding:

```
- [SEVERITY] <file>:<line> — <what is wrong>. Fix: <concrete change>.
```

Rules:
- Quote or reference the specific statement.
- Give the fix in the same line, with a short SQL snippet when it is non-obvious.
- Omit categories with no findings; do not pad with praise or restating the migration.
- If nothing is wrong, say "OK — no risks found" and list what was checked in one line.
