#!/usr/bin/env python3
"""Measure the starting context that N installed skills add to a Claude Code session.

For every (configuration, model, run): recreate one fixed, empty working directory (not a git repository, same path and
path length every time) whose .claude/skills/ holds exactly the configuration's skills, start `claude -p "x"
--max-turns 1` there with user settings, memory, MCP servers and plugins switched off, and record the start-up message
(skills and tools Claude Code reports) and the usage of the first request. Uses the logged-in subscription; API-key and
other billing variables are removed from the child's environment so nothing can bill an API account.

Usage:
  python bench/run.py --dry-run                 build the plan and the working directories, call nothing
  python bench/run.py --only C0,C10 --runs 1    smoke test (after the first run the script stops if the start-up
                                                message has no `skills` field)
  python bench/run.py                           the full plan
Needs CLAUDE_CONFIG_DIR set to an isolated, logged-in configuration directory (not the default ~/.claude).
Writes results/<YYYY-MM-DD>_<machine>_<experiment>/{env.json,plan.json,manifest.json,raw.jsonl,stdout/}; never
overwrites a run. Every string written outside stdout/ is scrubbed of the home directory, user name and temp paths."""
import argparse, datetime, glob, hashlib, json, os, platform, random, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skilltx import FM, disable_model_invocation, frontmatter, replace_body, split_sections, trim_description

CFG = json.loads((ROOT / "bench" / "config.json").read_text(encoding="utf-8"))
MAN = json.loads((ROOT / "workload" / "manifest.json").read_text(encoding="utf-8"))
SRC = ROOT / "workload" / "src"
BODY_HEAVY = "Synthetic placeholder, never invoked. " + ("Filler text for a long skill body. " * 600)
BILLING_VARS = {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
                "CLAUDE_CODE_USE_FOUNDRY", "ANTHROPIC_BASE_URL"}


def strip_var(name):
    n = name.upper()
    return n in BILLING_VARS or n.startswith("ANTHROPIC_") or n.startswith("CLAUDE_CODE_") or n == "CLAUDECODE"


def scrub_patterns():
    home = os.path.expanduser("~")
    user = os.path.basename(home)
    pats = {home, home.replace("\\", "/"), home.replace("\\", "\\\\"), user, os.environ.get("TEMP", ""), os.environ.get("TMP", "")}
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(home, buf, 1024):
            pats.update({buf.value, buf.value.replace("\\", "/"), os.path.basename(buf.value)})
    except Exception:
        pass
    return sorted((p for p in pats if p and len(p) > 2), key=len, reverse=True)


PATS = scrub_patterns()


def scrub(text):
    for p in PATS:
        text = re.sub(re.escape(p), "<scrubbed>", text, flags=re.I)
    return text


def find_claude():
    """CLAUDE_BIN wins (that is how the version is pinned); else claude on PATH; else the newest copy the desktop app
    keeps (its AppData path is virtualised on Windows, so the package folder is searched as well)."""
    if os.environ.get("CLAUDE_BIN"):
        return os.environ["CLAUDE_BIN"]
    found = shutil.which("claude")
    if found:
        return found
    pats = [os.path.expandvars(r"%APPDATA%\Claude\claude-code\*\claude.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude-code\*\claude.exe")]
    cands = [c for pat in pats for c in glob.glob(pat)]

    def ver(c):
        v = Path(c).parent.name
        return [int(x) for x in v.split(".")] if v.replace(".", "").isdigit() else [0]
    if cands:
        return sorted(cands, key=ver)[-1]
    sys.exit("claude not found: set CLAUDE_BIN to the pinned executable")


def refuse_placeholders():
    if "REPLACE_" in json.dumps(CFG["models"]) or "REPLACE_" in json.dumps(CFG["model_windows"]):
        sys.exit("config.json still has REPLACE_* models: set the models and their context windows first")
    missing = [m for m in CFG["models"] if m not in CFG["model_windows"]]
    if missing:
        sys.exit(f"model_windows has no entry for {missing}")
    cd = os.environ.get("CLAUDE_CONFIG_DIR")
    if not cd:
        sys.exit("CLAUDE_CONFIG_DIR is not set: use an isolated, logged-in configuration directory (bench/README.md); "
                 "otherwise your own skills and memory could enter every run and the results")
    if Path(cd).resolve() == (Path.home() / ".claude").resolve():
        sys.exit("CLAUDE_CONFIG_DIR is the default ~/.claude: use an isolated directory")


def skill_dir_for(name):
    """(source folder, is_root_level) of a real skill (popular or random-comparison), or None for a synthetic one."""
    for s in MAN["real_order"] + MAN.get("random_set", []) + MAN.get("extra_skills", []):
        if s["name"] == name:
            return SRC / s["source"].replace("/", "__") / Path(s["path"]).parent, Path(s["path"]).parent == Path(".")
    return None


