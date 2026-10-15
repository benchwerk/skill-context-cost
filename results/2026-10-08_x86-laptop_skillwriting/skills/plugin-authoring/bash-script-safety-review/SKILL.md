---
name: bash-script-safety-review
description: Review a Bash script for safety risks: missing set -euo pipefail, unquoted variables, rm -rf on variables that may be empty, unchecked cd, and reliance on the current directory. Use when the user asks to review, audit, harden, or check a shell/Bash script (.sh) for safety or robustness.
---

# Bash Script Safety Review

Review the Bash script the user names (a file path, or code pasted in the conversation). Read the whole script first. Report every risk found, each with its line number, why it is dangerous, and the corrected line. Do not rewrite unrelated code.

## What to check

### 1. Strict mode
- The script should enable `set -euo pipefail` near the top, right after the shebang.
- Flag it if it is missing, or if only part of it is set (e.g. `set -e` alone).
- Fix: `set -euo pipefail`. Optionally suggest `IFS=$'\n\t'` when the script word-splits on purpose.
- Note that `set -e` has gaps (commands in `if` conditions, `&&`/`||` lists, subshells in some contexts). Do not claim it makes the script safe on its own.
- Check the shebang too: `#!/usr/bin/env bash` or `#!/bin/bash`. If it is `#!/bin/sh`, then `pipefail` and other Bash features may not work.

### 2. Unquoted variables
- Flag `$var`, `${var}`, `$(cmd)`, and `$@`/`$*` used outside double quotes in command arguments, `[ ]` tests, `for` lists, and redirections. They are subject to word splitting and globbing.
- Fix: `"$var"`, `"$(cmd)"`, `"$@"`. Inside `[[ ]]` the left side does not split, but quote anyway for consistency.
- Do not flag variables that are intentionally unquoted (e.g. a deliberate array expansion). Suggest `"${arr[@]}"` for those.
- For unset variables, suggest `"${VAR:?VAR is required}"` when the script cannot work without it.

### 3. `rm -rf` on variables that may be empty
- Flag any `rm -rf "$VAR/..."`, `rm -rf $VAR`, `rm -rf "$VAR"/*`, `chmod -R`, `chown -R`, `mv`, or `find ... -delete` whose path depends on a variable that could be unset or empty. `rm -rf "$DIR/"` with an empty `DIR` becomes `rm -rf /`.
- Fix with a guard that aborts when the value is empty:
  - `rm -rf -- "${BUILD_DIR:?}/"`
  - or validate first: `[[ -n "$BUILD_DIR" && "$BUILD_DIR" != "/" ]] || exit 1`
- Also recommend `--` before the path so a value starting with `-` is not read as an option.
- Flag values derived from commands that can fail or print nothing, such as `DIR=$(dirname "$x")` or `VAR=$(grep ...)`.

### 4. Unchecked `cd`
- Flag a bare `cd dir` that has no error handling when the script does not use `set -e`, and flag `cd dir` followed by destructive commands even when it does (`cd dir || true` hides the failure).
- Fix: `cd "$dir" || exit 1` (or `cd "$dir" || { echo "cannot cd to $dir" >&2; exit 1; }`).
- Prefer a subshell when the directory change should be temporary: `( cd "$dir" && make )`.
- Flag `cd "$VAR" && rm -rf *` patterns: if `cd` fails under `||`/`;` chaining, the delete runs in the wrong directory.

### 5. Reliance on the current directory
- Flag relative paths (`./config`, `data/file`, `source lib.sh`) and `$(pwd)`/`$PWD` assumptions, since the script behaves differently depending on where it was launched from.
- Fix: resolve the script's own location once and build paths from it:
  ```bash
  SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  source "$SCRIPT_DIR/lib.sh"
  ```
  Then use `"$SCRIPT_DIR/config"` instead of `./config`.
- Also flag use of `$0` for the script's directory when the script may be sourced (use `BASH_SOURCE[0]`).

### Related risks (report briefly if seen)
- `mktemp` not used for temp files (predictable names like `/tmp/out`); suggest `tmp="$(mktemp)"` plus `trap 'rm -f "$tmp"' EXIT`.
- `eval` or unvalidated user input interpolated into commands.
- Parsing `ls` output; suggest globs or `find -print0` with `read -r -d ''`.
- `read` without `-r`.
- Backticks instead of `$(...)`.

## How to work

1. Read the script in full. If it is long, still read every line; risks hide in helper functions.
2. Go through the five checks above in order and note each occurrence with its line number.
3. If `shellcheck` is available, you may run it as a cross-check, but your report must not depend on it.
4. Do not modify the user's file unless they ask. Report first.

## Output format

Start with one line: the script name and the number of risks found, e.g. `deploy.sh: 6 risks (2 high, 3 medium, 1 low)`.

Then list each risk as:

```
### [HIGH|MEDIUM|LOW] <short title> (line N)
Why: <one sentence on what goes wrong and when>
Current:   <original line>
Corrected: <fixed line>
```

Severity guide:
- HIGH: can delete or overwrite the wrong data (`rm -rf` on a possibly empty variable, destructive command after an unchecked `cd`).
- MEDIUM: breaks on spaces/globs, hides failures, or depends on the launch directory.
- LOW: style or hardening that rarely bites.

Order findings by severity, then by line number. If the same issue appears many times (e.g. 15 unquoted variables), group them under one heading, list the line numbers, and show one representative correction plus the rule for the rest.

End with a "Suggested header" block when strict mode or directory resolution is missing:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
```

If a check finds nothing, say so in one line (e.g. "No unchecked `cd` found") rather than omitting it, so the user knows it was covered.
