#!/usr/bin/env python3
"""Print the output of Claude Code's own `/context` command for one configuration (footage, shots 2, 3 and 6 of footage_plan.md).

Usage: python bench/footage_context.py <config id> [model]
  e.g. python bench/record_console.py ctx_C50 -- python bench/footage_context.py C50
Builds the fixed working directory for the configuration (same builder as the measurement), runs `claude -p /context` in it with the
isolated config dir and prints the reply unchanged. This is the console form of the command, not the interactive screen. It makes
no model call. Needs CLAUDE_BIN and CLAUDE_CONFIG_DIR in the environment (see HANDOFF)."""
import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else run.CFG["models"][0]
    if not os.environ.get("CLAUDE_CONFIG_DIR"):
        sys.exit("CLAUDE_CONFIG_DIR must point at the isolated bench config dir")
    wd = run.build_workdir(cfg_id)
    claude = run.find_claude()
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    print(f"config {cfg_id}, model {model}, {len(run.MAN['sets'][cfg_id])} skills in the project", flush=True)
    cp = subprocess.run([claude, "-p", "/context", "--model", model, *run.CFG["claude_extra_args"]], cwd=wd, env=env,
                        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    print(cp.stdout, end="")
    sys.exit(cp.returncode)


if __name__ == "__main__":
    main()
