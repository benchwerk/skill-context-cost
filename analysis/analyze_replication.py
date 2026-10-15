#!/usr/bin/env python3
"""Part 13: replication on Claude Code 2.1.286 against the results on 2.1.284 (statements V1 to V4 of prediction.md, written before the replication).

Usage: python analysis/analyze_replication.py [--alias <replication alias run>]
Compares, from the run folders named below: V1 added tokens per configuration (window total of the first request minus the empty session of the same model, same
configuration in the old and the new run, tolerance 3%); V2 the trigger recall and false triggers; V3 the probe verdicts; V4 the alias hit rates (needs the
replication alias run, 10 runs per wording). Writes results/replication_findings.json."""
import collections, json, statistics as st, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent / "results"
OLD = {"skills": "2026-10-02_x86-laptop_skills", "invocation": "2026-10-02_x86-laptop_invocation", "mechanisms": "2026-10-02_x86-laptop_mechanisms", "restructure": "2026-10-02_x86-laptop_restructure"}
NEW_SKILLS = "2026-10-07_x86-laptop_replication_skills"
NEW_TRIGGER, OLD_TRIGGER = "2026-10-07_x86-laptop_replication_trigger", "2026-10-02_x86-laptop_trigger"
NEW_CLAIMS, OLD_CLAIMS = "2026-10-08_x86-laptop_replication_claims", "2026-10-03_x86-laptop_claims"


def tot(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def rows(folder):
    return [json.loads(l) for l in (R / folder / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def window_totals(folders):
    """(model, config) -> median window total of the first request"""
    by = collections.defaultdict(list)
    for f in folders:
        for r in rows(f):
            u = r.get("first_request_usage") or r.get("usage")
            if u and r.get("config"):
                by[(r["model"], r["config"])].append(tot(u))
    return {k: st.median(v) for k, v in by.items()}


def main(alias_run):
    old = window_totals(OLD.values())
    new = window_totals([NEW_SKILLS])
    out = {"claude_code": {"old": "2.1.284", "new": "2.1.286"}}
    # V1
    models = sorted({m for m, _ in new})
    v1 = {}
    for m in models:
        c0o, c0n = old.get((m, "C0")), new.get((m, "C0"))
        rows_ = []
        for (mm, c), n in sorted(new.items()):
            if mm != m or c == "C0" or (m, c) not in old or c.startswith(("G", "X1")):
                continue
            ao, an = old[(m, c)] - c0o, n - c0n
            rows_.append({"config": c, "added_old": ao, "added_new": an, "relative_change_pct": None if ao == 0 else round(100 * (an - ao) / ao, 2), "within_3pct": (an == ao) if ao == 0 else abs(an - ao) <= 0.03 * abs(ao)})
        v1[m] = {"empty_session_old": c0o, "empty_session_new": c0n, "empty_session_change": None if c0o is None else c0n - c0o, "configs_compared": len(rows_),
                 "configs_within_3pct": sum(1 for x in rows_ if x["within_3pct"]), "outside": [x for x in rows_ if not x["within_3pct"]]}
    out["V1_added_tokens"] = v1
    # V2
    o = json.loads((R / OLD_TRIGGER / "trigger_findings.json").read_text(encoding="utf-8"))
    n = json.loads((R / NEW_TRIGGER / "trigger_findings.json").read_text(encoding="utf-8"))
    def rate(d, cell, k="positive_all"):
        x = d["cells"][cell][k]
        return x["hits"], x["n"], x["rate"], x["ci"]
    v2 = {"original_alone": {"old": rate(o, "original/alone"), "new": rate(n, "original/alone")}, "original_crowded": {"old": rate(o, "original/crowded"), "new": rate(n, "original/crowded")},
          "false_triggers_old": o["false_triggers"]["total"], "false_triggers_new": n["false_triggers"]["total"], "calls_new": n["calls"], "mixed_cells_new": n["determinism"]["cells_with_mixed_outcomes"],
          "mixed_cells_old": o["determinism"]["cells_with_mixed_outcomes"]}
    v2["alone_within_10pp"] = abs(v2["original_alone"]["new"][2] - v2["original_alone"]["old"][2]) <= 0.10
    v2["crowded_within_10pp"] = abs(v2["original_crowded"]["new"][2] - v2["original_crowded"]["old"][2]) <= 0.10
    v2["no_false_triggers"] = n["false_triggers"]["total"] == 0
    out["V2_trigger"] = v2
    # V3
    po = {x["probe"]: x for x in json.loads((R / OLD_CLAIMS / "findings.json").read_text(encoding="utf-8"))}
    pn = {x["probe"]: x for x in json.loads((R / NEW_CLAIMS / "findings.json").read_text(encoding="utf-8"))}
    v3 = [{"probe": k, "old": po[k]["verdict"], "new": pn[k]["verdict"], "same": po[k]["verdict"] == pn[k]["verdict"], "new_observed": pn[k]["observed"]} for k in sorted(po) if k in pn]
    out["V3_probes"] = {"compared": len(v3), "same": sum(1 for x in v3 if x["same"]), "differences": [x for x in v3 if not x["same"]], "missing_in_new": sorted(set(po) - set(pn))}
    # V4
    if alias_run:
        rr = rows(alias_run)
        hit = collections.defaultdict(lambda: [0, 0])
        for r in rr:
            h = 1 if any(t["tool"] == "Skill" and "grilling" in t["input"] for t in r.get("tool_calls", [])) else 0
            hit[r["config"]][0] += h
            hit[r["config"]][1] += 1
        out["V4_alias"] = {c: {"hits": a, "n": b} for c, (a, b) in sorted(hit.items())}
        out["V4_alias_all_10_of_10"] = all(a == b == 10 for a, b in hit.values()) and len(hit) == 6
    # bundled skills reported by Claude Code at start-up: a 17th one (plugin-authoring) appears on 2.1.286
    bund = {}
    for f in [OLD["skills"], NEW_SKILLS] + sorted(p.name for p in R.glob("*_v1check_*")) + ([alias_run] if alias_run else []):
        rr = [r for r in rows(f) if r.get("init_skills") is not None]
        bund[f] = {"rows": len(rr), "with_plugin_authoring": sum(1 for r in rr if "plugin-authoring" in r["init_skills"]), "bundled_skills_in_C0_rows": sorted({len(r["init_skills"]) for r in rr if r["config"] == "C0"})}
    out["bundled_skill_plugin_authoring"] = bund
    if alias_run:
        def stats(folders, configs):
            rr = [r for f in folders for r in rows(f) if r["config"] in configs]
            return {"runs": len(rr), "result_subtypes": dict(collections.Counter(r.get("result_subtype") for r in rr)), "turns": dict(collections.Counter(r.get("num_turns") for r in rr)),
                    "max_tool_calls_in_a_run": max(len(r.get("tool_calls", [])) for r in rr), "tool_calls_in_runs_that_ended_in_error_max_turns": [[t["tool"] for t in r.get("tool_calls", [])] for r in rr if r.get("result_subtype") == "error_max_turns"]}
        flows = {"G-original", "G-slash", "G-prose", "G2-original", "G2-slash", "G2-prose"}
        out["alias_turns"] = {"2.1.284": stats(["2026-10-02_x86-laptop_alias", "2026-10-03_x86-laptop_alias_crowded"], flows), "2.1.286": stats([alias_run], flows)}
    (R / "replication_findings.json").write_text(json.dumps(out, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--alias") + 1] if "--alias" in sys.argv else None
    main(a)
