#!/usr/bin/env python3
"""Output-quality test for one skill (design-taste-frontend): none, original, split, placebo.

Each generation starts `claude -p "/design-taste-frontend <brief>"` (or the bare brief for `none`) in a fresh working directory
holding the condition's skill, lets the model finish (up to 8 turns, so a split skill can read its reference files), saves the
reply, extracts the HTML and runs the mechanical checks from quality_checks.py. Conditions:
  none      no skill installed, the bare brief
  original  the skill as published
  split     the same text cut into a 13 KB core and 15 reference files with an index (the X1 edit)
  placebo   the skill's own name and description over a body of unrelated skills (backend, cloud, tooling), cut to the same length
Usage: python bench/quality_run.py [--samples 3] [--max-calls N] [--stop-at 0.80] [--resume <folder>] [--experiment quality]
Needs CLAUDE_CONFIG_DIR. Writes results/<date>_<machine>_<experiment>/{env.json,plan.json,raw.jsonl,outputs/}."""
import argparse, datetime, hashlib, json, os, random, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run
from quality_checks import run_checks
from skilltx import FM, frontmatter, split_sections

ROOT, CFG, MAN = run.ROOT, run.CFG, run.MAN
SKILL = "design-taste-frontend"
TASKS = json.loads((ROOT / "bench" / "quality_tasks.json").read_text(encoding="utf-8"))
PLACEBO_SOURCES = ["microsoft-foundry", "neon", "google-agents-cli-deploy", "azure-diagnostics", "subagent-driven-development",
                   "skill-creator", "anti-detect-browser", "hyperframes-cli"]
CONDS = ["none", "original", "split", "placebo"]


def skill_path():
    s = next(x for x in MAN["real_order"] if x["name"] == SKILL)
    return run.SRC / s["source"].replace("/", "__") / s["path"]


def placebo_body(target_len):
    parts = []
    for n in PLACEBO_SOURCES:
        src, _ = run.skill_dir_for(n)
        raw = (src / "SKILL.md").read_text(encoding="utf-8-sig")
        m = FM.match(raw)
        parts.append((n, (raw[m.end():] if m else raw).strip()))
    text = "\n\n".join(b for _, b in parts)
    return text[:target_len], [(n, hashlib.sha256(b.encode()).hexdigest()[:12]) for n, b in parts]


def pasted_text():
    """the body the slash command would deliver (the skill file without its frontmatter), for the `pasted` condition"""
    raw = skill_path().read_text(encoding="utf-8-sig")
    m = FM.match(raw)
    return (raw[m.end():] if m else raw).strip()


