#!/usr/bin/env python3
"""The alias pattern: hit rate of the nested skill call and the cost of each way of reaching the same interview loop.

Usage: python analysis/analyze_alias.py results/<alias run> results/<main run>
Added tokens = window total of a request minus the empty session (C0, same model, from the main run). 'first' is the first
request; 'last' is the last request of the run (after any nested skill call). Hit = the model called the Skill tool with
a name containing 'grilling'. Writes alias_findings.json."""
import collections, json, statistics as st, sys
from pathlib import Path


def tot(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [round(c - h, 3), round(c + h, 3)]


def main(run, main_run):
    run = Path(run)
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    mf = json.loads((Path(main_run) / "findings.json").read_text(encoding="utf-8"))
    base = mf["models"][rows[0]["model"]]["C0_window_total"]["median"]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["config"]].append(r)
    out = {}
    for c, rs in sorted(by.items()):
        hit = sum(1 for r in rs if any(t["tool"] == "Skill" and "grilling" in t["input"] for t in r.get("tool_calls", [])))
        first = [tot(r["first_request_usage"]) - base for r in rs]
        last = [tot((r.get("iterations") or [r["usage"]])[-1]) - base for r in rs]
        out[c] = {"runs": len(rs), "nested_skill_calls": hit, "hit_rate": round(hit / len(rs), 3), "hit_rate_95ci": wilson(hit, len(rs)),
                  "first_request_added_median": st.median(first), "last_request_added_median": st.median(last),
                  "last_request_added_min_max": [min(last), max(last)], "turns": dict(collections.Counter(r.get("num_turns") for r in rs)),
                  "result_subtypes": dict(collections.Counter(str(r.get("result_subtype")) for r in rs))}
    if "G-inline" in out and "G-direct" in out:   # the crowded run (G2-*) has no inline or direct configuration
        inline, orig, direct = out["G-inline"]["last_request_added_median"], out["G-original"]["last_request_added_median"], out["G-direct"]["last_request_added_median"]
        out["_summary"] = {"alias_flow_minus_inline_tokens": orig - inline, "direct_minus_inline_tokens": direct - inline}
    (run / "alias_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for c, v in out.items():
        if c != "_summary":
            print(f"{c:11s} runs={v['runs']:2d} hits={v['nested_skill_calls']:2d} ci={v['hit_rate_95ci']} last_added median={v['last_request_added_median']:.0f} range={v['last_request_added_min_max']} turns={v['turns']}")
    print(out.get("_summary"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
