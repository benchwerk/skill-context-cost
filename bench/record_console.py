#!/usr/bin/env python3
"""Record a real command's console output as timestamped evidence (footage for the video).

Usage: python bench/record_console.py <name> -- <command> [args...]
  e.g. python bench/record_console.py full_run -- python bench/run.py
Writes results/footage/<name>.jsonl  one JSON object per output line: {"cmd": 0, "t": seconds since start, "line": text}
plus a final {"cmd": 0, "exit": code, "t": duration}, and results/footage/<name>_env.json (command, date, versions).
Same format as the Shorts demo recordings, so the video's terminal scene can replay it. Nothing is edited afterwards.
Every line is scrubbed of the home directory, user name and temp paths."""
import datetime, json, os, platform, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import scrub   # same scrub as the measurement

ROOT = Path(__file__).resolve().parent.parent


def main():
    if "--" not in sys.argv[2:] and len(sys.argv) < 4 or sys.argv[2] != "--":
        sys.exit(__doc__)
    name, cmd = sys.argv[1], sys.argv[3:]
    out = ROOT / "results" / "footage"
    out.mkdir(parents=True, exist_ok=True)
    if (out / f"{name}.jsonl").exists():
        sys.exit(f"{name}.jsonl exists: footage is never overwritten")
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env={**os.environ, "PYTHONUNBUFFERED": "1"}, text=True, encoding="utf-8", errors="replace", bufsize=1)
    with open(out / f"{name}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for line in p.stdout:
            f.write(json.dumps({"cmd": 0, "t": round(time.time() - t0, 3), "line": scrub(line.rstrip("\r\n"))}) + "\n")
            f.flush()
            print(line, end="")
        p.wait()
        f.write(json.dumps({"cmd": 0, "exit": p.returncode, "t": round(time.time() - t0, 3)}) + "\n")
    env = {"command": scrub(" ".join(cmd)), "date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "os": platform.platform(), "python": platform.python_version(), "exit": p.returncode}
    (out / f"{name}_env.json").write_text(json.dumps(env, indent=1) + "\n", encoding="utf-8", newline="\n")
    sys.exit(p.returncode)


if __name__ == "__main__":
    main()
