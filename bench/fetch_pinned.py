#!/usr/bin/env python3
"""Fetch the skill repositories at the commits recorded in workload/fetched.json and check every skill file against workload/manifest.json.

Usage: python bench/fetch_pinned.py [--check]
For every repository in workload/fetched.json: fetch exactly the recorded commit into workload/src/<owner>__<repo>/ (a shallow fetch of that
commit, nothing else) unless the folder exists. Then, for every skill in the manifest (the popular list, the random sample and the extra
skills), compute the sha256 of its SKILL.md and compare it with the manifest. Prints the number of matches and every mismatch; exits 1 on a
mismatch or a missing repository. `--check` only verifies what is already on disk. Needs git and network access. Unlike fetch_skills.py this does
not need the withheld selection file: the published manifest is enough to repeat the measurements."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workload" / "src"


def git(*a, cwd=None):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()


def main():
    rec = json.loads((ROOT / "workload" / "fetched.json").read_text(encoding="utf-8"))
    man = json.loads((ROOT / "workload" / "manifest.json").read_text(encoding="utf-8"))
    check = "--check" in sys.argv
    bad = 0
    SRC.mkdir(parents=True, exist_ok=True)
    for source, r in sorted(rec.items()):
        if "commit" not in r:
            continue
        d = SRC / source.replace("/", "__")
        if not d.exists():
            if check:
                print("missing", source)
                bad += 1
                continue
            try:
                d.mkdir()
                git("init", "--quiet", cwd=d)
                git("fetch", "--quiet", "--depth", "1", f"https://github.com/{source}", r["commit"], cwd=d)
                git("checkout", "--quiet", "FETCH_HEAD", cwd=d)
            except subprocess.CalledProcessError as e:
                print("FAILED", source, (e.stderr or "")[-120:])
                bad += 1
                continue
        head = git("rev-parse", "HEAD", cwd=d)
        if head != r["commit"]:
            print("WRONG COMMIT", source, head, "!=", r["commit"])
            bad += 1
    skills = man["real_order"] + man.get("random_set", []) + man.get("extra_skills", [])
    ok = 0
    for s in skills:
        f = SRC / s["source"].replace("/", "__") / s["path"]
        if not f.exists():
            print("missing file", s["source"], s["path"])
            bad += 1
        elif hashlib.sha256(f.read_bytes()).hexdigest() != s["sha256"]:
            print("HASH MISMATCH", s["source"], s["path"])
            bad += 1
        else:
            ok += 1
    print(f"{ok} of {len(skills)} skill files match the manifest; {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