def rm_tree(path, tries=10):
    """remove a folder; on Windows another process can hold it for a few seconds (a lingering child of a cut-off call): retry, then raise"""
    for _ in range(tries):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(3)
    try:
        shutil.rmtree(path)
    except OSError:   # the folder itself is held open by another process (its current directory): empty it, keep the folder
        for child in Path(path).iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()


def build_workdir(cfg_id):
    wd = Path(CFG["workdir_root"]) / "w"
    if wd.exists():
        rm_tree(wd)
    skills = wd / ".claude" / "skills"
    skills.mkdir(parents=True)
    synth = {s["name"]: s for lst in MAN["synthetic"].values() for s in lst}
    for name in MAN["sets"][cfg_id]:
        d = skills / name
        if name in synth:
            d.mkdir()
            s = synth[name]
            body = BODY_HEAVY if "body_chars" in s else "Synthetic placeholder, never invoked."
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {s['description']}\n---\n\n# {name}\n\n{body}\n",
                                        encoding="utf-8", newline="\n")
        else:
            src, root_level = skill_dir_for(name)
            if root_level:   # a SKILL.md at the repository root: copy that file only, never the whole repository
                d.mkdir()
                shutil.copy2(src / "SKILL.md", d / "SKILL.md")
            else:
                shutil.copytree(src, d)
            tx = MAN.get("variants", {}).get(cfg_id)
            if tx and tx.get("only") and tx["only"] != name:
                tx = None
            if tx:
                f = d / "SKILL.md"
                text = f.read_text(encoding="utf-8-sig")
                if tx["transform"] == "replace_body":
                    body = tx.get("body")
                    if body is None:
                        tsrc, _ = skill_dir_for(tx["body_from_skill"])
                        raw_t = (tsrc / "SKILL.md").read_text(encoding="utf-8-sig")
                        mt = FM.match(raw_t)
                        body = raw_t[mt.end():] if mt else raw_t
                    text = replace_body(text, body)
                elif tx["transform"] == "split_sections":
                    text, extra = split_sections(text, tx["core_chars"])
                    for rel, content in extra.items():
                        (d / rel).parent.mkdir(parents=True, exist_ok=True)
                        (d / rel).write_text(content, encoding="utf-8", newline="\n")
                else:
                    text = disable_model_invocation(text) if tx["transform"] == "disable_model_invocation" else trim_description(text, tx["limit"])
                f.write_text(text, encoding="utf-8", newline="\n")
    mech = MAN.get("mechanisms", {})
    spec = mech.get("configs", {}).get(cfg_id)
    if spec:
        text = instruction_text()
        if spec.get("claude_md"):
            (wd / "CLAUDE.md").write_text(text if spec["claude_md"] == "instruction" else mech["pointer"] + "\n",
                                          encoding="utf-8", newline="\n")
        if spec.get("docs"):
            (wd / "docs").mkdir(exist_ok=True)
            (wd / "docs" / "ui-rules.md").write_text(text, encoding="utf-8", newline="\n")
    return wd


def instruction_text():
    mech = MAN["mechanisms"]
    raw = (SRC / mech["source"].replace("/", "__") / mech["source_path"]).read_text(encoding="utf-8-sig")
    m = FM.match(raw)
    text = raw[m.end():].strip() if m else raw.strip()
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != mech["instruction_sha256"]:
        sys.exit("instruction text differs from the manifest: the clone changed")
    return text


TOOL_CALLS = []


def parse_events(stdout):
    TOOL_CALLS.clear()
    init = first_assistant = result = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        t = e.get("type")
        if t == "system" and e.get("subtype") == "init":
            init = e
        elif t == "assistant" and first_assistant is None:
            first_assistant = e
        if t == "assistant":
            for c in (e.get("message") or {}).get("content", []) or []:
                if c.get("type") == "tool_use":
                    TOOL_CALLS.append({"tool": c.get("name"), "input": json.dumps(c.get("input"))[:120]})
        elif t == "result":
            result = e
    return init, first_assistant, result


