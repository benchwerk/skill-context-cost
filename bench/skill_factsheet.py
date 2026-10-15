#!/usr/bin/env python3
"""Fact sheet of one skill for the review standard (skill_review_standard.md), from the study's own data only.

Usage: python bench/skill_factsheet.py <skill name>
Reads analysis/skill_features.json, analysis/skill_labels.json (if present), workload/manifest.json, the frozen popularity
snapshot, and the findings of the main and invocation runs. Every cost figure is marked measured or estimate."""
import glob, json, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def latest(pattern):
    c = sorted(glob.glob(str(ROOT / pattern)))
    return Path(c[-1]) if c else None


def pct(v, allv):
    return round(100 * sum(1 for x in allv if x <= v) / len(allv))


def main(name):
    feats = load(ROOT / "analysis" / "skill_features.json")
    f = next((x for x in feats if x["name"] == name), None)
    if not f:
        sys.exit(f"{name} is not among the {len(feats)} skills studied")
    labels = {}
    if (ROOT / "analysis" / "skill_labels.json").exists():
        labels = {x["name"]: x for x in load(ROOT / "analysis" / "skill_labels.json")}
    snap = {(r["source"], r["skill"]): r for r in load(ROOT / "workload" / "popularity_snapshot.json")["rows"]}
    s = next((v for k, v in snap.items() if k[0] == f["source"] and (k[1] == name or v["name"] == name)), None)
    main_run = latest("results/*_skills")
    inv_run = latest("results/*_invocation")
    mf = load(main_run / "findings.json") if main_run else {}
    fit = (mf.get("comparisons", {}) or {}).get("fit", {})
    inv = load(inv_run / "invocation_findings.json") if inv_run and (inv_run / "invocation_findings.json").exists() else None
    meas = next((r for r in (inv["skills"] if inv else []) if r["skill"] == name), None)
    b_char = 0.37
    est_listing = None if f["manual_only"] else round(fit.get("per_skill_constant_tokens", 0) + fit.get("tokens_per_listing_char", 0) * f["listing_chars"])
    est_inv = round(b_char * f["body_chars"] + 50)
    lab = labels.get(name)
    allb = [x["body_chars"] for x in feats]
    alll = [x["listing_chars"] for x in feats if not x["manual_only"]]
    print(f"# Fact sheet: {name}\n")
    print(f"- Source: {f['source']} | popularity-list position {f['popular_rank']} (leaderboard values withheld)")
    if s and s.get("weekly"):
        print(f"- Last eight weekly installs: {s['weekly']}")
    if lab:
        print(f"- Type: domain {lab['domain']}, form {lab['form']}, trigger clarity {lab['clarity']}; purpose: {lab['purpose']}")
    print(f"- Shape: {'folder with ' + str(f['folder_files']) + ' other file(s) (' + str(f['folder_bytes_other']) + ' bytes), extensions ' + json.dumps(f['folder_extensions']) if f['folder_files'] else 'single SKILL.md'}"
          f"; scripts {f['has_scripts']}; references dir {f['has_references_dir']}; manual-only {f['manual_only']}; hidden {f['hidden']}; user-invocable false {f['user_invocable_false']}")
    print("\n## Cost")
    if f["manual_only"]:
        print("- Listing: 0 tokens (manual-only: not offered to the model)")
    else:
        print(f"- Listing: {'MEASURED ' + str(meas['listing_tokens']) if meas else 'ESTIMATE ' + str(est_listing)} tokens per session (listing text {f['listing_chars']} chars, {pct(f['listing_chars'], alll)}th percentile of {len(alll)} automatic skills)")
    print(f"- Invocation: {'MEASURED ' + str(meas['invocation_tokens']) if meas else 'ESTIMATE ' + str(est_inv)} tokens (body {f['body_chars']} chars, {pct(f['body_chars'], allb)}th percentile of {len(allb)} skills)")
    if meas and meas.get("invocations_to_equal_listing_per_session"):
        print(f"- One invocation equals the listing cost of {meas['invocations_to_equal_listing_per_session']:.0f} sessions")
    print(f"- Deferred: {f['referenced_files_in_body']} file(s) the body points to, {f['deferred_bytes']} bytes, {f['deferred_share']:.0%} of the material is loaded only on demand")
    print("\n## Anatomy")
    print(f"- Description: {f['description_chars']} chars; trigger phrase {f['description_has_trigger_phrase']}; negative scope {f['description_has_negative_scope']}; sentences {f['description_sentences']}; non-ASCII/CJK {f['cjk_chars_in_description']}")
    print(f"- Body: {f['body_lines']} lines, {f['headings']} headings ({f['h2_plus']} below top level), {f['code_blocks']} code blocks, {f['table_rows']} table rows, {f['bullets']} bullets, {f['numbered_steps']} numbered steps, {f['forceful_words']} forceful words, {f['examples_mentions']} mentions of 'example', {f['urls_in_body']} URLs, {f['install_commands']} install commands")
    print(f"- Frontmatter keys: {', '.join(f['frontmatter_keys'])}; allowed-tools: {f['allowed_tools'] or '(none)'}")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]))
