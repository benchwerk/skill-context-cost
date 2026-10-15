#!/usr/bin/env python3
"""Turn a run folder into findings.json and estimates.json.

Usage: python analysis/analyze.py results/<run>

Definitions (fixed before any data):
- window total of a run = input + cache_creation + cache_read tokens of the first request. Output tokens are separate.
- added tokens of a configuration = its median window total minus the median of C0 for the SAME model. Every added
  figure carries `min`/`max`: the smallest and largest single run minus the C0 median.
- share of window = added / the context window of the model that ran (env.json model_windows). Never another window.
- a run is excluded from the medians when the skills Claude Code reports differ from the expected set (beyond the
  skills already reported by C0, the bundled baseline), when it has no start-up message or no usage; counts are reported.
- HEADLINE `typical_popular_skill_tokens`: the marginal cost per skill between C10 and C50 on the first model,
  (added C50 - added C10) / 40, with a min/max range from the run extremes. A single skill's own cost is not taken from
  C1 - C0, which also contains a fixed overhead.
- Model: added(set) = F + sum over skills of (a + b * listing_chars). b from the length sweep slope (sweep N fixed);
  F (fixed overhead of having any skill) and a (per-skill constant) from the sweep intercept and the F1 probe.
  Estimates for all skills = a + b * listing_chars (estimate, fitted on synthetic English text, below the listing cap).
"""
import json, re, statistics as st, sys
from pathlib import Path


