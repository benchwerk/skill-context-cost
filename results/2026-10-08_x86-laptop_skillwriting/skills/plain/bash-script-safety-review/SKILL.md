---
name: bash-script-safety-review
description: Review a Bash script for safety risks — missing set -euo pipefail, unquoted variables, rm -rf on possibly empty variables, unchecked cd, and reliance on the current directory — and list each risk with a corrected line. Use when the user asks to review, audit, harden, or "check the safety of" a shell/bash script.
---

# Bash Script Safety Review

Review the script the user names (or pastes). Read the whole file first, then report risks. Do not modify the file unless asked; the deliverable is the list of risks with corrected lines.

## Checks

1. **Strict mode** — Near the top (after the shebang) there should be `set -euo pipefail`. Flag a missing or partial form (`set -e` alone, `set -u` absent, no `pipefail`). Also check the shebang is `#!/usr/bin/env bash` or `#!/bin/bash` (not `sh`, since `pipefail` is a Bash feature). Mention that `IFS=$'\n\t'` is optional hardening. Note common strict-mode pitfalls the fix introduces, e.g. `grep` returning 1 with no match needs `|| true`, and unset optional vars need `${VAR:-}`.
2. **Unquoted variables** — Flag every `$var`, `${var}`, `$(cmd)`, and `$@`/`$*` used outside double quotes in command arguments, `[ ]` tests, `for` lists, and redirections. Fix: `"$var"`, `"$(cmd)"`, `"$@"`. For lists of items, suggest arrays: `files=(a b); "${files[@]}"`. Prefer `[[ ]]` over `[ ]` in Bash.
3. **`rm -rf` on variables that may be empty** — Flag `rm -rf $VAR/...`, `rm -rf "$VAR/"*`, `rm -rf "$DIR"/` etc. where the variable could be empty or unset (expands to `/` or `/*`). Fix with `${VAR:?message}`: `rm -rf -- "${BUILD_DIR:?BUILD_DIR is not set}"/`. Also suggest `--`, and for high-risk paths a sanity check that the path is not `/`, `$HOME`, or empty.
4. **Unchecked `cd`** — Flag `cd dir` without handling failure (also `pushd`/`popd`), especially when followed by destructive commands. Fix: `cd "$dir" || exit 1` (or `|| { echo "cannot cd to $dir" >&2; exit 1; }`). Note `set -e` does not protect `cd x && ...` chains or `cd` inside conditions.
5. **Reliance on the current directory** — Flag relative paths (`./foo`, `config.ini`, `../lib`) and `source`/file reads that assume the caller's CWD. Fix by anchoring to the script location:
   ```bash
   SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
   source "$SCRIPT_DIR/lib.sh"
   ```
   or `cd "$SCRIPT_DIR" || exit 1` once near the top if the script is meant to run from its own directory.

Also note, briefly and only if seen: `eval` or unvalidated input used in commands, `mktemp` not used for temp files (and no `trap ... EXIT` cleanup), `cat file | while read` subshell variable loss, `read` without `-r`, and `ls` output parsing. Keep these secondary to the five main checks.

## Output format

Start with a one-line verdict (e.g. "7 risks found: 2 high, 3 medium, 2 low"). Then list each risk in script order, using this shape:

```
### <n>. <Short title> — <High|Medium|Low> (line <N>)
Risk: <one sentence on what can go wrong, with a concrete failure case>
Original:  <the line as written>
Corrected: <the fixed line>
```

Severity guide: High = can delete or overwrite unintended data (`rm -rf` with empty variable, `cd` failure before destructive commands); Medium = breaks on spaces/globs or silently continues after errors; Low = robustness or style.

Rules:
- Quote the actual line and line number from the script; give a complete, copy-pasteable corrected line, not a description.
- If the same issue repeats, list the first few distinctly and group the rest ("same fix applies to lines 40, 52, 61").
- For missing strict mode, give the exact line to insert and where.
- If a check finds nothing, say so in one line ("No unchecked `cd` found") rather than omitting it.
- Do not invent risks; only report what is in the script. If the script is not Bash (e.g. `#!/bin/sh` using POSIX only), say that `pipefail` and arrays may be unavailable and give POSIX-compatible fixes.
- End with the full hardened header (shebang, `set -euo pipefail`, `SCRIPT_DIR` line) as a ready-to-paste block if any header fixes were needed.
