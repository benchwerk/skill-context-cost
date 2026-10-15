#!/usr/bin/env python3
"""Mechanical anatomy of every real skill in the manifest: structure, description style, bundled files, deferred material.

Usage: python bench/skill_anatomy.py        -> analysis/skill_features.json
Reads the pinned local clones only (no network, no model). Features are counted, never judged; judgement (the type of a
skill) is labelled separately against a written rubric (analysis/taxonomy.md)."""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skilltx import FM, frontmatter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workload" / "src"
MAN = json.loads((ROOT / "workload" / "manifest.json").read_text(encoding="utf-8"))

TRIGGER = re.compile(r"\b(use (this skill )?(when|for|to)|when (the user|you|working|asked)|triggers? (on|when)|activate|invoke when|apply (this )?when)\b", re.I)
NEGATIVE = re.compile(r"\b(do not use|don't use|not for|not intended|instead of|skip (this )?when)\b", re.I)
FORCE = re.compile(r"\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|REQUIRED|DO NOT)\b")
INSTALL = re.compile(r"\b(npm (i|install)|npx |pip install|pipx |brew install|cargo install|go install|curl [^\n]*\|\s*(ba)?sh|uv (add|tool))\b")
URL = re.compile(r"https?://[^\s)>\]]+")
REL = re.compile(r"\]\(((?!https?:|#|mailto:)[^)\s#]+)")
BARE = re.compile(r"`((?:[\w.-]+/)*[\w.-]+\.(?:md|txt|json|ya?ml|py|sh|js|ts|html|csv))`")
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")


def features(entry, popular_rank):
    base = SRC / entry["source"].replace("/", "__")
    path = base / entry["path"]
    folder = path.parent
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    fm = frontmatter(text)
    m = FM.match(text)
    body = text[m.end():] if m else text
    desc = fm.get("description", "")
    when = fm.get("when_to_use", "")
    root_level = folder == base
    files = [] if root_level else [p for p in folder.rglob("*") if p.is_file() and ".git" not in p.relative_to(folder).parts]
    sizes = {p.relative_to(folder).as_posix(): p.stat().st_size for p in files}
    others = {k: v for k, v in sizes.items() if k != "SKILL.md"}
    exts = {}
    for k in others:
        e = Path(k).suffix.lower() or "(none)"
        exts[e] = exts.get(e, 0) + 1
    # material the body points to and that exists in the folder (the model can read it later, only if needed)
    refs = set()
    for r in REL.findall(body) + BARE.findall(body):
        rp = (folder / r).resolve() if not r.startswith("/") else None
        if rp and rp.is_file() and folder.resolve() in rp.parents:
            refs.add(rp.relative_to(folder.resolve()).as_posix())
    deferred = sum(sizes.get(r, 0) for r in refs)
    lines = body.splitlines()
    head = [l for l in lines if re.match(r"^#{1,6}\s", l)]
    fences = len(re.findall(r"^\s*```", body, re.M)) // 2
    f = {
        "name": entry["name"], "source": entry["source"], "popular_rank": popular_rank, "leaderboard_rank": entry["rank"],
        "installs": entry["installs"],
        "listing_chars": entry["listing_chars"], "description_chars": len(desc), "when_to_use_chars": len(when),
        "description_has_trigger_phrase": bool(TRIGGER.search(desc + " " + when)),
        "description_has_negative_scope": bool(NEGATIVE.search(desc + " " + when)),
        "description_sentences": len(re.findall(r"[.!?](\s|$)", desc)),
        "frontmatter_keys": sorted(fm), "manual_only": fm.get("disable-model-invocation", "").lower() == "true",
        "user_invocable_false": fm.get("user-invocable", "").lower() == "false", "hidden": fm.get("hidden", "").lower() == "true",
        "allowed_tools": fm.get("allowed-tools", ""), "has_license_key": "license" in fm,
        "body_chars": len(body), "body_lines": len(lines), "headings": len(head), "h2_plus": len([h for h in head if not h.startswith("# ")]),
        "code_blocks": fences, "table_rows": len([l for l in lines if l.strip().startswith("|")]),
        "bullets": len([l for l in lines if re.match(r"^\s*[-*]\s", l)]),
        "numbered_steps": len([l for l in lines if re.match(r"^\s*\d+[.)]\s", l)]),
        "forceful_words": len(FORCE.findall(body)), "examples_mentions": len(re.findall(r"\bexample", body, re.I)),
        "urls_in_body": len(URL.findall(body)), "install_commands": len(INSTALL.findall(body)),
        "folder_files": len(others), "folder_bytes_other": sum(others.values()), "folder_extensions": exts,
        "has_scripts": any(e in exts for e in (".py", ".sh", ".js", ".ts", ".mjs")), "has_references_dir": any(k.startswith(("references/", "reference/", "docs/")) for k in others),
        "has_assets": any(k.startswith(("assets/", "templates/")) for k in others),
        "referenced_files_in_body": len(refs), "deferred_bytes": deferred,
        "deferred_share": round(deferred / (deferred + len(body.encode("utf-8"))), 3) if (deferred + len(body)) else 0,
        "non_ascii_share": entry.get("non_ascii_share"), "cjk_chars_in_description": len(CJK.findall(desc)),
        "skill_at_repo_root": root_level,
        "first_heading": head[0].lstrip("# ").strip()[:80] if head else "",
    }
    return f


def main():
    out = []
    for i, e in enumerate(MAN["real_order"]):
        out.append({**features(e, i + 1), "set": "popular"})
    names = {e["name"] for e in MAN["real_order"]}
    for e in MAN["random_set"]:
        if e["name"] not in names:
            out.append({**features(e, None), "set": "random"})
    (ROOT / "analysis" / "skill_features.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(out), "skills ->", ROOT / "analysis" / "skill_features.json")


if __name__ == "__main__":
    main()
