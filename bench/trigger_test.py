#!/usr/bin/env python3
"""Trigger test: does the model call a skill when it should, and not when it should not, for three descriptions of it?

For each skill, description variant (original, cut at a word boundary to 100 and to 40 characters), setting (the skill alone,
or among the 49 most-installed other skills) and prompt (4 that should trigger it, 2 of them with its keywords and 2
paraphrased; 4 that should not, one of them a near-miss), start `claude -p` with up to three turns and watch the stream
until the outcome is clear: a Skill tool call (with the skill name), or a text answer longer than 600 characters, or the end of
the run. Other tools (a model that explores first) do not end the watch. Nothing after the decision is generated, so a call
costs little of the subscription allowance. A watchdog kills a silent process after 150 seconds.
Usage:
  python bench/trigger_test.py --dry-run
  python bench/trigger_test.py --runs 3 [--max-calls N] [--stop-at 0.80] [--resume <results folder>]
Needs CLAUDE_CONFIG_DIR (isolated, logged in). Writes results/<date>_<machine>_trigger/{env.json,plan.json,raw.jsonl}."""
import argparse, datetime, hashlib, json, os, random, shutil, subprocess, sys, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run
from skilltx import frontmatter, trim_description

ROOT = run.ROOT
CFG = run.CFG
MAN = run.MAN
PROMPTS = json.loads((ROOT / "bench" / "trigger_prompts.json").read_text(encoding="utf-8"))
TX = CFG["trigger_experiment"]
TEXT_LIMIT = 600


def kill_tree(p):
    """end the call and every process it started (the model may have started a shell in the working folder, which would lock it)"""
    try:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=30)
    except Exception:
        pass
    try:
        p.kill()
    except Exception:
        pass


def build(skill, variant_limit, setting):
    wd = Path(CFG["workdir_root"]) / "w"
    if wd.exists():
        run.rm_tree(wd)
    sk = wd / ".claude" / "skills"
    sk.mkdir(parents=True)
    names = [skill]
    if setting == "crowded":
        names += [s["name"] for s in MAN["real_order"] if s["name"] != skill][:49]
    used = None
    for n in names:
        src, root_level = run.skill_dir_for(n)
        d = sk / n
        if root_level:
            d.mkdir()
            shutil.copy2(src / "SKILL.md", d / "SKILL.md")
        else:
            shutil.copytree(src, d)
        if n == skill:
            f = d / "SKILL.md"
            if variant_limit:
                f.write_text(trim_description(f.read_text(encoding="utf-8-sig"), variant_limit), encoding="utf-8", newline="\n")
            used = frontmatter(f.read_text(encoding="utf-8-sig")).get("description", "")
    return wd, used


