"""Part 14E: skills written by Claude (Sonnet) with three kinds of help, then checked by script and by a trigger test.

Arms: plain (a plain request), plugin-authoring (the bundled skill), skill-creator (Anthropic's published skill, from the local clone of
anthropics/skills, installed in the working directory). Phase 1 generates the 30 skills; phase 2 checks the files; phase 3 runs the trigger
prompts (4 should-trigger, 4 should-not per skill) with the generated skill installed alone.
  CLAUDE_CONFIG_DIR=<isolated dir> CLAUDE_BIN=<pinned exe> python bench/skillwriting_run.py [--stop-at 0.90]   (resumes by itself)
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run
import trigger_test as tt
from skilltx import frontmatter

ROOT = run.ROOT
TASKS = json.loads((ROOT / "bench" / "skillwriting_tasks.json").read_text(encoding="utf-8"))["tasks"]
ARMS = ["plain", "plugin-authoring", "skill-creator"]
MODEL = "claude-sonnet-5-5[1m]"
SC_SRC = run.SRC / "anthropics__skills" / "skills" / "skill-creator"
SUFFIX = ("Save it as out/{slug}/SKILL.md in the current directory (the folder out/ already exists; later it is installed as a skill). Do not ask questions, do not run tests, evals or benchmarks, "
          "and write only the skill folder.")


def prompt_for(arm, t):
    text = f"Create a Claude Code skill. Purpose: {t['brief']} " + SUFFIX.format(slug=t["slug"])
    return text if arm == "plain" else f"/{arm} {text}"


def build_gen(arm):
    wd = run.build_workdir("C0")
    (wd / "out").mkdir()
    if arm == "skill-creator":
        shutil.copytree(SC_SRC, wd / ".claude" / "skills" / "skill-creator")
    return wd


def check_file(path, slug):
    out = {"file_exists": path.exists()}
    if not path.exists():
        return out
    raw = path.read_text(encoding="utf-8-sig")
    m = run.FM.match(raw)
    fm = frontmatter(raw) if m else {}
    body = raw[m.end():] if m else raw
    desc = fm.get("description", "") or ""
    out.update({"frontmatter_parses": bool(m and fm), "name": fm.get("name"), "name_matches_folder": fm.get("name") == slug,
                "description_chars": len(desc), "description_within_cap": 0 < len(desc) <= 1536, "body_chars": len(body),
                "body_items": len(re.findall(r"^\s*(?:\d+[.)]|[-*])\s+\S", body, re.M)),
                "description_has_trigger": bool(re.search(r"\b(use when|when the user|when you|whenever|use this)\b", desc, re.I)),
                "disable_model_invocation": str(fm.get("disable-model-invocation", "")).lower() == "true"})
    out["body_has_steps"] = out["body_items"] >= 3
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stop-at", type=float, default=0.90)
    ap.add_argument("--phase", default="1,3")
    a = ap.parse_args()
    exe = run.find_claude()
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    env["CLAUDE_CONFIG_DIR"] = os.environ["CLAUDE_CONFIG_DIR"]
    out = ROOT / "results" / "2026-10-08_x86-laptop_skillwriting"
    (out / "skills").mkdir(parents=True, exist_ok=True)
    gen_f, trg_f = out / "generation.jsonl", out / "triggers.jsonl"
    load = lambda f: [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []
    gdone = {(r["arm"], r["task"]) for r in load(gen_f)}
    tdone = {(r["arm"], r["task"], r["prompt_id"]) for r in load(trg_f) if r.get("decision") not in (None, "timeout")}   # "none" = no skill call in three turns (the model used other tools): a non-trigger, not a failure

    def meter(rl):
        if rl and ((rl.get("five_hour") or 0) >= a.stop_at or rl.get("status") not in (None, "allowed", "allowed_warning")):
            print(f"STOP: five-hour meter {rl.get('five_hour')} status {rl.get('status')} resets {rl.get('five_hour_resets_local')}; run again then")
            sys.exit(3)

    if "1" in a.phase:
        for t in TASKS:
            for arm in ARMS:
                if (arm, t["id"]) in gdone:
                    continue
                wd = build_gen(arm)
                cmd = [exe, "-p", prompt_for(arm, t), "--output-format", "stream-json", "--verbose", "--max-turns", "25", "--model", MODEL,
                       "--permission-mode", "acceptEdits", *run.CFG["claude_extra_args"]]
                cp = subprocess.run(cmd, cwd=wd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                init, first, result = run.parse_events(cp.stdout)
                rl = run.rate_limit(cp.stdout)
                u = (result or {}).get("usage") or {}
                dest = out / "skills" / arm / t["slug"]
                src = wd / "out" / t["slug"]
                if dest.exists():
                    run.rm_tree(dest)
                if src.exists():
                    shutil.copytree(src, dest)
                row = {"arm": arm, "task": t["id"], "status": (result or {}).get("subtype"), "turns": (result or {}).get("num_turns"),
                       "output_tokens": u.get("output_tokens"), "input_tokens": u.get("input_tokens"), "cache_creation": u.get("cache_creation_input_tokens"),
                       "cache_read": u.get("cache_read_input_tokens"), "tools": [c["tool"] for c in run.TOOL_CALLS], "rate_limit": rl,
                       "skill_files": sorted(str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()) if dest.exists() else []}
                row.update(check_file(dest / "SKILL.md", t["slug"]))
                with gen_f.open("a", encoding="utf-8", newline="\n") as f:
                    f.write(run.scrub(json.dumps(row)) + "\n")
                print("gen", arm, t["id"], row["status"], row["turns"], row.get("description_chars"), row.get("body_items"), rl and rl.get("five_hour"), flush=True)
                meter(rl)
    if "3" in a.phase:
        for t in TASKS:
            for arm in ARMS:
                skill_dir = out / "skills" / arm / t["slug"]
                if not (skill_dir / "SKILL.md").exists():
                    continue
                name = frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8-sig")).get("name") or t["slug"]
                for pol in ("pos", "neg"):
                    for i, pr in enumerate(t[pol], 1):
                        pid = f"{pol}{i}"
                        if (arm, t["id"], pid) in tdone:
                            continue
                        wd = Path(run.CFG["workdir_root"]) / "w"
                        if wd.exists():
                            run.rm_tree(wd)
                        shutil.copytree(skill_dir, wd / ".claude" / "skills" / name)
                        decision, rl, secs, others, first_text, usage1 = tt.first_move(exe, env, wd, pr, MODEL, name)
                        row = {"arm": arm, "task": t["id"], "prompt_id": pid, "polarity": pol, "decision": decision, "skill_name": name,
                               "hit": decision == "skill:" + name, "other_skill": decision.startswith("skill:") and decision != "skill:" + name,
                               "seconds": secs, "rate_limit": rl, "first_request_usage": usage1}
                        with trg_f.open("a", encoding="utf-8", newline="\n") as f:
                            f.write(run.scrub(json.dumps(row)) + "\n")
                        print("trg", arm, t["id"], pid, decision, rl and rl.get("five_hour"), flush=True)
                        if decision == "timeout":
                            print("STOP: no decision; not spending more")
                            sys.exit(3)
                        meter(rl)


if __name__ == "__main__":
    main()
