#!/usr/bin/env python3
"""Invocation cost of the most-installed skills: tokens added when a skill is run by hand, beyond being listed.

Usage: python analysis/analyze_invocation.py results/<invocation run> results/<main run>

For skill k: L_k = the skill alone, prompt "x" (listed only); I_k = the skill alone, prompt "/<name>" (invoked by hand).
listing_tokens  = L_k - C0               (C0 = empty session of the same model, from the main run)
invocation_tokens = I_k - L_k            (what running the skill adds: the body plus a small fixed overhead)
Window total = input + cache_creation + cache_read of the first request. Fit: invocation_tokens = overhead + b * body_chars
(least squares over the skills). Writes invocation_findings.json into the invocation run folder."""
import json, statistics as st, sys
from pathlib import Path


def total(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def main(inv, main_run):
    inv, main_run = Path(inv), Path(main_run)
    man = json.loads((inv / "manifest.json").read_text(encoding="utf-8"))
    flags = json.loads((Path(__file__).resolve().parent / "skill_flags.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in (inv / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    model = rows[0]["model"]
    mf = json.loads((main_run / "findings.json").read_text(encoding="utf-8"))
    c0 = mf["models"][model]["C0_window_total"]["median"]
    by = {r["config"]: r for r in rows if r.get("usage")}
    out, pts = [], []
    for k in range(1, 21):
        i, l = by.get(f"I{k}"), by.get(f"L{k}")
        s = man["real_order"][k - 1]
        if not i or not l:
            out.append({"k": k, "skill": s["name"], "error": "missing run"})
            continue
        listing, inv_t = total(l["usage"]) - c0, total(i["usage"]) - total(l["usage"])
        manual = flags.get(s["name"], {}).get("disable_model_invocation", False)
        row = {"k": k, "skill": s["name"], "source": s["source"], "body_chars": s["body_chars"],
               "listing_tokens": listing, "invocation_tokens": inv_t, "manual_only": manual,
               "tokens_per_body_char": inv_t / s["body_chars"] if s["body_chars"] else None,
               "invocations_to_equal_listing_per_session": (inv_t / listing) if listing > 0 else None,
               "init_ok": "init_skills" in i and s["name"] in i["init_skills"]}
        out.append(row)
        pts.append((s["body_chars"], inv_t))
    n = len(pts)
    mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    b = sum((p[0] - mx) * (p[1] - my) for p in pts) / sum((p[0] - mx) ** 2 for p in pts)
    a = my - b * mx
    ss_res = sum((p[1] - (a + b * p[0])) ** 2 for p in pts)
    ss_tot = sum((p[1] - my) ** 2 for p in pts)
    cross = []
    for t in range(1, 6):   # reproducibility: listed-only totals against the main run's single-skill configs
        mc = mf["models"][model]["configs"].get(f"T{t}")
        if mc and f"L{t}" in by:
            cross.append({"skill": t, "this_run": total(by[f"L{t}"]["usage"]) - c0, "main_run": mc["added"]})
    bodies = sorted(p[0] for p in pts)
    res = {"model": model, "C0": c0, "skills": out,
           "fit": {"overhead_tokens": a, "tokens_per_body_char": b, "r2": 1 - ss_res / ss_tot if ss_tot else None, "n": n},
           "median_body_chars": st.median(bodies), "median_invocation_tokens": st.median(p[1] for p in pts),
           "max_invocation_tokens": max(p[1] for p in pts),
           "listing_cross_check_against_main_run": cross,
           "median_invocations_to_equal_listing": st.median(r["invocations_to_equal_listing_per_session"] for r in out
                                                             if r.get("invocations_to_equal_listing_per_session") is not None)}
    (inv / "invocation_findings.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote", inv / "invocation_findings.json")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