def window_total(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def spread(v):
    return {"median": st.median(v), "min": min(v), "max": max(v), "n": len(v)}


def linfit(pts):
    n = len(pts)
    mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    if sxx == 0:
        return None
    b = sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
    a = my - b * mx
    ss_tot = sum((p[1] - my) ** 2 for p in pts)
    ss_res = sum((p[1] - (a + b * p[0])) ** 2 for p in pts)
    return {"intercept": a, "slope": b, "r2": (1 - ss_res / ss_tot) if ss_tot else None}


def main(run):
    run = Path(run)
    env = json.loads((run / "env.json").read_text(encoding="utf-8"))
    man = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    flags_path = Path(__file__).resolve().parent / "skill_flags.json"
    flags = json.loads(flags_path.read_text(encoding="utf-8")) if flags_path.exists() else {}
    hidden = {n for n, f in flags.items() if f.get("user_invocable_false")}   # offered to the model, not in the start-up list
    manual = {n for n, f in flags.items() if f.get("disable_model_invocation")}   # not offered to the model: cost nothing
    windows = dict(env["model_windows"])
    for r in rows:   # the window Claude Code itself reports wins over the configured one; a mismatch is recorded
        mu = (r.get("model_usage") or {}).get(r["model"]) or {}
        if mu.get("contextWindow") and mu["contextWindow"] != windows.get(r["model"]):
            windows[r["model"]] = mu["contextWindow"]
            env.setdefault("window_mismatch", []).append(r["model"])
    models = sorted({r["model"] for r in rows}, key=lambda m: env["models"].index(m) if m in env["models"] else 99)

    # baseline contents (skills Claude Code reports with no skills installed), per model
    baseline = {}
    for m in models:
        sets = [set(r.get("init_skills", [])) for r in rows if r["model"] == m and r["config"] == "C0" and "init_skills" in r]
        baseline[m] = set.intersection(*sets) if sets else set()

    for r in rows:
        r["_excluded"] = None
        if not r.get("usage") or r.get("returncode") not in (0, None):
            r["_excluded"] = "no usage or non-zero exit"
        elif "init_skills" not in r:
            r["_excluded"] = "no start-up message"
        else:
            seen = set(r["init_skills"])
            extra = seen - set(r["expected_skills"]) - baseline[r["model"]]
            miss = set(r["expected_skills"]) - seen - hidden
            r["_unexpected"], r["_missing"] = sorted(extra), sorted(miss)
            if extra or miss:
                r["_excluded"] = "skills reported differ from expected"
    good = [r for r in rows if not r["_excluded"]]
    excluded = [{"seq": r["seq"], "config": r["config"], "model": r["model"], "why": r["_excluded"],
                 "unexpected": r.get("_unexpected"), "missing": r.get("_missing"), "stderr_tail": r.get("stderr_tail")}
                for r in rows if r["_excluded"]]

    by = {}
    for r in good:
        by.setdefault((r["model"], r["config"]), []).append(r)

    findings = {"run": run.name, "claude_version": env.get("claude_version"), "model_windows": windows, "window_mismatch": env.get("window_mismatch", []),
                "excluded_runs": excluded, "baseline_reported_skills": {m: sorted(baseline[m]) for m in models},
                "tools_identical_to_C0": {}, "models": {}}
    for m in models:
        base_rows = by.get((m, "C0"), [])
        base_tools = {tuple(sorted(r.get("init_tools", []))) for r in base_rows}
        for (mm, cfg), rs in by.items():
            if mm == m:
                findings["tools_identical_to_C0"].setdefault(m, {})[cfg] = {tuple(sorted(r.get("init_tools", []))) for r in rs} == base_tools \
                    if len(base_tools) == 1 else None
        if not base_rows:
            findings["models"][m] = {"error": "no usable C0 runs"}
            continue
        c0 = st.median(window_total(r["usage"]) for r in base_rows)
        c0_tot = [window_total(r["usage"]) for r in base_rows]
        out = {"window_tokens": windows.get(m), "C0_window_total": spread(c0_tot), "configs": {}}
        for (mm, cfg), rs in sorted(by.items(), key=lambda kv: (kv[0][1] != "C0", kv[0][1])):
            if mm != m:
                continue
            tot = [window_total(r["usage"]) for r in rs]
            n_exp = rs[0]["n_expected"]
            added = st.median(tot) - c0
            names = rs[0]["expected_skills"]
            row = {"n_skills": n_exp, "n_model_visible": sum(1 for x in names if x not in manual),
                   "manual_only_skills_in_set": sorted(x for x in names if x in manual), "runs": len(rs), "window_total": spread(tot),
                   "cache_creation": spread([r["usage"].get("cache_creation_input_tokens", 0) or 0 for r in rs]),
                   "cache_read": spread([r["usage"].get("cache_read_input_tokens", 0) or 0 for r in rs]),
                   "output": spread([r["usage"].get("output_tokens", 0) or 0 for r in rs]),
                   "added": added, "added_min": min(tot) - c0, "added_max": max(tot) - c0,
                   "added_share_of_own_window": (added / windows[m]) if windows.get(m) else None,
                   "result_subtypes": sorted({str(r.get("result_subtype")) for r in rs})}
            out["configs"][cfg] = row
        # marginal cost along the real prefix sets C0, C1, C10, C50, C100 (exact names only)
        chain = sorted(((int(c[1:]), c) for c in out["configs"] if re.fullmatch(r"C[1-9]\d*", c)))
        prev, prev_marg = (0, 0.0), None
        for n, c in chain:
            row = out["configs"][c]
            marg = (row["added"] - prev[1]) / (n - prev[0])
            row["marginal_per_skill_since_previous_N"] = marg
            if prev_marg is not None and prev[0] > 0 and marg < 0.7 * prev_marg:
                row["cap_suspected"] = True
            prev, prev_marg = (n, row["added"]), (marg if n > 1 else None)
        cf = out["configs"]
        if "C10" in cf and "C50" in cf:
            lo = (cf["C50"]["added_min"] - cf["C10"]["added_max"]) / 40
            hi = (cf["C50"]["added_max"] - cf["C10"]["added_min"]) / 40
            out["typical_popular_skill_tokens"] = {"value": (cf["C50"]["added"] - cf["C10"]["added"]) / 40, "min": lo, "max": hi,
                                                   "definition": "(added C50 - added C10) / 40, tokens per skill, this model"}
            dv = cf["C50"]["n_model_visible"] - cf["C10"]["n_model_visible"]
            if dv > 0:
                out["typical_model_visible_skill_tokens"] = {"value": (cf["C50"]["added"] - cf["C10"]["added"]) / dv,
                                                             "definition": "(added C50 - added C10) / (skills offered to the model in C50 minus C10)"}
        findings["models"][m] = out

    # comparisons, fit and estimates on the first model (single-model configurations run there)
    m0 = models[0]
    cf = findings["models"][m0].get("configs", {}) if "configs" in findings["models"].get(m0, {}) else {}
    comp, est = {}, {}
    n = None
    for cid in cf:
        pass
    sw = sorted(((int(re.fullmatch(r"S(\d+)-L(\d+)", c).group(2)), c) for c in cf if re.fullmatch(r"S\d+-L\d+", c)))
    if sw:
        n = cf[sw[0][1]]["n_skills"]
        pts = []
        for length, c in sw:
            sk = man["synthetic"][c]
            pts.append((sum(x["listing_chars"] for x in sk) / len(sk), cf[c]["added"]))
        fit = linfit(pts)
        comp["sweep_points_chars_vs_added"] = pts
        if fit:
            b = fit["slope"] / n
            comp["fit"] = {"tokens_per_listing_char": b, "r2": fit["r2"], "sweep_n": n}
            f1 = cf.get("F1")
            f1c = man["synthetic"]["F1"][0]["listing_chars"] if "F1" in man["synthetic"] else None
            if f1 and f1c is not None and n > 1:
                a = (fit["intercept"] - f1["added"] + b * f1c) / (n - 1)
                F = f1["added"] - a - b * f1c
                comp["fit"].update({"per_skill_constant_tokens": a, "fixed_overhead_tokens": F})
                allskills = {s["name"]: s for s in man["real_order"] + man.get("random_set", [])}
                est = {nm: round(a + b * s["listing_chars"], 1) for nm, s in allskills.items()}
                val = []
                for c, names in man["sets"].items():
                    if c in cf and (re.fullmatch(r"C(10|50|100)", c) or c == "R50"):
                        pred = F + sum(a + b * allskills[x]["listing_chars"] for x in names)
                        val.append({"config": c, "measured": cf[c]["added"], "estimated": pred,
                                    "error_pct": 100 * (pred - cf[c]["added"]) / cf[c]["added"] if cf[c]["added"] else None})
                for k in range(1, 6):
                    t = cf.get(f"T{k}")
                    if t:
                        s = man["real_order"][k - 1]
                        inc = t["added"] - f1["added"]
                        pred_inc = b * (s["listing_chars"] - f1c)
                        val.append({"config": f"T{k}", "skill": s["name"], "measured_increment_over_F1": inc, "estimated_increment": pred_inc,
                                    "error_tokens": pred_inc - inc, "non_ascii_share": s.get("non_ascii_share")})
                comp["fit_validation"] = val
    bl = None
    for c in cf:
        mt = re.fullmatch(r"S(\d+)-B(\d+)", c)
        if mt:
            bl = mt.group(2)
            twin = f"S{mt.group(1)}-L{bl}"
            if twin in cf:
                comp["body_check"] = {"difference_added_tokens": cf[c]["added"] - cf[twin]["added"],
                                      "range": [cf[c]["added_min"] - cf[twin]["added_max"], cf[c]["added_max"] - cf[twin]["added_min"]],
                                      "meaning": "about 0 = skill bodies are not in the starting context"}
    for k in ("C50-disable", "C50-trim100"):
        if k in cf and "C50" in cf and cf["C50"]["added"]:
            saved = cf["C50"]["added"] - cf[k]["added"]
            comp[k] = {"added": cf[k]["added"], "C50_added": cf["C50"]["added"], "saved": saved,
                       "saved_share": saved / cf["C50"]["added"],
                       "saved_range": [cf["C50"]["added_min"] - cf[k]["added_max"], cf["C50"]["added_max"] - cf[k]["added_min"]],
                       "required_caveat": "disable: the skill is no longer offered to the model and can only be started by name; trim: "
                                          "whether the skill still triggers when it should was not measured"}
    if "R50" in cf and "C50" in cf and cf["C50"]["added"]:
        comp["popular50_vs_random50"] = {"popular_C50_added": cf["C50"]["added"], "random_R50_added": cf["R50"]["added"],
                                         "ratio_random_to_popular": cf["R50"]["added"] / cf["C50"]["added"]}
    if len(models) > 1:
        mb = findings["models"][models[1]].get("configs", {})
        comp["second_model_vs_first"] = {c: {"first": cf[c]["added"], "second": mb[c]["added"],
                                             "ratio": (mb[c]["added"] / cf[c]["added"]) if cf[c]["added"] else None}
                                         for c in ("C1", "C10", "C50", "C100") if c in cf and c in mb}
    findings["comparisons"] = comp
    (run / "findings.json").write_text(json.dumps(findings, indent=1) + "\n", encoding="utf-8", newline="\n")
    (run / "estimates.json").write_text(json.dumps({"label": "estimate: fitted on synthetic English descriptions below the "
                                                    "listing cap; see comparisons.fit_validation for errors", m0: est}, indent=1) + "\n",
                                        encoding="utf-8", newline="\n")
    print("wrote", run / "findings.json")


if __name__ == "__main__":
    main(sys.argv[1])