def rate_limit(stdout):
    """Subscription meter from the rate_limit_event of one call: five-hour and seven-day utilisation, status, reset time."""
    for line in stdout.splitlines():
        if '"rate_limit_event"' in line:
            try:
                i = json.loads(line)["rate_limit_info"]
                w = i.get("unifiedWindows", {})
                fh = w.get("five_hour", {})
                return {"status": i.get("status"), "five_hour": fh.get("utilization"),
                        "five_hour_resets_local": datetime.datetime.fromtimestamp(fh["resetsAt"]).astimezone().isoformat(timespec="minutes")
                        if fh.get("resetsAt") else None,
                        "seven_day": w.get("seven_day", {}).get("utilization")}
            except (ValueError, KeyError):
                return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma list of configuration ids")
    ap.add_argument("--permission-mode", help="pass --permission-mode to claude (a controlled test of how an unset mode changes the first request)")
    ap.add_argument("--runs", type=int)
    ap.add_argument("--models", help="comma list overriding config models (smoke tests)")
    ap.add_argument("--experiment", help="results folder suffix for a separate part of the study (not a smoke test)")
    ap.add_argument("--resume", help="name of an existing results folder: continue its plan (same Claude Code version)")
    ap.add_argument("--stop-at", type=float, default=0.90,
                    help="stop when the five-hour subscription meter reaches this fraction (default 0.90)")
    ap.add_argument("--max-calls", type=int, help="stop after this many calls in this invocation")
    a = ap.parse_args()
    if not a.dry_run:
        refuse_placeholders()
    claude = find_claude()
    runs = a.runs or CFG["runs"]
    models = a.models.split(",") if a.models else CFG["models"]
    cfg_ids = a.only.split(",") if a.only else list(MAN["sets"])
    unknown = [c for c in cfg_ids if c not in MAN["sets"]]
    if unknown:
        sys.exit(f"unknown configuration(s): {unknown}")
    Path(CFG["workdir_root"]).mkdir(parents=True, exist_ok=True)

    version = subprocess.run([claude, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    second = set(CFG["second_model_configs"])
    plan = [{"config": c, "model": m, "run": r} for c in cfg_ids for m in (models if c in second else models[:1])
            for r in range(1, runs + 1)]
    random.Random(CFG["seed"]).shuffle(plan)   # interleaved, order logged: drift cannot line up with one configuration
    for i, p in enumerate(plan):
        p["seq"] = i + 1

    done, resuming = set(), bool(a.resume)
    if resuming:
        out = ROOT / "results" / a.resume
        if not (out / "plan.json").exists():
            sys.exit(f"cannot resume: {out} has no plan.json")
        old_env = json.loads((out / "env.json").read_text(encoding="utf-8"))
        if old_env["claude_version"] != version:
            sys.exit(f"cannot resume: Claude Code is {version}, the run started on {old_env['claude_version']}")
        if old_env["manifest_sha256"] != hashlib.sha256((ROOT / "workload" / "manifest.json").read_bytes()).hexdigest():
            sys.exit("cannot resume: workload/manifest.json changed since the run started")
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
        for line in (out / "raw.jsonl").read_text(encoding="utf-8").splitlines():
            r0 = json.loads(line)
            if r0.get("usage") and "init_skills" in r0:
                done.add(r0["seq"])
        with open(out / "resumes.jsonl", "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"resumed": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                "already_done": len(done), "stop_at": a.stop_at}) + "\n")
    else:
        out = ROOT / "results" / f"{datetime.date.today().isoformat()}_{CFG['machine']}_{a.experiment or CFG['experiment']}{'_dry' if a.dry_run else ('_smoke' if ((a.only or a.runs or a.models) and not a.experiment) else '')}"
        if out.exists():
            sys.exit(f"{out} exists: results are immutable, remove nothing; wait a day or pass a different experiment name")
        (out / "stdout").mkdir(parents=True)
        shutil.copy2(ROOT / "workload" / "manifest.json", out / "manifest.json")
    removed = sorted(k.upper() for k in os.environ if strip_var(k))
    env_info = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "machine": CFG["machine"],
                "claude_version": version, "claude_path": claude, "os": platform.platform(), "python": platform.python_version(),
                "cpu": platform.processor(), "models": models, "model_windows": CFG["model_windows"],
                "runs_per_config": runs, "permission_mode": a.permission_mode, "seed": CFG["seed"], "extra_args": CFG["claude_extra_args"], "prompt": CFG["prompt"],
                "env_vars_removed_names_only": removed, "isolated_config_dir": bool(os.environ.get("CLAUDE_CONFIG_DIR")),
                "workdir_path_length": len(str(Path(CFG["workdir_root"]) / "w")),
                "manifest_sha256": hashlib.sha256((ROOT / "workload" / "manifest.json").read_bytes()).hexdigest(),
                "popularity_snapshot_raw_page_sha256": MAN["snapshot_raw_page_sha256"],
                "repo_commits": json.loads((ROOT / "workload" / "fetched.json").read_text(encoding="utf-8"))}
    if not resuming:
        (out / "env.json").write_text(scrub(json.dumps(env_info, indent=1)) + "\n", encoding="utf-8", newline="\n")
        (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8", newline="\n")

    env = {k: v for k, v in os.environ.items() if not strip_var(k)}
    print(f"{len(plan)} runs ({len(done)} already done) -> {scrub(str(out))}")
    print(f"claude: {scrub(claude)} ({version})")
    calls = 0
    with open(out / "raw.jsonl", "a" if resuming else "w", encoding="utf-8", newline="\n") as raw:
        for p in plan:
            if p["seq"] in done:
                continue
            if a.max_calls and calls >= a.max_calls:
                print(f"STOP: --max-calls {a.max_calls} reached; continue with --resume {out.name}")
                sys.exit(3)
            wd = build_workdir(p["config"])
            prompt = MAN.get("prompts", {}).get(p["config"], CFG["prompt"]).replace("__INSTRUCTION__", instruction_text() if "mechanisms" in MAN else "")
            turns = str(MAN.get("max_turns", {}).get(p["config"], 1))
            cmd = [claude, "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns", turns,
                   "--model", p["model"], *CFG["claude_extra_args"], *(["--permission-mode", a.permission_mode] if a.permission_mode else [])]
            row = {**p, "n_expected": len(MAN["sets"][p["config"]]), "expected_skills": MAN["sets"][p["config"]],
                   "command": ["claude"] + [(c if c is not prompt else (c if len(c) < 200 else f"<prompt of {len(c)} characters>")) for c in cmd[1:]]}
            if a.dry_run:
                row["workdir_skill_folders"] = sorted(x.name for x in (wd / ".claude" / "skills").iterdir())
                print(f"[{p['seq']}/{len(plan)}] {p['config']} {p['model']} run {p['run']} (dry)")
            else:
                t0 = time.time()
                try:
                    cp = subprocess.run(cmd, cwd=wd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                                        errors="replace", timeout=240)
                    stdout, stderr, rc = cp.stdout, cp.stderr[-500:], cp.returncode
                except subprocess.TimeoutExpired as e:
                    part = e.stdout or ""
                    stdout, stderr, rc = (part.decode("utf-8", "replace") if isinstance(part, bytes) else part), "timeout", -1
                row["seconds"] = round(time.time() - t0, 1)
                row["returncode"], row["stderr_tail"] = rc, stderr
                (out / "stdout" / f"{p['seq']:03d}_{p['config']}.jsonl").write_text(stdout, encoding="utf-8", newline="\n")
                init, first, res = parse_events(stdout)
                if init:
                    row["init_has_skills_field"] = "skills" in init
                    row["init_skills"] = init.get("skills", []) or []
                    row["init_tools"] = init.get("tools", []) or []
                    row["init_slash_commands"] = init.get("slash_commands", []) or []
                    row["init_model"] = init.get("model")
                row["tool_calls"] = list(TOOL_CALLS)
                if first:
                    row["first_request_usage"] = (first.get("message") or {}).get("usage")
                if res:
                    row["result_subtype"] = res.get("subtype")
                    row["is_error"] = res.get("is_error")
                    row["num_turns"] = res.get("num_turns")
                    row["result_usage"] = res.get("usage")
                    row["iterations"] = (res.get("usage") or {}).get("iterations")
                    row["model_usage"] = res.get("modelUsage")
                    row["reported_cost_usd"] = res.get("total_cost_usd")
                row["usage"] = row.get("first_request_usage") or row.get("result_usage")
                rl = rate_limit(stdout)
                if rl:
                    row["rate_limit"] = rl
                calls += 1
                print(f"[{p['seq']}/{len(plan)}] {p['config']} {p['model']} run {p['run']} rc={rc} {row['seconds']}s"
                      f"{' NO-USAGE' if not row['usage'] else ''}")
                time.sleep(2)
            raw.write(scrub(json.dumps(row)) + "\n")
            raw.flush()
            if not a.dry_run:
                rl = row.get("rate_limit") or {}
                why = None
                if not row.get("usage"):
                    why = "this call returned no usage (a limit or an error): stopping so no more of the allowance is spent"
                elif rl.get("status") not in (None, "allowed", "allowed_warning"):
                    why = f"subscription status is {rl.get('status')}"
                elif rl.get("five_hour") is not None and rl["five_hour"] >= a.stop_at:
                    why = f"five-hour meter is at {rl['five_hour']:.0%} (stop-at {a.stop_at:.0%})"
                if why:
                    resets = rl.get("five_hour_resets_local")
                    print(f"STOP: {why}. The five-hour window resets at {resets}. Continue then with: "
                          f"python bench/run.py --resume {out.name}")
                    sys.exit(3)
            if not a.dry_run and p["seq"] == 1 and not row.get("init_has_skills_field"):
                sys.exit("STOP: the start-up message has no `skills` field (or no start-up message arrived), so the isolation "
                         "check cannot work. Look at results/<run>/stdout/001_*.jsonl and fix the harness before continuing.")
    shutil.rmtree(Path(CFG["workdir_root"]) / "w", ignore_errors=True)
    print("done ->", scrub(str(out)))


if __name__ == "__main__":
    main()
