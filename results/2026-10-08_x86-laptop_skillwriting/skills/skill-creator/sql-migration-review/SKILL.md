---
name: sql-migration-review
description: Review a SQL migration file or diff for deployment risk and produce a short severity-ordered verdict list. Checks for locks on large tables, missing rollback/down migration, NOT NULL columns without defaults, destructive data loss (DROP, TRUNCATE, column type changes, unqualified DELETE), and index creation without CONCURRENTLY. Use whenever the user asks to review, check, vet, or sanity-check a migration, ALTER TABLE, schema change, or Rails/Django/Flyway/Alembic/Knex/Prisma migration before merging or deploying, even if they don't say "risk".
---

# SQL Migration Review

Migrations fail in production in a few predictable ways: they hold locks that block traffic, they destroy data that can't be recovered, or they can't be undone. Find those before deploy.

## Process

1. Locate the migration (file path, diff, or pasted SQL). If it's a framework migration (Rails, Django, Alembic, Knex, Prisma, Flyway, etc.), reason about the SQL it generates. Read the paired down/rollback section or file if one exists.
2. Identify the database engine if possible (default to PostgreSQL assumptions and say so; note MySQL differences where they matter). Check for hints on table size; if unknown, treat tables as potentially large and say that was assumed.
3. Check each category below against every statement.
4. Output the verdict list.

## Checks

**Data loss** (usually Critical)
- `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `DELETE`/`UPDATE` without a `WHERE`, column type narrowing, or renames that break running code. Recommend backup, expand/contract (stop reading in code first, drop in a later release), or a rename-then-drop-later step.

**Locks on large tables** (High; Critical on hot, big tables)
- `ALTER TABLE` that rewrites the table or takes `ACCESS EXCLUSIVE` for long: column type change, adding a column with a volatile default (pre-PG11 any default), `ADD CONSTRAINT` (FOREIGN KEY / CHECK) without `NOT VALID` then `VALIDATE CONSTRAINT`, `SET NOT NULL` on existing column (scans table; prefer a validated CHECK first).
- Backfilling `UPDATE` over a whole table in one transaction; recommend batches.
- DDL mixed into one long transaction with other statements; recommend `lock_timeout`.

**Non-null columns without defaults** (High)
- `ADD COLUMN ... NOT NULL` with no `DEFAULT` fails on tables with rows. Suggest add nullable, backfill in batches, then add the constraint, or add a default.

**Index creation without CONCURRENTLY** (High on big tables, Medium otherwise)
- `CREATE INDEX` / `CREATE UNIQUE INDEX` blocks writes. Suggest `CREATE INDEX CONCURRENTLY`, which cannot run inside a transaction block, so the migration must disable its transaction wrapper (e.g. `disable_ddl_transaction!`, `atomic = False`). Flag the case where CONCURRENTLY is used inside a transaction as a bug. Also `DROP INDEX` should be `CONCURRENTLY`.

**Missing rollback** (Medium; High if the change is also destructive)
- No down/revert path, or a down that doesn't truly reverse (e.g. restores a dropped column but not its data). State what the rollback would need to be, or that it is irreversible and requires a backup/forward fix.

Mention any other serious hazard you notice (e.g. enum changes, renames), but don't pad the list.

## Output format

Keep it short. Order by severity: Critical, High, Medium, Low. One line per finding, each with the statement or line, the problem, and the fix.

```
Verdict: BLOCK | FIX BEFORE DEPLOY | OK  (assumptions: PostgreSQL, tables large)

1. [Critical] line 12 `DROP COLUMN users.legacy_email` – irreversible data loss. Fix: stop reading it in code first, drop in a later release after a backup.
2. [High] line 5 `ADD COLUMN plan text NOT NULL` – fails on existing rows. Fix: add nullable, backfill in batches, then SET NOT NULL.
3. [High] line 8 `CREATE INDEX idx_orders_user` – blocks writes. Fix: CREATE INDEX CONCURRENTLY, outside a transaction.
4. [Medium] no down migration – cannot roll back. Fix: add a reversal or document it as forward-only.
```

If nothing is wrong, say `Verdict: OK` and list any assumptions made. Do not rewrite the migration unless asked.
