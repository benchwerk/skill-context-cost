---
name: bash-script-safety-review
description: Review a Bash/shell script for safety hazards and give the corrected line for each risk. Checks for missing `set -euo pipefail`, unquoted variables, `rm -rf` on variables that may be empty, unchecked `cd`, and reliance on the current working directory. Use this skill whenever the user asks to review, audit, lint, harden, or sanity-check a .sh/bash script, deploy/backup/cleanup/install script, or pastes shell code and asks "is this safe?", even if they don't say "safety review".
---

# Bash Script Safety Review

Shell scripts fail silently and destructively: an unset variable inside `rm -rf "$DIR/"` can wipe `/`, and a failed `cd` makes later commands run in the wrong place. The goal of this review is to find those hazards and hand back concrete fixes the user can paste in, not just warnings.

## Process

1. Read the whole script (ask for the path only if none was given; otherwise use the file or pasted code). Note the shebang, since `set -o pipefail` and some fixes are Bash-specific; if it is `#!/bin/sh`, say so and use POSIX-compatible fixes (no `[[ ]]`, no arrays, `pipefail` is not guaranteed).
2. Check each category below, scanning every line, including functions, loops, and heredocs.
3. Report findings using the output format below. Do not rewrite the whole script unless asked; give line-level fixes.
4. If a category is clean, say so in one line so the user knows it was checked.

## What to check

### 1. Strict mode
Look for `set -euo pipefail` near the top (after the shebang). Missing or partial (`set -e` only) is a finding.
- `-e` stops on failed commands, `-u` turns unset variables into errors, `pipefail` makes `a | b` fail if `a` fails.
- Fix: add `set -euo pipefail` as the first line after the shebang. Optionally add `IFS=$'\n\t'`.
- Warn about the side effects of adding it: commands that legitimately return non-zero (`grep` with no match, `diff`) now abort the script and need `|| true` or an `if`; `$1`-style optional args need `${1:-}`.
- `set -e` is silently disabled inside `if`/`||`/`&&` contexts and in command substitutions used as arguments; mention this when the script relies on it.

### 2. Unquoted variables
Any `$var`, `$(cmd)`, or `${var}` outside double quotes undergoes word splitting and globbing, so a path with a space or `*` breaks or matches the wrong files.
- Fix: `"$var"`, `"$(cmd)"`, `"${arr[@]}"`.
- Also flag unquoted `$@`/`$*` (use `"$@"`), and unquoted variables in `[ ]` tests (`[ -f $f ]` → `[ -f "$f" ]`).
- Not a finding: assignments (`x=$y`), the inside of `[[ ]]` on the left of `==`, and intentional splitting (but suggest an array in that case).

### 3. `rm -rf` on variables that may be empty
`rm -rf "$DIR/"` with empty `DIR` becomes `rm -rf /`. Also flag `rm -rf $DIR/*`, and variables built from other variables or command output that can be empty.
- Fix, preferred: `rm -rf -- "${DIR:?DIR is not set}"` (aborts if unset or empty). Use `--` so names beginning with `-` are not read as options.
- For subpaths: `rm -rf -- "${BUILD_DIR:?}/cache"`.
- For extra safety, suggest validating that the target is the expected directory (e.g. `[[ $DIR == /tmp/myapp.* ]]`) or using `mktemp -d` with a `trap 'rm -rf -- "$tmp"' EXIT`.
- Note that `set -u` alone does not catch a variable set to the empty string; `:?` does.

### 4. Unchecked `cd`
A failed `cd` leaves the script in the old directory, and the following `rm`, `git`, or `make` runs there.
- Fix: `cd "$dir" || exit 1` (or `|| { echo "cannot cd to $dir" >&2; exit 1; }`). Under `set -e` a bare `cd` aborts, but still flag it when strict mode is absent or when the `cd` is in a `||`/`&&` chain, subshell, or `if` where `-e` does not apply.
- For temporary moves use a subshell: `( cd "$dir" && make )`, which also avoids having to `cd -` back.

### 5. Reliance on the current directory
Relative paths (`./config`, `data/in.txt`, `source lib.sh`) and `$PWD` assumptions break when the script is run from another directory or via cron/systemd.
- Fix: resolve the script's own directory once and build paths from it:
  ```bash
  SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  source "$SCRIPT_DIR/lib.sh"
  ```
  or `cd "$SCRIPT_DIR"` explicitly at the top if the script is meant to run from its own folder.
- Flag `$(pwd)`/`$PWD` used as a base for destructive operations, and relative `rm`, `mv`, or `find .` targets.

### Also mention briefly (if seen)
Only if clearly present, add short notes for: `eval` or unquoted input used in commands, `cat file | while read` losing variables in a subshell, `ls` output parsing, missing `--` before user-controlled filenames, backticks instead of `$(...)`, and `read` without `-r`. Keep these in a short "Other observations" list so the five requested categories stay the focus.

## Output format

Use this structure:

```
## Summary
<one or two sentences: overall risk level (High/Medium/Low) and count of findings>

## Findings

### 1. <Short title> — <High|Medium|Low>
Line <N>: `<original line>`
Risk: <one sentence on what can go wrong, with a concrete failure case>
Fix: `<corrected line>`

### 2. ...

## Checked, no issues
- <categories with no findings>

## Other observations
- <optional>
```

Guidelines:
- Cite the line number and quote the original line so the user can find it.
- The "Fix" must be an actual corrected line (or short block) that preserves the script's intent, not advice like "quote your variables".
- Rank by severity: anything that can delete data (`rm -rf` with empty variables, unchecked `cd` before `rm`) is High; missing strict mode and unquoted variables that guard destructive commands are Medium or High; style-level quoting is Low.
- When many lines share the same issue (e.g. 12 unquoted variables), list the most dangerous ones individually and group the rest into one finding with line numbers.
- Offer the fully patched script at the end only as an offer, unless the user asked for it.

## Example

Input:
```bash
#!/bin/bash
cd $BUILD_DIR
rm -rf $BUILD_DIR/*
cp config.yml $DEST
```

Output (abridged):

### 1. Missing strict mode — Medium
Line 1: `#!/bin/bash`
Risk: Failed commands and unset variables are ignored, so the script keeps running after errors.
Fix: add `set -euo pipefail` on line 2.

### 2. Unchecked `cd` with unquoted variable — High
Line 2: `cd $BUILD_DIR`
Risk: If `BUILD_DIR` is empty, `cd` goes to `$HOME`; if the directory is missing, the next `rm` runs in the wrong place.
Fix: `cd -- "${BUILD_DIR:?BUILD_DIR is not set}" || exit 1`

### 3. `rm -rf` on possibly empty variable — High
Line 3: `rm -rf $BUILD_DIR/*`
Risk: With `BUILD_DIR` empty this expands to `rm -rf /*`.
Fix: `rm -rf -- "${BUILD_DIR:?BUILD_DIR is not set}"/*`

### 4. Relies on current directory — Medium
Line 4: `cp config.yml $DEST`
Risk: `config.yml` is resolved against wherever the script was launched, and `$DEST` is unquoted.
Fix: `cp -- "$SCRIPT_DIR/config.yml" "${DEST:?}"` with `SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"` defined near the top.
