#!/usr/bin/env python3
"""Resolve the selected skills to files and write workload/manifest.json (the sets measured, chosen before any run).

Input: workload/selection.json (rule applied to the frozen popularity snapshot) and the clones in workload/src/.
For every candidate, in rank order, the skill's SKILL.md is looked up in its repository (parent folder name or
frontmatter name equals the skill id). A candidate that cannot be found, has no name or description, or repeats a
skill name already used is skipped and recorded in `skipped` (the next candidate takes its place).
Sets: C1, C10, C50, C100 are prefixes of the main list; T1..T5 the first five alone; R50 a seeded random sample
(comparison); synthetic sets for the length sweep (S10-L<chars>), the body check (S10-B<chars>) and the fixed-overhead
probe (F1); C50-disable / C50-trim100 are variants of C50.
Usage: python bench/build_workload.py"""
import hashlib, json
from pathlib import Path

from skilltx import FM, frontmatter, listing_chars

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench" / "config.json").read_text(encoding="utf-8"))
SRC = ROOT / "workload" / "src"
OUT = ROOT / "workload"
BODY_HEAVY = "Synthetic placeholder, never invoked. " + ("Filler text for a long skill body. " * 600)  # same string as in run.py


def sha(b):
    return hashlib.sha256(b).hexdigest()


def find_skill(source, skill_id):
    base = SRC / source.replace("/", "__")
    if not base.exists():
        return None, "repository not fetched"
    cands = []
    for p in base.rglob("SKILL.md"):
        if ".git" in p.relative_to(base).parts:
            continue
        fm = frontmatter(p.read_text(encoding="utf-8-sig", errors="replace"))
        if p.parent.name == skill_id or fm.get("name") == skill_id:
            cands.append(p)
    if not cands:
        return None, "SKILL.md not found"
    cands.sort(key=lambda p: (len(p.parts), str(p)))
    return cands[0], None


def resolve(candidates, rec, skipped, used, limit):
    """used: dict skill name -> (source, path) already taken; the same (source, path) may be taken again."""
    out = []
    for r in candidates:
        if len(out) >= limit:
            break
        commit = rec.get(r["source"], {}).get("commit")
        p, why = find_skill(r["source"], r["skill"]) if commit else (None, "repository not fetched")
        if p is None:
            skipped.append({"rank": r["rank"], "source": r["source"], "skill": r["skill"], "why": why})
            continue
        data = p.read_bytes()
        text = data.decode("utf-8-sig", "replace")
        fm = frontmatter(text)
        name, desc = fm.get("name"), fm.get("description")
        if not name or not desc:
            skipped.append({"rank": r["rank"], "source": r["source"], "skill": r["skill"], "why": "no name or description"})
            continue
        base = SRC / r["source"].replace("/", "__")
        rel = str(p.relative_to(base)).replace("\\", "/")
        if name in used and used[name] != (r["source"], rel):
            skipped.append({"rank": r["rank"], "source": r["source"], "skill": r["skill"], "why": "skill name already used by another file"})
            continue
        if name in {o["name"] for o in out}:
            skipped.append({"rank": r["rank"], "source": r["source"], "skill": r["skill"], "why": "skill name already used"})
            continue
        used.setdefault(name, (r["source"], rel))
        out.append({"rank": r["rank"], "source": r["source"], "commit": commit, "path": rel, "name": name,
                    "installs": r["installs"], "sha256": sha(data), "listing_chars": listing_chars(fm),
                    "description_chars": len(desc), "name_chars": len(name),
                    "body_chars": len(text) - len(FM.match(text).group(0)) if FM.match(text) else len(text),
                    "non_ascii_share": round(sum(1 for ch in (name + desc) if ord(ch) > 127) / len(name + desc), 3)})
    return out


