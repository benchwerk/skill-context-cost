#!/usr/bin/env python3
"""Output-quality results for the design skill. Usage: python analysis/analyze_quality.py results/<quality run>

Score of a page = share of the 16 mechanical checks it passes (a check passes when the forbidden pattern is absent). A reply with no
HTML scores 0 and is also counted separately. The unit of analysis is the brief: samples of one brief are averaged first, then the
12 brief means are compared, with a seeded bootstrap over briefs (5,000 resamples, percentile 95% interval). Comparisons and
decision rules are the ones fixed in prediction.md (Part 9) and quality_protocol.md:
  Q1  original minus none: positive control (interval above 0, point estimate at least +3 points)
  Q2  placebo minus none: within +-3 points
  Q3  split minus original: not worse if the lower bound is above -10 points
  Q4  share of split runs that opened a reference file: under 25%
  Q5  em-dash share: none at least 25%, original lower
Writes quality_findings.json."""
import collections, json, random, statistics as st, sys
from pathlib import Path

CONDS = ["none", "original", "split", "placebo"]


def boot(task_means, a, b, n=5000, seed=7):
    """difference of condition means over tasks with a bootstrap over tasks; task_means[cond][task] -> mean score"""
    tasks = sorted(set(task_means[a]) & set(task_means[b]))
    if not tasks:
        return None
    d = [task_means[a][t] - task_means[b][t] for t in tasks]
    rnd = random.Random(seed)
    boots = sorted(sum(rnd.choice(d) for _ in d) / len(d) for _ in range(n))
    return {"diff": sum(d) / len(d), "ci": [boots[int(0.025 * n)], boots[int(0.975 * n) - 1]], "tasks": len(tasks)}


