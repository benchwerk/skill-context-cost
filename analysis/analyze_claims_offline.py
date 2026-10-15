#!/usr/bin/env python3
"""Ledger claims that need no model call, checked against data already held.

Usage: python analysis/analyze_claims_offline.py        (reads skill_features.json, the popularity snapshot, the local clones)
  C-053 / C-073 / K-032  SKILL.md under 500 lines          -> share of the 138 skills over 500 lines
  C-071 / C-092          body under 5,000 tokens           -> share over 5,000 tokens (0.37 tokens per character, labelled estimate)
  C-069 / C-004          description 1,024 / 1,536 chars   -> share of listing texts over each
  C-100 / K-034          concise beats comprehensive       -> no data here (quality test)
  K-052 / K-053 / C-121  install counts gameable           -> identical weekly series, zero-to-spike jumps, concentration in the snapshot
  K-046 / K-048          share of skills with security flags -> static heuristics only (flags are not vulnerabilities)
Writes offline_claims_findings.json."""
import collections, json, re, statistics as st
from pathlib import Path

A = Path(__file__).resolve().parent
ROOT = A.parent
feats = json.loads((A / "skill_features.json").read_text(encoding="utf-8"))
snap = json.loads((ROOT / "workload" / "popularity_snapshot.json").read_text(encoding="utf-8"))["rows"]
man = json.loads((ROOT / "workload" / "manifest.json").read_text(encoding="utf-8"))
out = {}
n = len(feats)
out["C-053_over_500_lines"] = {"n": n, "over": sum(1 for f in feats if f["body_lines"] > 500), "share": round(sum(1 for f in feats if f["body_lines"] > 500) / n, 3),
                               "median_lines": st.median(f["body_lines"] for f in feats), "max_lines": max(f["body_lines"] for f in feats)}
over5k = [f for f in feats if 0.37 * f["body_chars"] + 50 > 5000]
out["C-071_over_5000_tokens_estimate"] = {"over": len(over5k), "share": round(len(over5k) / n, 3), "median_tokens_estimate": round(st.median(0.37 * f["body_chars"] + 50 for f in feats))}
out["C-069_C-004_description_length"] = {"over_1024": sum(1 for f in feats if f["listing_chars"] > 1024), "over_1536_raw": sum(1 for f in feats if f["description_chars"] + f["when_to_use_chars"] > 1536),
                                         "max_listing_chars": max(f["listing_chars"] for f in feats), "median": st.median(f["listing_chars"] for f in feats)}
out["structure"] = {"multi_file_share": round(sum(1 for f in feats if f["folder_files"] > 0) / n, 3), "points_to_files_share": round(sum(1 for f in feats if f["referenced_files_in_body"] > 0) / n, 3)}

# install-count integrity (K-052, K-053)
series = collections.defaultdict(list)
for r in snap:
    series[tuple(r["weekly"])].append(r)
identical = [v for v in series.values() if len(v) >= 2 and sum(v[0]["weekly"]) > 0]
near = []
by_src = collections.defaultdict(list)
for r in snap:
    by_src[r["source"]].append(r)
for src, rs in by_src.items():
    if len(rs) >= 3:
        last = [x["weekly"][-1] for x in rs]
        if last and max(last) > 0 and (max(last) - min(last)) / max(last) < 0.02 and max(last) > 5000:
            near.append((src, len(rs), min(last), max(last)))
spike = [r for r in snap if sum(r["weekly"][:5]) == 0 and r["weekly"][-1] >= 10000]
inst = sorted((r["installs"] for r in snap), reverse=True)
tot = sum(inst)
out["K-052_K-053_snapshot"] = {"rows": len(snap), "groups_with_identical_8_week_series": len(identical), "rows_in_such_groups": sum(len(g) for g in identical),
                               "largest_identical_group": max((len(g) for g in identical), default=0),
                               "sources_whose_skills_share_the_same_last_week_within_2pct": len(near),
                               "rows_with_zero_first_5_weeks_then_over_10k_last_week": len(spike),
                               "top10_share_of_installs_in_snapshot": round(sum(inst[:10]) / tot, 3), "top100_share": round(sum(inst[:100]) / tot, 3)}

# static security heuristics over the local clones (flags, not vulnerabilities)
PAT = {
    "network_call": re.compile(r"\b(curl|wget|Invoke-WebRequest|requests\.(get|post)|urllib|fetch\(|axios|http\.client|XMLHttpRequest)\b", re.I),
    "obfuscation_or_eval": re.compile(r"\b(base64\s+(-d|--decode)|atob\(|eval\(|exec\(|Function\(|powershell\s+-enc|\\x[0-9a-f]{2}\\x[0-9a-f]{2})", re.I),
    "pipe_to_shell": re.compile(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b", re.I),
    "credential_paths": re.compile(r"(~/\.ssh|\.aws/credentials|\.env\b|id_rsa|\.npmrc|keychain|API_KEY|SECRET_KEY)", re.I),
    "destructive": re.compile(r"(rm\s+-rf\s+(/|~|\$HOME)|git\s+push\s+--force|DROP\s+TABLE|mkfs\.|format\s+c:)", re.I),
    "prompt_override": re.compile(r"(ignore (all |any )?(previous|prior|above) instructions|do not (tell|inform|mention to) the user|without (telling|informing) the user|disregard (the )?system)", re.I),
    "hidden_unicode": re.compile("[​‌‍⁠‪-‮⁦-⁩﻿]"),
}
flags = collections.defaultdict(list)
checked = 0
unique_entries, seen_entries = [], set()   # the 12 skills that are in both the popular list and the random sample are counted once
for e in man["real_order"] + man["random_set"]:
    if (e["source"], e["path"]) not in seen_entries:
        seen_entries.add((e["source"], e["path"]))
        unique_entries.append(e)
for e in unique_entries:
    base = ROOT / "workload" / "src" / e["source"].replace("/", "__")
    folder = (base / e["path"]).parent
    files = [base / e["path"]] if folder == base else [p for p in folder.rglob("*") if p.is_file() and p.stat().st_size < 400_000 and ".git" not in p.relative_to(folder).parts]
    texts = []
    for p in files:
        try:
            texts.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    blob = "\n".join(texts)
    checked += 1
    for k, rx in PAT.items():
        if rx.search(blob):
            flags[k].append(e["name"])
uniq = {n for v in flags.values() for n in v}
out["K-046_K-048_static_flags"] = {"skills_checked": checked, "skills_with_any_flag": len(uniq), "share": round(len(uniq) / checked, 3),
                                   "by_category": {k: len(v) for k, v in flags.items()}, "note": "heuristics only: a flag means a pattern appears somewhere in the skill folder (documentation and examples included), not that it is malicious"}
(A / "offline_claims_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
for k, v in out.items():
    print(k, json.dumps(v)[:330])
