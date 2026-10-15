#!/usr/bin/env python3
"""Withhold row-level leaderboard data from the files that are published.

Decision of the owner (2026-10-03): the study publishes the selection rule and the hash of the frozen snapshot, not the ranking
itself. This script copies each affected file to build/private_leaderboard/ (not published, first time only), then removes the
keys `installs`, `rank`, `leaderboard_rank` and `weekly` from the published copy. Names, sources, paths, hashes and our own
list position (`popular_rank`) stay. Safe to run more than once.
Usage: python bench/withhold_leaderboard.py"""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "build" / "private_leaderboard"
KEYS = {"installs", "rank", "leaderboard_rank", "weekly", "example_sources", "example_spikes"}
FILES = ["analysis/skill_features.json", "analysis/offline_claims_findings.json", "workload/manifest.json", *[str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "results").glob("*/manifest.json")],
         *[str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "results").glob("*/invocation_findings.json")]]


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in KEYS}
    if isinstance(o, list):
        return [strip(x) for x in o]
    return o


for rel in FILES:
    p = ROOT / rel
    if not p.exists():
        continue
    backup = PRIV / rel
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, backup)
    data = json.loads(backup.read_text(encoding="utf-8"))   # always strip from the private original
    p.write_text(json.dumps(strip(data), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("scrubbed", rel)