def secondary(run, rows, by):
    """Exploratory sensitivity analyses added after an independent review of the checks (see quality_checks_v2.py): the same pages
    scored with the repaired checks (v2), and scores restricted to the checks that fail on at least one page (the others are at
    ceiling for every condition). The primary analysis above is unchanged and is the one the decision rules use."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bench"))
    from quality_checks_v2 import run_checks_v2
    res = {}
    v2 = {}
    for r in rows:
        f = list((run / "outputs").glob(f"{r['seq']:03d}_{r['cond']}_{r['task']}_{r['sample']}.txt"))
        v2[r["seq"]] = run_checks_v2(f[0].read_text(encoding="utf-8")) if f else {"has_html": False, "results": {}}
    def variant(name, getter, keep=None):
        tm = {}
        for c in CONDS:
            per = collections.defaultdict(list)
            for r in by[c]:
                ch = getter(r)
                if keep is not None:
                    ch = {k: v for k, v in ch.items() if k in keep}
                per[r["task"]].append(sum(ch.values()) / len(ch) if ch else 0.0)
            if per:
                tm[c] = {t: sum(v) / len(v) for t, v in per.items()}
        entry = {"mean_score_pct": {c: round(100 * sum(v.values()) / len(v), 2) for c, v in tm.items()}}
        for label, a, b in (("original minus none", "original", "none"), ("placebo minus none", "placebo", "none"), ("split minus original", "split", "original"), ("split minus none", "split", "none")):
            if a in tm and b in tm:
                d = boot(tm, a, b)
                entry[label] = {"diff_pp": round(d["diff"] * 100, 2), "ci_pp": [round(d["ci"][0] * 100, 2), round(d["ci"][1] * 100, 2)]}
        res[name] = entry
        return tm
    v1 = lambda r: r["checks"] if r["has_html"] else {}
    v2get = lambda r: v2[r["seq"]]["results"]
    informative_v1 = {k for r in rows if r["has_html"] for k, ok in r["checks"].items() if not ok}
    informative_v2 = {k for r in rows for k, ok in v2[r["seq"]]["results"].items() if not ok}
    variant("v1_all_16_checks (primary)", v1)
    variant("v2_all_16_checks", v2get)
    variant("v1_only_checks_that_fail_somewhere", v1, informative_v1)
    variant("v2_only_checks_that_fail_somewhere", v2get, informative_v2)
    res["checks_that_fail_somewhere_v1"] = sorted(informative_v1)
    res["checks_that_fail_somewhere_v2"] = sorted(informative_v2)
    res["pages_where_v1_and_v2_disagree_on_a_check"] = sum(1 for r in rows if r["has_html"] and any(r["checks"].get(k) != v2[r["seq"]]["results"].get(k) for k in r["checks"]))
    return res


def main(run):
    run = Path(run)
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("finished")]
    env = json.loads((run / "env.json").read_text(encoding="utf-8"))
    for r in rows:
        ch = r["checks"] or {}
        r["score"] = sum(ch.values()) / len(ch) if r["has_html"] and ch else 0.0
    by = {c: [r for r in rows if r["cond"] == c] for c in CONDS}
    out = {"run": run.name, "claude_version": env.get("claude_version"), "generations": len(rows), "per_condition": {}}
    task_means = {}
    for c, rs in by.items():
        if not rs:
            continue
        tm = collections.defaultdict(list)
        for r in rs:
            tm[r["task"]].append(r["score"])
        task_means[c] = {t: sum(v) / len(v) for t, v in tm.items()}
        names = sorted({k for r in rs if r["has_html"] for k in r["checks"]})
        out["per_condition"][c] = {
            "n": len(rs), "briefs": len(tm), "has_html_share": round(sum(r["has_html"] for r in rs) / len(rs), 3),
            "mean_score": round(sum(task_means[c].values()) / len(task_means[c]), 4),
            "perfect_pages_share": round(sum(1 for r in rs if r["score"] == 1.0) / len(rs), 3),
            "median_html_chars": st.median(r["html_chars"] for r in rs if r["html_chars"]) if any(r["html_chars"] for r in rs) else None,
            "median_output_tokens": st.median(r["output_tokens"] for r in rs if r["output_tokens"]) if any(r["output_tokens"] for r in rs) else None,
            "share_with_reference_reads": round(sum(1 for r in rs if r["reference_reads"] > 0) / len(rs), 3),
            "median_turns": st.median(r["turns"] for r in rs if r["turns"]) if any(r["turns"] for r in rs) else None,
            "check_pass_rate": {k: round(sum(r["checks"][k] for r in rs if r["has_html"]) / max(1, sum(1 for r in rs if r["has_html"])), 3) for k in names}}
    comp = {}
    for label, a, b in (("Q1 original minus none", "original", "none"), ("Q2 placebo minus none", "placebo", "none"),
                        ("Q3 split minus original", "split", "original"), ("split minus none", "split", "none"), ("original minus placebo", "original", "placebo")):
        if a in task_means and b in task_means:
            comp[label] = boot(task_means, a, b)
    out["comparisons_points"] = {k: ({"diff_pp": round(v["diff"] * 100, 2), "ci_pp": [round(v["ci"][0] * 100, 2), round(v["ci"][1] * 100, 2)], "briefs": v["tasks"]} if v else None) for k, v in comp.items()}
    verdicts = {}
    q1 = comp.get("Q1 original minus none")
    if q1:
        verdicts["Q1_positive_control"] = "holds" if q1["ci"][0] > 0 and q1["diff"] >= 0.03 else ("checks not sensitive here (interval includes 0)" if q1["ci"][0] <= 0 else "effect under 3 points")
    q2 = comp.get("Q2 placebo minus none")
    if q2:
        verdicts["Q2_placebo_within_3pp"] = "holds" if abs(q2["diff"]) <= 0.03 else "fails"
    q3 = comp.get("Q3 split minus original")
    if q3:
        lo, hi = q3["ci"]
        if lo > -0.10 and hi < 0:
            verdicts["Q3_split_not_worse"] = "within the 10-point margin, but a decrease is detected (interval below 0): the rule is met, the split version is not equal"
        elif lo > -0.10:
            verdicts["Q3_split_not_worse"] = "no evidence of harm beyond 10 points (interval includes 0)"
        else:
            verdicts["Q3_split_not_worse"] = "harm not excluded (lower bound at or below -10 points)"
    if "split" in out["per_condition"]:
        verdicts["Q4_split_reads_under_25pct"] = "holds" if out["per_condition"]["split"]["share_with_reference_reads"] < 0.25 else "fails"
    emd = {c: 1 - v["check_pass_rate"].get("no_em_dash", 1) for c, v in out["per_condition"].items()}
    if "none" in emd and "original" in emd:
        verdicts["Q5_em_dash"] = "holds" if emd["none"] >= 0.25 and emd["original"] < emd["none"] else "fails"
    out["em_dash_share_of_pages"] = {c: round(v, 3) for c, v in emd.items()}
    out["verdicts_against_prediction"] = verdicts
    allk = collections.defaultdict(list)
    for c, v in out["per_condition"].items():
        for k, x in v["check_pass_rate"].items():
            allk[k].append(x)
    out["checks_that_never_fail_in_any_condition"] = sorted(k for k, v in allk.items() if min(v) == 1.0)
    out["secondary_exploratory"] = secondary(run, rows, by)
    (run / "quality_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"generations {len(rows)}")
    for c, v in out["per_condition"].items():
        print(f"{c:9s} n={v['n']:3d} html={v['has_html_share']:.2f} score={v['mean_score']*100:6.2f}% perfect={v['perfect_pages_share']:.2f} refreads={v['share_with_reference_reads']:.2f} outtok={v['median_output_tokens']} turns={v['median_turns']}")
    for k, v in out["comparisons_points"].items():
        print(f"{k:28s} {v['diff_pp'] if v else None} pp  {v['ci_pp'] if v else ''}")
    print("em-dash share of pages:", out["em_dash_share_of_pages"])
    print(json.dumps(verdicts, indent=1))
    print("never-failing checks:", out["checks_that_never_fail_in_any_condition"])
    print("\nSECONDARY (exploratory, after an independent review of the checks):")
    for k, v in out["secondary_exploratory"].items():
        if isinstance(v, dict):
            print(" ", k, v["mean_score_pct"])
            for kk, vv in v.items():
                if kk != "mean_score_pct":
                    print("     ", kk, vv["diff_pp"], "pp", vv["ci_pp"])
        else:
            print(" ", k, v)


if __name__ == "__main__":
    main(sys.argv[1])
