#!/usr/bin/env python3
"""Fetch the GitHub repositories named in workload/selection.json (shallow clone) into workload/src/ and record the
commit of each in workload/fetched.json. Nothing is redistributed: the clones are local and not published.

Usage:  python bench/fetch_skills.py            clone missing repositories, record HEAD commits
        python bench/fetch_skills.py --check    verify the clones still match the recorded commits
Needs git on PATH. Existing clones are never overwritten or updated."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workload" / "src"
REC = ROOT / "workload" / "fetched.json"


def git(*a, cwd=None):
    return subprocess.run(["git", "-c", "core.longpaths=true", *a], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout.strip()


def repo_dir(source):
    return SRC / source.replace("/", "__")


def main():
    sel = json.loads((ROOT / "workload" / "selection.json").read_text(encoding="utf-8"))
    sources = sorted({r["source"] for r in sel["main_candidates"] + sel["random_candidates"]})
    rec = json.loads(REC.read_text(encoding="utf-8")) if REC.exists() else {}
    check = "--check" in sys.argv
    SRC.mkdir(parents=True, exist_ok=True)
    for s in sources:
        d = repo_dir(s)
        if not d.exists():
            if check:
                sys.exit(f"missing clone {d}")
            try:
                git("clone", "--quiet", "--depth", "1", f"https://github.com/{s}", str(d))
            except subprocess.CalledProcessError as e:
                rec[s] = {"error": (e.stderr or "")[-200:]}
                print(f"FAILED {s}")
                continue
        head = git("rev-parse", "HEAD", cwd=d)
        if s in rec and "commit" in rec[s] and rec[s]["commit"] != head:
            sys.exit(f"{s}: HEAD {head} != recorded {rec[s]['commit']}")
        rec[s] = {"commit": head}
        print(f"ok {s} {head[:10]}")
    if not check:
        REC.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
