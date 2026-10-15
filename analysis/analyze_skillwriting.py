"""Part 14E (prediction.md): scores results/<date>_<machine>_skillwriting. -> skillwriting_findings.json
The prediction named a hand-written arm; no human wrote skills for this part, so E2 compares with the published human-written skills of the workload
(description length of the 100 most-installed and the random set), a deviation recorded in RESULTS.md.
  python analysis/analyze_skillwriting.py results/<folder>"""
import collections, json, statistics, sys
from pathlib import Path

d = Path(sys.argv[1])
root = Path(__file__).resolve().parents[1]
load = lambda f: [json.loads(l) for l in (d / f).read_text(encoding="utf-8").splitlines() if l.strip()] if (d / f).exists() else []
gen = load("generation.jsonl")
trg = list({(r["arm"], r["task"], r["prompt_id"]): r for r in load("triggers.jsonl") if r["decision"] != "timeout"}.values())   # one row per prompt; the last one wins
ARMS = ["plain", "plugin-authoring", "skill-creator"]
man = json.loads((root / "workload" / "manifest.json").read_text(encoding="utf-8"))
ref = [s["description_chars"] for s in man["real_order"] + man.get("random_set", []) if "description_chars" in s]
f = {"reference_human_skills": {"n": len(ref), "mean_description_chars": round(statistics.mean(ref), 1), "median": statistics.median(ref)}}
arms = {}
for a in ARMS:
    g = [r for r in gen if r["arm"] == a]
    ok = [r for r in g if r.get("file_exists") and r.get("frontmatter_parses") and r.get("description_within_cap")]
    t = [r for r in trg if r["arm"] == a]
    pos = [r for r in t if r["polarity"] == "pos"]
    neg = [r for r in t if r["polarity"] == "neg"]
    per_skill = collections.defaultdict(int)
    for r in pos:
        per_skill[r["task"]] += r["hit"]
    arms[a] = {"skills": len(g), "load_and_parse_ok": len(ok), "name_matches_folder": sum(bool(r.get("name_matches_folder")) for r in g),
               "mean_description_chars": round(statistics.mean(r["description_chars"] for r in ok), 1) if ok else None,
               "mean_body_items": round(statistics.mean(r["body_items"] for r in ok), 1) if ok else None,
               "has_trigger_wording": sum(bool(r.get("description_has_trigger")) for r in ok), "has_steps": sum(bool(r.get("body_has_steps")) for r in ok),
               "extra_files": sum(len(r["skill_files"]) > 1 for r in g),
               "mean_output_tokens": round(statistics.mean(r["output_tokens"] for r in g if r.get("output_tokens")), 0) if g else None,
               "trigger_rows": len(t), "should_trigger_hits": f"{sum(r['hit'] for r in pos)} of {len(pos)}",
               "mean_hits_per_skill_of_4": round(sum(per_skill.values()) / max(1, len(per_skill)), 2) if per_skill else None,
               "false_triggers": f"{sum(r['hit'] or r['other_skill'] for r in neg)} of {len(neg)}"}
f["arms"] = arms
done = all(arms[a]["trigger_rows"] == 80 for a in ARMS)
f["complete"] = done
f["E1_plain_loads_9_of_10"] = arms["plain"]["load_and_parse_ok"] >= 9
f["E2_longer_than_human_reference"] = {a: arms[a]["mean_description_chars"] is not None and arms[a]["mean_description_chars"] > f["reference_human_skills"]["mean_description_chars"] for a in ("plain", "plugin-authoring", "skill-creator")}
if done:
    h = {a: arms[a]["mean_hits_per_skill_of_4"] for a in ARMS}
    f["E3_assisted_not_more_than_1_above_plain"] = {a: h[a] - h["plain"] <= 1 for a in ("plugin-authoring", "skill-creator")}
    f["E4_false_trigger_rate_le_10pct"] = {a: sum(r["hit"] or r["other_skill"] for r in trg if r["arm"] == a and r["polarity"] == "neg") / 40 <= 0.10 for a in ARMS}
(d / "skillwriting_findings.json").write_text(json.dumps(f, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(f, indent=1))
