"""Part 14A-D (prediction.md): scores the first-request totals of results/*_part14/raw.jsonl. -> part14_findings.json next to the raw file.
  python analysis/analyze_part14.py results/<date>_<machine>_part14"""
import collections, json, statistics, sys
from pathlib import Path

d = Path(sys.argv[1])
rows = [json.loads(l) for l in (d / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
g = collections.defaultdict(list)
for r in rows:
    g[(r["part"], r["model"], r["condition"])].append(r["window_total"])
med = {k: statistics.median(v) for k, v in g.items()}
exact = {f"{k[0]}/{k[1]}/{k[2]}": len(set(v)) == 1 for k, v in g.items() if k[0] == "A"}
f = {"A1_runs_repeat_exactly_all_settings": all(exact.values()), "A_totals": {f"{m}/{c}": med[("A", m, c)] for (p, m, c) in med if p == "A"}}
removed = {}
for m in ("sonnet", "haiku", "opus"):
    base = med[("A", m, "default")]
    removed[m] = {c: base - med[("A", m, c)] for c in ("no-skills", "tools3", "tools1", "system-prompt", "exclude-dynamic", "minimal")}
    removed[m]["tools3_share_of_default"] = round(removed[m]["tools3"] / base, 3)
f["A_removed_tokens"] = removed
f["A2"] = {m: 2500 <= removed[m]["no-skills"] <= 3500 for m in removed}
f["A3"] = {m: removed[m]["tools3"] > 10000 and removed[m]["tools3_share_of_default"] > 0.60 for m in removed}
f["A4"] = {m: 1500 <= removed[m]["system-prompt"] <= 3000 for m in removed}
f["A5"] = {m: removed[m]["exclude-dynamic"] < 500 for m in removed}
f["A6"] = {"haiku_larger_than_sonnet": med[("A", "haiku", "default")] > med[("A", "sonnet", "default")],
           "opus_within_500_of_sonnet": abs(med[("A", "opus", "default")] - med[("A", "sonnet", "default")]) <= 500}
f["A7"] = {m: med[("A", m, "minimal")] <= 4000 for m in removed}
b0 = med[("B", "sonnet", "syn0")]
add = {n: med[("B", "sonnet", f"syn{n}")] - b0 for n in (100, 200, 400)}
bundled = removed["sonnet"]["no-skills"]
f["B_added"] = add
f["B1_within_5pct_of_100"] = {n: abs(add[n] - add[100]) / add[100] <= 0.05 for n in (200, 400)}
f["B_growth_200_to_400_pct"] = round(100 * (add[400] - add[200]) / add[200], 1)
f["B2_total_listing_400"] = {"tokens": bundled + add[400], "pct_of_1M": round(100 * (bundled + add[400]) / 1_000_000, 2), "in_9500_12500": 9500 <= bundled + add[400] <= 12500}
base, idle, atf, pas = (med[("C", "sonnet", c)] for c in ("base", "file-present-unreferenced", "at-file", "pasted"))
f["C"] = {"base": base, "file_present_unreferenced": idle, "at_file": atf, "pasted": pas, "idle_vs_empty_session": idle - b0,
          "at_file_rise": atf - base, "pasted_rise": pas - base, "at_file_minus_pasted": atf - pas,
          "C1_idle_within_30": abs(idle - b0) <= 30, "C2_within_150_of_pasted": abs(atf - pas) <= 150, "C3_rise_at_least_2000": atf - base >= 2000}
f["D"] = {c: {"median": med[("D", "sonnet", c)], "added_over_baseline": med[("D", "sonnet", c)] - med[("D", "sonnet", "baseline")]}
          for c in ("invoke-plugin-authoring", "invoke-run-skill-generator")}
f["D1_each_body_over_1000"] = all(v["added_over_baseline"] > 1000 for v in f["D"].values())
f["D2"] = "not tested: a single listing entry cannot be separated from the others"
(d / "part14_findings.json").write_text(json.dumps(f, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: f[k] for k in f if k not in ("A_totals",)}, indent=1))
