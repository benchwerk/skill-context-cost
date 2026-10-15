#!/usr/bin/env python3
"""Cost and structure by type of skill. Usage: python analysis/analyze_types.py <main run> <invocation run>

Joins skill_features.json (counted), skill_labels.json (external labels against taxonomy.md) and the measured costs.
Per-skill cost: listing = measured (top 20) else estimate a + b * listing_chars from the length-sweep fit, 0 if manual-only;
invocation = measured (top 20) else estimate 0.37 * body_chars + 50 (a rate chosen below the measured median of 0.379). Measured and estimated values are not
labelled separately in the output. Writes type_findings.json."""
import collections, json, statistics as st, sys
from pathlib import Path

A = Path(__file__).resolve().parent
DOM = {"D1": "software-process", "D2": "frontend-ui-design", "D3": "platform-reference", "D4": "tool-operation", "D5": "media-generation",
       "D6": "business-marketing", "D7": "office-documents", "D8": "agent-meta", "D9": "other"}
FORM = {"F1": "procedure", "F2": "reference", "F3": "rules-and-style", "F4": "tool-wrapper", "F5": "persona-or-mode", "F6": "stub-pointer"}
COARSE = {"F1": "procedural", "F4": "procedural", "F2": "knowledge", "F3": "knowledge", "F5": "mode-or-stub", "F6": "mode-or-stub"}


def med(x):
    return st.median(x) if x else None


def main(main_run, inv_run):
    feats = json.loads((A / "skill_features.json").read_text(encoding="utf-8"))
    labels = {x["name"]: x for x in json.loads((A / "skill_labels.json").read_text(encoding="utf-8"))}
    mf = json.loads((Path(main_run) / "findings.json").read_text(encoding="utf-8"))
    fit = mf["comparisons"]["fit"]
    inv = {r["skill"]: r for r in json.loads((Path(inv_run) / "invocation_findings.json").read_text(encoding="utf-8"))["skills"]}
    rows = []
    for f in feats:
        lab = labels[f["name"]]
        m = inv.get(f["name"])
        listing = 0 if f["manual_only"] else (m["listing_tokens"] if m else round(fit["per_skill_constant_tokens"] + fit["tokens_per_listing_char"] * f["listing_chars"]))
        invocation = m["invocation_tokens"] if m else round(0.37 * f["body_chars"] + 50)
        rows.append({**f, **{k: lab[k] for k in ("domain", "form", "clarity", "confidence")}, "coarse_form": COARSE[lab["form"]],
                     "listing_tokens": listing, "invocation_tokens": invocation, "cost_measured": bool(m)})

    def group(key, names):
        out = {}
        for k, label in names.items():
            g = [r for r in rows if r[key] == k]
            if not g:
                continue
            auto = [r for r in g if not r["manual_only"]]
            out[k] = {"label": label, "n": len(g), "share": round(len(g) / len(rows), 3),
                      "median_body_chars": med([r["body_chars"] for r in g]), "median_listing_chars": med([r["listing_chars"] for r in auto]),
                      "median_listing_tokens": med([r["listing_tokens"] for r in auto]), "median_invocation_tokens": med([r["invocation_tokens"] for r in g]),
                      "total_listing_tokens": sum(r["listing_tokens"] for r in g),
                      "multi_file_share": round(sum(1 for r in g if r["folder_files"] > 0) / len(g), 2),
                      "points_to_files_share": round(sum(1 for r in g if r["referenced_files_in_body"] > 0) / len(g), 2),
                      "median_deferred_share_if_any": med([r["deferred_share"] for r in g if r["referenced_files_in_body"] > 0]),
                      "has_scripts_share": round(sum(1 for r in g if r["has_scripts"]) / len(g), 2),
                      "manual_only": sum(1 for r in g if r["manual_only"]), "median_clarity": med([r["clarity"] for r in g]),
                      "examples": [r["name"] for r in sorted(g, key=lambda r: r.get("popular_rank") or 999)[:4]]}
        return out
    res = {"n": len(rows), "by_domain": group("domain", DOM), "by_form": group("form", FORM),
           "by_coarse_form": group("coarse_form", {"procedural": "procedure + tool-wrapper", "knowledge": "reference + rules-and-style", "mode-or-stub": "persona/mode + stub"}),
           "by_clarity": {}}
    for c in (1, 2, 3):
        g = [r for r in rows if r["clarity"] == c]
        res["by_clarity"][c] = {"n": len(g), "median_description_chars": med([r["description_chars"] for r in g]),
                                "trigger_phrase_share": round(sum(r["description_has_trigger_phrase"] for r in g) / len(g), 2) if g else None}
    pop = [r for r in rows if r["set"] == "popular"]
    rnd = [r for r in rows if r["set"] == "random"]
    res["popular_vs_random_only"] = {"popular_median_invocation": med([r["invocation_tokens"] for r in pop]), "random_median_invocation": med([r["invocation_tokens"] for r in rnd]),
                                     "popular_median_listing_automatic": med([r["listing_tokens"] for r in pop if not r["manual_only"]]),
                                     "random_median_listing_automatic": med([r["listing_tokens"] for r in rnd if not r["manual_only"]])}
    # which skills concentrate the cost
    tot_l = sum(r["listing_tokens"] for r in rows)
    top = sorted(rows, key=lambda r: -r["listing_tokens"])[:10]
    res["listing_concentration"] = {"total_listing_tokens_all_138": tot_l, "top10_share": round(sum(r["listing_tokens"] for r in top) / tot_l, 3),
                                    "top10": [(r["name"], r["listing_tokens"], r["domain"]) for r in top]}
    big = sorted(rows, key=lambda r: -r["invocation_tokens"])[:8]
    res["invocation_extremes"] = [(r["name"], r["invocation_tokens"], r["domain"], r["form"], r["deferred_share"]) for r in big]
    (A / "type_findings.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("wrote type_findings.json")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
