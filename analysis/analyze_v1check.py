#!/usr/bin/env python3
"""Controlled test of the replication discrepancy (Part 13, V1): the same configurations on Claude Code 2.1.284 and 2.1.286, with and without an explicit
`--permission-mode default`, two runs each (folders `*_v1check_<version>_<default|notset>`).

Usage: python analysis/analyze_v1check.py
For every sweep: the window total of the first request for the empty session C0 and the tokens added by each configuration (its total minus the C0 of the same sweep and
model), with the two runs of each shown so that repeatability is visible. Writes results/v1check_findings.json. Exploratory: this test was not in the prediction."""
import collections, json, statistics as st
from pathlib import Path

R = Path(__file__).resolve().parent.parent / "results"
CONFIGS = ["C0", "C1", "C10", "C50", "C100", "C50-disable", "F1", "I2", "I3", "I10", "L2", "L3", "L10"]


def tot(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


out = {}
for d in sorted(R.glob("*_v1check_*")):
    key = d.name.split("_v1check_")[1]
    by = collections.defaultdict(list)
    for l in (d / "raw.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            u = r.get("first_request_usage") or r.get("usage")
            if u:
                by[(r["model"], r["config"])].append(tot(u))
    sweep = {}
    for model in sorted({m for m, _ in by}):
        c0 = by.get((model, "C0"))
        if not c0:
            continue
        base = st.median(c0)
        row = {"C0_runs": c0, "added": {}}
        for c in CONFIGS[1:]:
            v = by.get((model, c))
            if v:
                row["added"][c] = {"runs": [x - base for x in v]}
        sweep["sonnet" if "sonnet" in model else "haiku"] = row
    out[key] = sweep
(R / "v1check_findings.json").write_text(json.dumps(out, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
for key, sw in out.items():
    print("==", key)
    for m, row in sw.items():
        print(f"  {m:6s} C0 {row['C0_runs']}  added: " + ", ".join(f"{c} {v['runs']}" for c, v in row["added"].items() if c in ("C1", "C10", "C50", "C100", "I2", "I3", "I10")))
