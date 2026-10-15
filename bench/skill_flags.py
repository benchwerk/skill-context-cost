#!/usr/bin/env python3
"""Record two frontmatter flags of every real skill in the manifest, from the local clones, into analysis/skill_flags.json:
  user_invocable_false          the skill is not a slash command, so Claude Code does not list it in the start-up
                                skills it reports (it is still offered to the model)
  disable_model_invocation      the skill is manual-only: not offered to the model, so it costs no listing tokens
Added after the first full run, when 'shadcn' (user-invocable: false) looked missing and three popular skills added
zero tokens. The raw run data is unchanged; the flags are read from the same pinned clones.
Usage: python bench/skill_flags.py"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skilltx import frontmatter

ROOT = Path(__file__).resolve().parent.parent
man = json.loads((ROOT / "workload" / "manifest.json").read_text(encoding="utf-8"))
out = {}
for s in man["real_order"] + man.get("random_set", []):
    p = ROOT / "workload" / "src" / s["source"].replace("/", "__") / s["path"]
    fm = frontmatter(p.read_text(encoding="utf-8-sig", errors="replace"))
    out[s["name"]] = {"user_invocable_false": fm.get("user-invocable", "").lower() == "false",
                      "disable_model_invocation": fm.get("disable-model-invocation", "").lower() == "true",
                      "sha256": s["sha256"]}
(ROOT / "analysis" / "skill_flags.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(out), "skills;", sum(v["user_invocable_false"] for v in out.values()), "not user-invocable;",
      sum(v["disable_model_invocation"] for v in out.values()), "manual-only")
