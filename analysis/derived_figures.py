#!/usr/bin/env python3
"""Figures that the documents cite and that no findings file holds: agreement of the external labels with the hand-labelled sample, and the
effect of counting characters with CRLF line endings on the invocation slope.

Usage: python analysis/derived_figures.py        (reads analysis/labels_sample_manual.tsv, skill_labels.json, skill_features.json and the
                                                   invocation findings of the invocation run) -> analysis/derived_figures.json
Slope: least squares of invocation tokens on body characters over the 20 measured skills, with characters as stored (CRLF counts two) and as
LF-normalised (`body_chars` of skill_features.json). The split skill's core (13,117 characters, 15 reference files) is what
`bench/skilltx.py split_sections(text, 12000)` returns for `design-taste-frontend` at the commit in workload/manifest.json; it needs the cloned
skill file and is recorded here as a constant."""
import json, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "analysis"
labels = {x["name"]: x for x in json.loads((A / "skill_labels.json").read_text(encoding="utf-8"))}
manual = []
for line in (A / "labels_sample_manual.tsv").read_text(encoding="utf-8").splitlines():
    if line.startswith("#") or not line.strip():
        continue
    n, d, f, c = [x.strip() for x in line.split("|")]
    manual.append((n, d, f, int(c)))
agree = {"sample": len(manual),
         "domain": sum(1 for n, d, f, c in manual if labels[n]["domain"] == d),
         "form": sum(1 for n, d, f, c in manual if labels[n]["form"] == f),
         "clarity_exact": sum(1 for n, d, f, c in manual if labels[n]["clarity"] == c),
         "clarity_within_1": sum(1 for n, d, f, c in manual if abs(labels[n]["clarity"] - c) <= 1)}
agree.update({k + "_pct": round(100 * agree[k] / agree["sample"], 1) for k in ("domain", "form", "clarity_exact", "clarity_within_1")})

feat = {x["name"]: x for x in json.loads((A / "skill_features.json").read_text(encoding="utf-8"))}
run = sorted((ROOT / "results").glob("*_invocation"))[0]
inv = json.loads((run / "invocation_findings.json").read_text(encoding="utf-8"))["skills"]


def slope(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


stored = [(r["body_chars"], r["invocation_tokens"]) for r in inv]
lf = [(feat[r["skill"]]["body_chars"], r["invocation_tokens"]) for r in inv]
out = {"label_agreement": agree,
       "invocation_slope_tokens_per_char": {"skills": len(inv), "stored_counts_crlf": round(slope(*zip(*stored)), 4), "lf_counts": round(slope(*zip(*lf)), 4),
                                            "lf_over_stored_pct": round(100 * (slope(*zip(*lf)) / slope(*zip(*stored)) - 1), 2)},
       "median_tokens_per_body_char": {"stored": round(st.median(t / c for c, t in stored if c), 4), "lf": round(st.median(t / c for c, t in lf if c), 4)},
       "split_skill": {"core_chars": 13117, "reference_files": 15, "target_core_chars": 12000}}
body = [x["body_chars"] for x in feat.values()]
deferred = [x["deferred_share"] for x in feat.values() if x["deferred_bytes"] > 0]
out["descriptive"] = {"skills": len(body), "median_body_chars": st.median(body), "skills_with_deferred_material": len(deferred), "median_deferred_share_of_those": round(st.median(deferred), 3)}
(A / "derived_figures.json").write_text(json.dumps(out, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
print(json.dumps(out, indent=1))
