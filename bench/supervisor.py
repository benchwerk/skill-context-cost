#!/usr/bin/env python3
"""Run a long measurement across several subscription windows without anyone restarting it.

Usage: python bench/supervisor.py <name> -- <command> [args...]
  e.g. python bench/supervisor.py trigger -- python bench/trigger_test.py --runs 3
The command is run; when it stops with exit code 3 (its own guard: the five-hour meter reached the limit, or --max-calls),
the supervisor reads the reset time and the results folder from the command's last STOP line, sleeps until two minutes after
the reset, and runs the same command again with --resume <folder>. It ends when the command exits 0 (finished) or with
another code (error), or after 12 attempts. The log is written to build/supervisor_<name>.log (not published).
The environment (CLAUDE_CONFIG_DIR, CLAUDE_BIN) is inherited from whoever starts it."""
import datetime, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    if "--" not in sys.argv or len(sys.argv) < 4:
        sys.exit(__doc__)
    name = sys.argv[1]
    cmd = sys.argv[sys.argv.index("--") + 1:]
    (ROOT / "build").mkdir(exist_ok=True)
    log = open(ROOT / "build" / f"supervisor_{name}.log", "a", encoding="utf-8", newline="\n")

    def say(msg):
        line = f"{datetime.datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()
    folder, attempt = None, 0
    while attempt < 12:
        attempt += 1
        c = cmd + (["--resume", folder] if folder else [])
        say(f"attempt {attempt}: {' '.join(c)}")
        p = subprocess.Popen(c, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        last_stop = ""
        for line in p.stdout:
            log.write(line)
            log.flush()
            if line.startswith("STOP"):
                last_stop = line
        rc = p.wait()
        say(f"exit code {rc}")
        if rc == 0:
            say("finished")
            return
        if rc != 3:
            say("stopped by an error; not retrying")
            sys.exit(rc)
        m = re.search(r"--resume (\S+)", last_stop)
        if m:
            folder = m.group(1)
        r = re.search(r"resets (?:at )?(\d{4}-\d\d-\d\dT\d\d:\d\d[+-]\d\d:\d\d)", last_stop)
        if r:
            wake = datetime.datetime.fromisoformat(r.group(1)) + datetime.timedelta(minutes=2)
            secs = max(60, (wake - datetime.datetime.now().astimezone()).total_seconds())
        else:
            secs = 1800
        say(f"sleeping {int(secs)} s (until about {(datetime.datetime.now().astimezone() + datetime.timedelta(seconds=secs)).isoformat(timespec='minutes')})")
        time.sleep(secs)
    say("gave up after 12 attempts")
    sys.exit(2)


if __name__ == "__main__":
    main()
