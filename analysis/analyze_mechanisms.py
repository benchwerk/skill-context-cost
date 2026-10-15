#!/usr/bin/env python3
"""Delivery mechanisms for the same instruction text: idle and used cost, and the expected cost per session.

Usage: python analysis/analyze_mechanisms.py results/<mechanisms run>
Window total = input + cache_creation + cache_read. 'Added' = against M-base (empty session, prompt x). For the file
pointer the 'used' figure is the context at the LAST request (after the model has read the file); for every other
mechanism it is the first request. Expected cost per session at usage frequency p:
  skill       = idle + p * (used - idle)          idle = listed only; used = listed and invoked by hand
  CLAUDE.md   = used                              the text is loaded every session
  prompt      = p * used                          nothing loaded unless pasted
  file pointer= idle + p * (used - idle)          idle = the pointer line; used = pointer plus file read
Writes mechanism_findings.json."""
import json, sys
from pathlib import Path


def tot(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def main(run):
    run = Path(run)
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    vals = {}
    for r in rows:
        its = r.get("iterations") or []
        last = tot(its[-1]) if its else None
        first = tot(r["first_request_usage"]) if r.get("first_request_usage") else tot(r["usage"])
        vals.setdefault(r["config"], []).append({"first": first, "last": last or first, "turns": r.get("num_turns"),
                                                  "subtype": r.get("result_subtype")})
    base = {v["first"] for v in vals["M-base"]}
    assert len(base) == 1, f"baseline not constant: {base}"
    b = base.pop()

    def added(cfg, key="first"):
        xs = {v[key] for v in vals[cfg]}
        return {"added": min(xs) - b, "spread": max(xs) - min(xs), "runs": len(vals[cfg])}
    idle = {"skill": added("M-skill-idle")["added"], "claude_md": added("M-claudemd")["added"], "prompt": 0,
            "file_pointer": added("M-docs-idle")["added"]}
    used = {"skill": added("M-skill-used")["added"], "claude_md": added("M-claudemd")["added"],
            "prompt": added("M-prompt-used")["added"], "file_pointer": added("M-docs-used", "last")["added"]}
    curves = {}
    for p in (0, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0):
        curves[str(p)] = {"skill": idle["skill"] + p * (used["skill"] - idle["skill"]), "claude_md": used["claude_md"],
                          "prompt": p * used["prompt"], "file_pointer": idle["file_pointer"] + p * (used["file_pointer"] - idle["file_pointer"])}
    cross = {}
    if used["skill"] != idle["skill"]:
        # skill vs file pointer and skill vs pasted prompt: p where expected costs are equal
        a1, b1 = idle["skill"], used["skill"] - idle["skill"]
        a2, b2 = idle["file_pointer"], used["file_pointer"] - idle["file_pointer"]
        cross["skill_vs_file_pointer_p"] = (a2 - a1) / (b1 - b2) if b1 != b2 else None
    docs_read = [v["turns"] for v in vals["M-docs-used"]]
    res = {"base_window_total": b, "idle_added": idle, "used_added": used,
           "file_was_read_in_runs": sum(1 for v in vals["M-docs-used"] if v["last"] > v["first"]), "file_runs": len(vals["M-docs-used"]),
           "expected_added_tokens_per_session": curves, "crossings": cross,
           "note": "window tokens, first-request cache effects ignored; the pasted prompt and the file read also cost the person/extra turn"}
    (run / "mechanism_findings.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("base_window_total", "idle_added", "used_added", "file_was_read_in_runs")}, indent=1))
    for p, c in curves.items():
        print(p, {k: round(v) for k, v in c.items()})
    print(cross)


if __name__ == "__main__":
    main(sys.argv[1])
