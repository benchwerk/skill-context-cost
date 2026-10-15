#!/usr/bin/env python3
"""Part 12: the skill invoked by slash command against the same text pasted into the prompt (statements R1 to R5 of prediction.md).

Usage: python analysis/analyze_pasted.py results/<pasted run> results/<Part 9 quality run> [--allow-partial]
The pasted run holds two conditions, `pasted` and `original`, 72 generations. The Part 9 run supplies `none` (R2) and the earlier `original`
score (R5). Score of a page = share of the 16 primary checks passed (0 when the page has no HTML), as in analyze_quality.py; differences are
means over the 12 briefs with a bootstrap over briefs (same function). Tokens come from the `usage` of each result. Writes
quality_pasted_findings.json in the pasted run folder. Refuses a run with fewer than 72 finished generations unless --allow-partial
(only to test the script: partial results are not interpreted)."""
import collections, json, statistics as st, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_quality import boot


FAILED = {}


def rows_of(run):
    rows = [json.loads(l) for l in (Path(run) / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    n_failed = sum(1 for r in rows if not (r.get("output_tokens") or 0) > 0)   # network or login failures: reported, then run again (same seq, later row)
    rows = [r for r in rows if r.get("finished") and (r.get("output_tokens") or 0) > 0]
    FAILED[Path(run).name] = n_failed
    for r in rows:
        ch = r["checks"] or {}
        r["score"] = sum(ch.values()) / len(ch) if r["has_html"] and ch else 0.0
    return rows


def task_means(rows, cond):
    per = collections.defaultdict(list)
    for r in rows:
        if r["cond"] == cond:
            per[r["task"]].append(r["score"])
    return {t: sum(v) / len(v) for t, v in per.items()}


def total_in(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def main(run, main_run, partial):
    rows, base = rows_of(run), rows_of(main_run)
    if len(rows) < 72 and not partial:
        sys.exit(f"{len(rows)} finished generations of 72: run not complete (use --allow-partial only to test the script)")
    tm = {"pasted": task_means(rows, "pasted"), "original": task_means(rows, "original"), "none": task_means(base, "none"), "original_part9": task_means(base, "original")}
    mean = lambda d: sum(d.values()) / len(d) if d else None
    out = {"run": Path(run).name, "generations": len(rows), "failed_attempts_excluded_and_rerun": FAILED.get(Path(run).name, 0), "mean_score_pct": {c: round(100 * mean(d), 2) for c, d in tm.items() if d}}

    def diff(a, b):
        d = boot(tm, a, b)
        return {"diff_pp": round(d["diff"] * 100, 2), "ci_pp": [round(d["ci"][0] * 100, 2), round(d["ci"][1] * 100, 2)], "briefs": d["tasks"]}

    out["pasted_minus_original"] = r1 = diff("pasted", "original")
    out["pasted_minus_none_part9"] = r2 = diff("pasted", "none")
    out["original_minus_none_part9"] = diff("original", "none")
    out["original_this_run_minus_part9"] = diff("original", "original_part9")
    one = {c: [total_in(r["usage"]) for r in rows if r["cond"] == c and r.get("turns") == 1 and r.get("usage")] for c in ("pasted", "original")}
    med = {c: (st.median(v) if v else None) for c, v in one.items()}
    out["one_turn_median_total_input_tokens"] = {**med, "n": {c: len(v) for c, v in one.items()}}
    gap = med["original"] - med["pasted"] if med["original"] is not None and med["pasted"] is not None else None
    out["original_minus_pasted_tokens"] = gap
    per_cond = {}
    for c in ("pasted", "original"):
        rs = [r for r in rows if r["cond"] == c]
        steps = []   # five-hour meter step between consecutive rows (same window), attributed to the earlier row: free data for the quota study
        for a, b in zip(rows, rows[1:]):
            ra, rb = a.get("rate_limit") or {}, b.get("rate_limit") or {}
            if a["cond"] == c and ra.get("five_hour") is not None and rb.get("five_hour") is not None and ra.get("five_hour_resets_local") == rb.get("five_hour_resets_local"):
                steps.append(rb["five_hour"] - ra["five_hour"])
        per_cond[c] = {"n": len(rs), "median_turns": st.median(r["turns"] for r in rs if r["turns"]), "share_with_tool_calls": round(sum(1 for r in rs if r["tool_calls"]) / len(rs), 3),
                       "median_output_tokens": st.median(r["output_tokens"] for r in rs if r["output_tokens"]),
                       "mean_meter_step_points": round(100 * sum(steps) / len(steps), 3) if steps else None, "meter_steps_n": len(steps)}
    out["per_condition"] = per_cond
    out["verdicts_against_prediction"] = {
        "R1_pasted_within_3pp_of_original_and_interval_includes_0": "holds" if abs(r1["diff_pp"]) <= 3 and r1["ci_pp"][0] <= 0 <= r1["ci_pp"][1] else
            ("interval excludes 0: the delivery route matters, direction " + ("pasted higher" if r1["diff_pp"] > 0 else "pasted lower") if not r1["ci_pp"][0] <= 0 <= r1["ci_pp"][1] else "point estimate beyond 3 points, interval includes 0"),
        "R2_pasted_at_least_3pp_above_none_interval_above_0": "holds" if r2["diff_pp"] >= 3 and r2["ci_pp"][0] > 0 else "fails",
        "R3_original_minus_pasted_between_0_and_250_tokens": None if gap is None else ("holds" if 0 <= gap <= 250 else "fails"),
        "R4_pasted_median_one_turn_no_tool_calls": "holds" if per_cond["pasted"]["median_turns"] == 1 and per_cond["pasted"]["share_with_tool_calls"] == 0 else "fails",
        "R5_original_within_5pp_of_part9": "holds" if abs(out["original_this_run_minus_part9"]["diff_pp"]) <= 5 else "fails"}
    (Path(run) / "quality_pasted_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], args[1], "--allow-partial" in sys.argv)