def synthetic(i, length, tag):
    topics = ["invoices", "calendars", "release notes", "log files", "spreadsheets", "meeting notes", "test plans",
              "icons", "changelogs", "contracts"]
    d = f"Use when the user asks to work with {topics[i % len(topics)]} (synthetic skill {tag}{i:03d}). "
    filler = "Covers creating, reviewing and summarising the files, with checks and a short report. "
    while len(d) < length:
        d += filler
    return d[:length].rstrip()


def synth_set(prefix, length, n, body=None):
    skills = []
    for i in range(n):
        name = f"synthetic-{prefix}{length}-{i:03d}"
        desc = synthetic(i, length, prefix)
        text = f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\n{body or 'Synthetic placeholder, never invoked.'}\n"
        e = {"name": name, "description": desc, "sha256": sha(text.encode()), "listing_chars": len(desc),
             "description_chars": len(desc), "name_chars": len(name), "synthetic": True}
        if body:
            e["body_chars"] = len(body)
        skills.append(e)
    return skills


def main():
    sel = json.loads((OUT / "selection.json").read_text(encoding="utf-8"))
    rec = json.loads((OUT / "fetched.json").read_text(encoding="utf-8"))
    skipped, used = [], {}
    need = max(CFG["real_ns"])
    order = resolve(sel["main_candidates"], rec, skipped, used, need)
    if len(order) < need:
        raise SystemExit(f"only {len(order)} resolvable popular skills, need {need}")
    main_names = {s["name"]: (s["source"], s["path"]) for s in order}
    random_set = resolve(sel["random_candidates"], rec, skipped, dict(main_names), CFG["selection"]["random_n"])
    sets = {"C0": [], **{f"C{n}": [s["name"] for s in order[:n]] for n in CFG["real_ns"]}}
    sets["R50"] = [s["name"] for s in random_set]
    synth, n = {}, CFG["sweep_n"]
    for length in CFG["sweep_lengths_chars"]:
        synth[f"S{n}-L{length}"] = synth_set("L", length, n)
    bl = CFG["body_check_length"]
    synth[f"S{n}-B{bl}"] = synth_set("B", bl, n, BODY_HEAVY)
    synth["F1"] = synth_set("F", 30, 1)
    for k, v in synth.items():
        sets[k] = [s["name"] for s in v]
    variants = {}
    for cid, tx in CFG["improvement_variants"].items():
        sets[cid] = list(sets["C50"])
        variants[cid] = tx
    for k in range(1, CFG["individual_k"] + 1):
        sets[f"T{k}"] = [order[k - 1]["name"]]
    prompts = {}
    for k in range(1, CFG.get("invocation_k", 0) + 1):
        sets[f"I{k}"] = [order[k - 1]["name"]]          # the skill alone, invoked by hand
        prompts[f"I{k}"] = "/" + order[k - 1]["name"]
        sets[f"L{k}"] = [order[k - 1]["name"]]          # the same skill, listed only (prompt x)
    # mechanisms: the same instruction text (the body of one skill) delivered five ways
    src_name = CFG["mechanism_source_skill"]
    src = next(s for s in order if s["name"] == src_name)
    raw_text = (SRC / src["source"].replace("/", "__") / src["path"]).read_text(encoding="utf-8-sig")
    mfm = FM.match(raw_text)
    instruction = raw_text[mfm.end():].strip() if mfm else raw_text.strip()
    task = "Now build a login button."
    mech = {"source_skill": src_name, "source": src["source"], "source_path": src["path"], "source_commit": src["commit"],
            "instruction_chars": len(instruction), "instruction_sha256": sha(instruction.encode("utf-8")), "task": task,
            "pointer": "Detailed UI rules are in docs/ui-rules.md. Read that file before any UI work.",
            "configs": {
                "M-base": {},
                "M-skill-idle": {"skills": [src_name]},
                "M-skill-used": {"skills": [src_name]},
                "M-claudemd": {"claude_md": "instruction"},
                "M-prompt-used": {},
                "M-docs-idle": {"claude_md": "pointer", "docs": "instruction"},
                "M-docs-used": {"claude_md": "pointer", "docs": "instruction", "max_turns": 3}}}
    for cid, spec in mech["configs"].items():
        sets[cid] = list(spec.get("skills", []))
    prompts["M-skill-used"] = "/" + src_name
    prompts["M-prompt-used"] = "__INSTRUCTION__\n\n" + task
    prompts["M-docs-used"] = "Read docs/ui-rules.md and then say only: ok."
    max_turns = {"M-docs-used": 3}
    for xid, xs in CFG.get("restructure_experiments", {}).items():
        sk = next(s for s in order if s["name"] == xs["skill"])
        for suffix in ("orig", "split", "split-read"):
            sets[f"{xid}-{suffix}"] = [sk["name"]]
        prompts[f"{xid}-orig"] = prompts[f"{xid}-split"] = "/" + sk["name"]
        prompts[f"{xid}-split-read"] = "/" + sk["name"] + " " + xs["read_prompt"]
        max_turns[f"{xid}-split-read"] = 3
        variants[f"{xid}-split"] = variants[f"{xid}-split-read"] = {"transform": "split_sections", "core_chars": xs["core_chars"]}
    ax = CFG.get("alias_experiment")
    extra_skills = []
    if ax:
        found = {}
        for role in ("alias", "target"):
            p_, why = find_skill(ax["source"], ax[role])
            if p_ is None:
                raise SystemExit(f"alias experiment: {role} {ax[role]} not found: {why}")
            base_ = SRC / ax["source"].replace("/", "__")
            data_ = p_.read_bytes()
            fm_ = frontmatter(data_.decode("utf-8-sig", "replace"))
            found[role] = {"source": ax["source"], "commit": rec[ax["source"]]["commit"], "path": str(p_.relative_to(base_)).replace("\\", "/"),
                           "name": fm_["name"], "sha256": sha(data_)}
            extra_skills.append(found[role])
        a_, t_ = found["alias"]["name"], found["target"]["name"]
        topic = ax["topic"]
        sets["G-original"] = [a_, t_]
        sets["G-slash"] = [a_, t_]
        sets["G-prose"] = [a_, t_]
        sets["G-inline"] = [a_]
        sets["G-direct"] = [t_]
        for k in ("G-original", "G-slash", "G-prose", "G-inline"):
            prompts[k] = "/" + a_ + " " + topic
        prompts["G-direct"] = "/" + t_ + " " + topic
        for k in sets:
            if k.startswith("G-"):
                max_turns[k] = 3
        variants["G-slash"] = {"transform": "replace_body", "only": a_, "body": ax["variants"]["slash"]}
        variants["G-prose"] = {"transform": "replace_body", "only": a_, "body": ax["variants"]["prose"]}
        variants["G-inline"] = {"transform": "replace_body", "only": a_, "body_from_skill": t_}
        crowd = [s["name"] for s in order if s["name"] not in (a_, t_)][:ax.get("crowd_others", 0)]
        if crowd:   # the alias test among many installed skills (G2-*); the same body variants as in the empty session
            for k, base_ in (("G2-original", None), ("G2-slash", "G-slash"), ("G2-prose", "G-prose")):
                sets[k] = [a_, t_] + crowd
                prompts[k] = prompts["G-original"]
                max_turns[k] = 3
                if base_:
                    variants[k] = variants[base_]
    manifest = {"seed": CFG["seed"], "snapshot_raw_page_sha256": sel["snapshot_raw_page_sha256"], "real_order": order,
                "random_set": random_set, "sets": sets, "synthetic": synth, "variants": variants, "prompts": prompts, "max_turns": max_turns, "extra_skills": extra_skills, "mechanisms": mech, "skipped": skipped}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"manifest: {len(order)} popular + {len(random_set)} random skills resolved, {len(skipped)} skipped; sets: {', '.join(sets)}")


if __name__ == "__main__":
    main()