def first_move(claude, env, wd, prompt, model, skill):
    p = subprocess.Popen([claude, "-p", prompt, "--output-format", "stream-json", "--verbose", "--include-partial-messages",
                          "--max-turns", "3", "--model", model, *CFG["claude_extra_args"]],
                         cwd=wd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, encoding="utf-8", errors="replace")
    timer = threading.Timer(150, kill_tree, [p])
    timer.start()
    t0, decision, rl, buf, tool, text, other_tools, first_text = time.time(), None, None, "", None, 0, [], ""
    usage1 = None   # token counts of the first request (message_start); the call is cut at the decision, so only this side is known
    try:
        for line in p.stdout:
            if not line.startswith("{"):
                continue
            e = json.loads(line)
            t = e.get("type")
            if t == "rate_limit_event" and rl is None:
                rl = run.rate_limit(line)
            if t == "result":
                break
            if t != "stream_event":
                continue
            ev = e["event"]
            et = ev.get("type")
            if et == "message_start" and usage1 is None:
                usage1 = (ev.get("message") or {}).get("usage")
            if et == "content_block_start":
                cb = ev["content_block"]
                tool = cb.get("name") if cb["type"] == "tool_use" else None
                if tool and tool != "Skill":
                    other_tools.append(tool)
                buf = ""
            elif et == "content_block_delta":
                d = ev["delta"]
                if d.get("type") == "text_delta":
                    text += len(d["text"])
                    if len(first_text) < 160:
                        first_text += d["text"]
                    if text > TEXT_LIMIT:
                        decision = "text"
                        break
                elif d.get("type") == "input_json_delta" and tool == "Skill":
                    buf += d.get("partial_json", "")
                    try:
                        decision = "skill:" + json.loads(buf).get("skill", "?")
                        break
                    except ValueError:
                        pass
    finally:
        timer.cancel()
        kill_tree(p)
    if decision is None:
        decision = "text" if text else ("none" if time.time() - t0 < 149 else "timeout")
    return decision, rl, round(time.time() - t0, 1), other_tools, first_text.replace("\n", " ")[:160], usage1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--runs", type=int, default=TX["runs"])
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--stop-at", type=float, default=0.80)
    ap.add_argument("--resume")
    ap.add_argument("--experiment", default="trigger")
    a = ap.parse_args()
    if not a.dry_run:
        run.refuse_placeholders()
    claude = run.find_claude()
    model = CFG["models"][0]
    plan = []
    for skill in TX["skills"]:
        for vname, lim in TX["variants"].items():
            for setting in TX["settings"]:
                for pol in ("positive", "negative"):
                    for pr in PROMPTS[skill][pol]:
                        for r in range(1, a.runs + 1):
                            plan.append({"skill": skill, "variant": vname, "limit": lim, "setting": setting, "polarity": pol,
                                         "prompt_id": pr["id"], "kind": pr["kind"], "prompt": pr["text"], "run": r})
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
        text = (out / "raw.jsonl").read_text(encoding="utf-8")
        done = {json.loads(l)["seq"] for l in text.splitlines() if l.strip() and json.loads(l).get("decision") not in (None, "none", "timeout")}
        if text and not text.endswith("\n"):
            (out / "raw.jsonl").write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        out = ROOT / "results" / f"{datetime.date.today().isoformat()}_{CFG['machine']}_{a.experiment}{'_dry' if a.dry_run else ''}"
        if out.exists():
            sys.exit(f"{out} exists: use --resume or another --experiment name")
        out.mkdir(parents=True)
        env_info = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "claude_version": version, "model": model,
                    "model_window": CFG["model_windows"][model], "runs": a.runs, "seed": CFG["seed"], "experiment": TX,
                    "text_limit_chars": TEXT_LIMIT, "max_turns": 3,
                    "prompts_sha256": hashlib.sha256((ROOT / "bench" / "trigger_prompts.json").read_bytes()).hexdigest(),
                    "extra_args": CFG["claude_extra_args"], "isolated_config_dir": bool(os.environ.get("CLAUDE_CONFIG_DIR"))}
        (out / "env.json").write_text(run.scrub(json.dumps(env_info, indent=1)) + "\n", encoding="utf-8", newline="\n")
        (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8", newline="\n")
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    print(f"{len(plan)} calls ({len(done)} done) -> {run.scrub(str(out))}")
    calls = 0
    with open(out / "raw.jsonl", "a" if a.resume else "w", encoding="utf-8", newline="\n") as raw:
        for p in plan:
            if p["seq"] in done:
                continue
            if a.max_calls and calls >= a.max_calls:
                print(f"STOP: --max-calls reached; continue with --resume {out.name}")
                sys.exit(3)
            row = {k: p[k] for k in ("seq", "skill", "variant", "setting", "polarity", "prompt_id", "kind", "run")}
            wd, used_desc = build(p["skill"], p["limit"], p["setting"])
            row["description_chars_used"] = len(used_desc)
            if p["run"] == 1 and p["prompt_id"] in ("P1", "N1"):
                row["description_used"] = used_desc
            if a.dry_run:
                row["skills_in_workdir"] = len(list((wd / ".claude" / "skills").iterdir()))
                print(f"[{p['seq']}/{len(plan)}] {p['skill']} {p['variant']} {p['setting']} {p['prompt_id']} (dry, {row['skills_in_workdir']} skills, desc {len(used_desc)} chars)")
            else:
                decision, rl, secs, others, first_text, usage1 = first_move(claude, env, wd, p["prompt"], model, p["skill"])
                calls += 1
                row.update({"decision": decision, "hit": decision == "skill:" + p["skill"],
                            "other_skill": decision.startswith("skill:") and decision != "skill:" + p["skill"],
                            "tools_before_decision": others, "first_text": first_text, "seconds": secs, "rate_limit": rl, "first_request_usage": usage1})
                print(f"[{p['seq']}/{len(plan)}] {p['skill']} {p['variant']} {p['setting']} {p['prompt_id']} -> {decision} {others or ''} ({secs}s)", flush=True)
                raw.write(run.scrub(json.dumps(row)) + "\n")
                raw.flush()
                if decision in ("none", "timeout"):
                    print("STOP: no decision from the model (a limit or an error); not spending more.")
                    sys.exit(3)
                if rl and ((rl.get("five_hour") or 0) >= a.stop_at or rl.get("status") not in (None, "allowed", "allowed_warning")):
                    print(f"STOP: five-hour meter at {rl.get('five_hour')} (status {rl.get('status')}); the window resets at "
                          f"{rl.get('five_hour_resets_local')}. Continue then with --resume {out.name}")
                    sys.exit(3)
                continue
            raw.write(json.dumps(row) + "\n")
            raw.flush()
    shutil.rmtree(Path(CFG["workdir_root"]) / "w", ignore_errors=True)
    print("done ->", run.scrub(str(out)))


if __name__ == "__main__":
    main()
