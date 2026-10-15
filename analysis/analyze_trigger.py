#!/usr/bin/env python3
"""Trigger test results. Usage: python analysis/analyze_trigger.py results/<trigger run>

Hit = the model called the Skill tool for the target skill. Rates are over calls; intervals are 95% Wilson for one proportion and
Newcombe's method for a difference of two proportions (pooled over the four skills, so the unit is a call, not an independent
skill: the intervals are optimistic about generalising to other skills). Writes trigger_findings.json."""
import collections, json, math, statistics as st, sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def newcombe(k1, n1, k2, n2):
    """difference p1 - p2 with a 95% interval"""
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def main(run):
    run = Path(run)
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("decision") not in (None, "none", "timeout")]
    out = {"calls": len(rows), "decisions": dict(collections.Counter(r["decision"].split(":")[0] for r in rows)),
           "other_skill_calls": sum(1 for r in rows if r["other_skill"]), "calls_with_tools_before_decision": sum(1 for r in rows if r["tools_before_decision"])}

    def rate(sel):
        k = sum(1 for r in sel if r["hit"])
        lo, hi = wilson(k, len(sel))
        return {"hits": k, "n": len(sel), "rate": round(k / len(sel), 3) if sel else None, "ci": [round(lo, 3), round(hi, 3)] if lo is not None else None}
    cells = {}
    for variant in ("original", "trim100", "trim40"):
        for setting in ("alone", "crowded"):
            sel = [r for r in rows if r["variant"] == variant and r["setting"] == setting]
            cells[f"{variant}/{setting}"] = {
                "positive_all": rate([r for r in sel if r["polarity"] == "positive"]),
                "positive_keyword": rate([r for r in sel if r["kind"] == "keyword"]),
                "positive_paraphrase": rate([r for r in sel if r["kind"] == "paraphrase"]),
                "negative_hard_false_trigger": rate([r for r in sel if r["kind"] == "hard"]),
                "negative_near_miss_false_trigger": rate([r for r in sel if r["kind"] == "near-miss"])}
    out["cells"] = cells
    out["by_skill_original_alone"] = {s: rate([r for r in rows if r["skill"] == s and r["variant"] == "original" and r["setting"] == "alone" and r["polarity"] == "positive"])
                                      for s in sorted({r["skill"] for r in rows})}
    diffs = {}
    for setting in ("alone", "crowded"):
        base = [r for r in rows if r["variant"] == "original" and r["setting"] == setting and r["polarity"] == "positive"]
        for v in ("trim100", "trim40"):
            for label, pred in (("all", lambda r: True), ("keyword", lambda r: r["kind"] == "keyword"), ("paraphrase", lambda r: r["kind"] == "paraphrase")):
                a = [r for r in rows if r["variant"] == v and r["setting"] == setting and r["polarity"] == "positive" and pred(r)]
                b = [r for r in base if pred(r)]
                d = newcombe(sum(r["hit"] for r in a), len(a), sum(r["hit"] for r in b), len(b))
                diffs[f"{v} minus original / {setting} / {label}"] = [round(x, 3) for x in d]
    for variant in ("original", "trim100", "trim40"):
        a = [r for r in rows if r["variant"] == variant and r["setting"] == "crowded" and r["polarity"] == "positive"]
        b = [r for r in rows if r["variant"] == variant and r["setting"] == "alone" and r["polarity"] == "positive"]
        diffs[f"crowded minus alone / {variant} / all"] = [round(x, 3) for x in newcombe(sum(r["hit"] for r in a), len(a), sum(r["hit"] for r in b), len(b))]
    out["differences_pp_with_95ci"] = diffs
    # determinism: cells with mixed outcomes across the three runs
    grp = collections.defaultdict(list)
    for r in rows:
        grp[(r["skill"], r["variant"], r["setting"], r["prompt_id"])].append(r["hit"])
    mixed = [k for k, v in grp.items() if 0 < sum(v) < len(v)]
    out["determinism"] = {"cells": len(grp), "cells_with_mixed_outcomes": len(mixed), "share": round(len(mixed) / len(grp), 3)}
    fp = [r for r in rows if r["polarity"] == "negative" and r["hit"]]
    out["false_triggers"] = {"total": len(fp), "near_miss": sum(1 for r in fp if r["kind"] == "near-miss"), "examples": [(r["skill"], r["variant"], r["setting"], r["prompt_id"]) for r in fp[:8]]}
    # what the model did when it did not call the skill on a positive prompt
    miss = [r for r in rows if r["polarity"] == "positive" and not r["hit"]]
    out["positive_misses"] = {"n": len(miss), "with_other_tools_first": sum(1 for r in miss if r["tools_before_decision"]),
                              "answered_in_text": sum(1 for r in miss if r["decision"] == "text"), "other_skill": sum(1 for r in miss if r["other_skill"])}
    (run / "trigger_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("calls", "decisions", "other_skill_calls", "calls_with_tools_before_decision", "determinism", "false_triggers", "positive_misses")}, indent=1))
    for c, v in cells.items():
        print(f"{c:18s} pos all {v['positive_all']['rate']:.2f} {v['positive_all']['ci']} kw {v['positive_keyword']['rate']:.2f} para {v['positive_paraphrase']['rate']:.2f} | false: hard {v['negative_hard_false_trigger']['rate']:.2f} near {v['negative_near_miss_false_trigger']['rate']:.2f}")
    print(json.dumps(out["by_skill_original_alone"]))
    for k, v in diffs.items():
        print(f"{k:58s} {v[0]*100:6.1f} pp  [{v[1]*100:6.1f}, {v[2]*100:6.1f}]")


if __name__ == "__main__":
    main(sys.argv[1])
