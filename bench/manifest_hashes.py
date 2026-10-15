#!/usr/bin/env python3
"""List, per run folder, the hash of the manifest as it was run (recorded in env.json) and the hash of the published manifest.json.

Usage: python bench/manifest_hashes.py
The published manifests had their row-level leaderboard values (rank, installs, weekly counts) removed after the runs by
bench/withhold_leaderboard.py, so the two hashes differ in every run that used a manifest. Writes results/manifest_hashes.json."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = {}
for env in sorted((ROOT / "results").glob("*/env.json")):
    if "smoke" in env.parent.name or env.parent.name.endswith("_dry"):
        continue   # not published
    d = env.parent
    e = json.loads(env.read_text(encoding="utf-8"))
    m = d / "manifest.json"
    row = {"recorded_in_env_json": e.get("manifest_sha256")}
    if m.exists():
        row["published_manifest_sha256"] = hashlib.sha256(m.read_bytes()).hexdigest()
        row["same"] = row["recorded_in_env_json"] == row["published_manifest_sha256"]
    out[d.name] = row
(ROOT / "results" / "manifest_hashes.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(f"{len(out)} run folders -> results/manifest_hashes.json")