def build(cond):
    wd = Path(CFG["workdir_root"]) / "w"
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    (wd / ".claude" / "skills").mkdir(parents=True)
    if cond in ("none", "pasted"):   # pasted: no skill installed, its body goes into the prompt (see pasted_text)
        return wd
    d = wd / ".claude" / "skills" / SKILL
    d.mkdir()
    text = skill_path().read_text(encoding="utf-8-sig")
    if cond == "original":
        (d / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
    elif cond == "split":
        new, files = split_sections(text, 12000)
        (d / "SKILL.md").write_text(new, encoding="utf-8", newline="\n")
        for rel, content in files.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(content, encoding="utf-8", newline="\n")
    elif cond == "placebo":
        m = FM.match(text)
        body, _ = placebo_body(len(text) - len(m.group(0)))
        (d / "SKILL.md").write_text(m.group(0) + "\n" + body + "\n", encoding="utf-8", newline="\n")
    return wd


def generate(claude, env, wd, prompt, model):
    long_prompt = len(prompt) > 20000   # a Windows command line holds about 32,000 characters: the pasted skill goes in on stdin
    cp = subprocess.run([claude, "-p", *([] if long_prompt else [prompt]), "--output-format", "stream-json", "--verbose", "--max-turns", "8", "--model", model, *CFG["claude_extra_args"]],
                        cwd=wd, env=env, input=prompt if long_prompt else None, stdin=None if long_prompt else subprocess.DEVNULL,
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    o = {"reply": "", "tools": [], "turns": None, "usage": None, "rl": None, "subtype": None}
    for l in cp.stdout.splitlines():
        if not l.startswith("{"):
            continue
        e = json.loads(l)
        t = e.get("type")
        if t == "assistant":
            for c in (e.get("message") or {}).get("content", []) or []:
                if c.get("type") == "tool_use":
                    o["tools"].append({"tool": c.get("name"), "input": json.dumps(c.get("input"))[:110]})
        elif t == "rate_limit_event" and o["rl"] is None:
            o["rl"] = run.rate_limit(l)
        elif t == "result":
            o["reply"] = e.get("result") or ""
            o["turns"], o["subtype"], o["usage"] = e.get("num_turns"), e.get("subtype"), e.get("usage")
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--stop-at", type=float, default=0.80)
    ap.add_argument("--resume")
    ap.add_argument("--experiment", default="quality")
    ap.add_argument("--conds", default=",".join(CONDS))
    a = ap.parse_args()
    run.refuse_placeholders()
    claude, model = run.find_claude(), CFG["models"][0]
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    plan = [{"cond": c, "task": t["id"], "sample": s, "brief": t["text"]} for c in a.conds.split(",") for t in TASKS["tasks"] for s in range(1, a.samples + 1)]
    random.Random(CFG["seed"]).shuffle(plan)
    for i, p in enumerate(plan):
        p["seq"] = i + 1
    Path(CFG["workdir_root"]).mkdir(parents=True, exist_ok=True)
    version = subprocess.run([claude, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    done = set()
    if a.resume:
        out = ROOT / "results" / a.resume
        old = json.loads((out / "env.json").read_text(encoding="utf-8"))
        if old["claude_version"] != version:
            sys.exit(f"cannot resume: Claude Code is {version}, the run started on {old['claude_version']}")
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
        txt = (out / "raw.jsonl").read_text(encoding="utf-8")
        # a row with zero output tokens is an infrastructure failure (network, login), not a page: it stays in raw.jsonl and its cell is run again
        done = {json.loads(l)["seq"] for l in txt.splitlines() if l.strip() and json.loads(l).get("finished") and (json.loads(l).get("output_tokens") or 0) > 0}
    else:
        out = ROOT / "results" / f"{datetime.date.today().isoformat()}_{CFG['machine']}_{a.experiment}"
        if out.exists():
            sys.exit(f"{out} exists: use --resume or another --experiment name")
        (out / "outputs").mkdir(parents=True)
        _, comp = placebo_body(10)
        env_info = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "claude_version": version, "model": model,
                    "model_window": CFG["model_windows"][model], "skill": SKILL, "conditions": a.conds.split(","), "samples": a.samples, "seed": CFG["seed"],
                    "tasks_sha256": hashlib.sha256((ROOT / "bench" / "quality_tasks.json").read_bytes()).hexdigest(),
                    "checks_sha256": hashlib.sha256((ROOT / "bench" / "quality_checks.py").read_bytes()).hexdigest(),
                    "placebo_sources": comp, "extra_args": CFG["claude_extra_args"], "invocation": "slash command for the skill conditions; pasted: the skill body (no frontmatter) placed before the brief, no skill installed"}
        (out / "env.json").write_text(run.scrub(json.dumps(env_info, indent=1)) + "\n", encoding="utf-8", newline="\n")
        (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(plan)} generations ({len(done)} done) -> {run.scrub(str(out))}", flush=True)
    calls = 0
    with open(out / "raw.jsonl", "a" if a.resume else "w", encoding="utf-8", newline="\n") as raw:
        for p in plan:
            if p["seq"] in done:
                continue
            if a.max_calls and calls >= a.max_calls:
                print(f"STOP: --max-calls reached; continue with --resume {out.name}")
                sys.exit(3)
            wd = build(p["cond"])
            if p["cond"] == "pasted":
                prompt = pasted_text() + "\n\n" + p["brief"] + " " + TASKS["suffix"]
            else:
                prompt = ("/" + SKILL + " " if p["cond"] != "none" else "") + p["brief"] + " " + TASKS["suffix"]
            t0 = time.time()
            o = generate(claude, env, wd, prompt, model)
            calls += 1
            (out / "outputs" / f"{p['seq']:03d}_{p['cond']}_{p['task']}_{p['sample']}.txt").write_text(run.scrub(o["reply"]), encoding="utf-8", newline="\n")
            chk = run_checks(o["reply"])
            reads = [t for t in o["tools"] if t["tool"] == "Read" and "references" in t["input"]]
            u = o["usage"] or {}
            row = {"seq": p["seq"], "cond": p["cond"], "task": p["task"], "sample": p["sample"], "finished": bool(o["reply"]), "turns": o["turns"], "subtype": o["subtype"],
                   "has_html": chk["has_html"], "html_chars": chk.get("html_chars"), "checks": chk["results"], "reference_reads": len(reads),
                   "tool_calls": [t["tool"] for t in o["tools"]], "output_tokens": u.get("output_tokens"), "usage": u, "seconds": round(time.time() - t0, 1), "rate_limit": o["rl"]}
            raw.write(run.scrub(json.dumps(row)) + "\n")
            raw.flush()
            ok = sum(chk["results"].values()) if chk["has_html"] else None
            print(f"[{p['seq']}/{len(plan)}] {p['cond']:8s} {p['task']} s{p['sample']} html={chk['has_html']} pass={ok}/{len(chk['results'])} turns={o['turns']} refreads={len(reads)} "
                  f"out={u.get('output_tokens')} ({row['seconds']}s) meter={(o['rl'] or {}).get('five_hour')}", flush=True)
            rl = o["rl"] or {}
            if not o["reply"]:
                print("STOP: empty reply (a limit or an error); not spending more.")
                sys.exit(3)
            if (rl.get("five_hour") or 0) >= a.stop_at or rl.get("status") not in (None, "allowed", "allowed_warning"):
                print(f"STOP: five-hour meter at {rl.get('five_hour')}; the window resets at {rl.get('five_hour_resets_local')}. Continue then with --resume {out.name}")
                sys.exit(3)
    shutil.rmtree(Path(CFG["workdir_root"]) / "w", ignore_errors=True)
    print("done ->", run.scrub(str(out)))


if __name__ == "__main__":
    main()
