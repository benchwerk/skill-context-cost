#!/usr/bin/env python3
"""Claim probes: one small experiment per documented behaviour of skills in Claude Code, each with the claim's own prediction.

Every probe builds a throwaway working directory (separate from the trigger test's), starts `claude -p` once or a few times,
and reads what Claude Code reports: the skills and slash commands in its start-up message, the tokens of the first request,
the model's text and its tool calls. `expect` is what the cited documentation says should happen, written before running;
`check` compares it with what was observed and returns a verdict: holds, fails, or inconclusive.
Usage:
  python bench/claim_probes.py --list
  python bench/claim_probes.py [--only P-01,P-04] [--stop-at 0.80]
Needs CLAUDE_CONFIG_DIR (isolated, logged in). Probes write only into their own working directory, except P-09, which puts one personal test skill into the isolated configuration directory and removes it afterwards.
Writes results/<date>_<machine>_claims/{env.json,raw.jsonl,findings.json}."""
import argparse, datetime, json, os, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run

ROOT, CFG = run.ROOT, run.CFG
PROBE_ROOT = Path(CFG["workdir_root"]) / "p"
BASE_SKILLS = set()   # bundled skills reported by an empty directory, filled in by the control run
CTL = {}              # control observation


def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def skill(wd, name, desc="Use when the user asks for the probe check.", body="Probe body.", extra="", fm_name=None, folder=".claude/skills", dirname=None):
    d = wd / folder / (dirname or name)
    fm = f"---\nname: {fm_name or name}\ndescription: {desc}\n{extra}---\n\n{body}\n"
    w(d / "SKILL.md", fm)


def personal_dir(name):
    """personal skill folder inside the isolated config dir (never the default ~/.claude)"""
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    if not cfg or Path(cfg).resolve() == (Path.home() / ".claude").resolve():
        sys.exit("refusing: CLAUDE_CONFIG_DIR must point at the isolated bench config dir")
    return Path(cfg) / "skills" / name


def personal_skill(name, body):
    w(personal_dir(name) / "SKILL.md", f"---\nname: {name}\ndescription: Use when the user asks for the probe check.\n---\n\n{body}\n")


def new(o):
    """skills reported beyond the bundled ones"""
    return sorted(set(o["skills"]) - BASE_SKILLS)


def added(o):
    return o["tokens"] - CTL["tokens"]


# ---------------------------------------------------------------- probes
def p04_setup(n):
    return lambda wd: skill(wd, "lenprobe", desc=("Use when the user asks for the length probe. " + "alpha beta gamma delta " * 400)[:n])


def p05_setup(v):
    return lambda wd: skill(wd, "boolprobe", extra=f"disable-model-invocation: {v}\n")


PROBES = [
    {"id": "P-01", "claims": ["C-031"], "title": "a skill with no frontmatter at all",
     "expect": "Claude Code: loads, named after its directory (the open spec calls frontmatter required)",
     "setup": lambda wd: w(wd / ".claude/skills/nofm/SKILL.md", "Just a body, no header.\n"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "nofm" in new(os_[0]) else "fails")},
    {"id": "P-02", "claims": ["C-090"], "title": "frontmatter name differs from the directory name",
     "expect": "spec: name must match the directory; client guidance: load leniently (either name may appear)",
     "setup": lambda wd: skill(wd, "dirname-a", fm_name="fmname-b"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if new(os_[0]) else "fails")},
    {"id": "P-03", "claims": ["C-068"], "title": "reserved word 'claude' in the skill name",
     "expect": "platform docs: forbidden; Claude Code docs reserve only anthropic-skills and synced (claim = not loaded)",
     "setup": lambda wd: skill(wd, "claude-helper"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "fails" if "claude-helper" in new(os_[0]) else "holds")},
    {"id": "P-04", "claims": ["C-004", "C-069", "K-030"], "title": "description length against listing tokens (500 to 6,000 characters)",
     "expect": "the listing cap is 1,536 characters: tokens grow until about 1,536 characters and then stop (the spec says 1,024; an old issue says 250)",
     "variants": [(f"L{n}", p04_setup(n)) for n in (500, 1000, 1100, 1536, 1600, 3000, 6000)],
     "check": None},
    {"id": "P-05", "claims": ["C-045"], "title": "boolean spellings of disable-model-invocation",
     "expect": "true, True, YES, yes, 1, on all hide the skill from the model (listing cost 0); false does not",
     "variants": [(f"B-{v}", p05_setup(v)) for v in ("true", "True", "YES", "yes", "1", "on", "false")],
     "check": None},
    {"id": "P-06", "claims": ["C-047"], "title": "invalid optional fields (license, compatibility, metadata)",
     "expect": "accepted but ignored: the skill still loads",
     "setup": lambda wd: skill(wd, "optfields", extra="license: 12345\ncompatibility: " + "x" * 600 + "\nmetadata:\n  nested:\n    deep: [1, 2]\n"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "optfields" in new(os_[0]) else "fails")},
    {"id": "P-07", "claims": ["K-010"], "title": "block-scalar description (>-) against a single-line one",
     "expect": "both load and cost the same (the claim of a broken loader concerns reflowed files)",
     "variants": [("single", lambda wd: skill(wd, "blk", desc="Use when the user asks for the block probe and wants a long answer about it.")),
                  ("block", lambda wd: w(wd / ".claude/skills/blk/SKILL.md", "---\nname: blk\ndescription: >-\n  Use when the user asks for the block probe\n  and wants a long answer about it.\n---\n\nProbe body.\n"))],
     "check": None},
    {"id": "P-08", "claims": ["C-025"], "title": "a skill and a command with the same name",
     "expect": "the skill wins (the reply contains SKILLVERSION)", "turns": 2, "prompt": "/dup",
     "setup": lambda wd: (skill(wd, "dup", body="Reply with exactly the single word SKILLVERSION and nothing else."),
                          w(wd / ".claude/commands/dup.md", "Reply with exactly the single word CMDVERSION and nothing else.\n")),
     "check": lambda os_: (f"reply: {os_[0]['text'][:80]!r}", "holds" if "SKILLVERSION" in os_[0]["text"] else ("fails" if "CMDVERSION" in os_[0]["text"] else "inconclusive"))},
    {"id": "P-09", "claims": ["C-024"], "title": "same skill name in the personal config and in the project",
     "expect": "documentation: personal over project (the CLI help calls project over user the universal convention); reply names the winner",
     "turns": 2, "prompt": "/prec", "runs": 3,
     "variants": [("both", lambda wd: (skill(wd, "prec", body="Reply with exactly the single word PROJECTVERSION and nothing else."),
                                       personal_skill("prec", "Reply with exactly the single word PERSONALVERSION and nothing else.")))],
     "cleanup": lambda: shutil.rmtree(personal_dir("prec"), ignore_errors=True),
     "check": None},
    {"id": "P-10", "claims": ["C-021"], "title": "a skill in a nested directory",
     "expect": "not listed at start; loads only when a file in that subdirectory is read",
     "setup": lambda wd: skill(wd, "deepskill", folder="sub/.claude/skills"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "deepskill" not in new(os_[0]) else "fails")},
    {"id": "P-11a", "claims": ["C-022"], "title": "start in a subfolder, skill in the parent (no git)",
     "expect": "parent .claude/skills is found up to the repository root", "cwd": "sub",
     "setup": lambda wd: (skill(wd, "upskill"), (wd / "sub").mkdir(exist_ok=True)),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "upskill" in new(os_[0]) else "fails")},
    {"id": "P-11b", "claims": ["C-022"], "title": "start in a subfolder, skill in the parent (git repository)",
     "expect": "parent .claude/skills is found up to the repository root", "cwd": "sub",
     "setup": lambda wd: (skill(wd, "upskill"), (wd / "sub").mkdir(exist_ok=True), subprocess.run(["git", "init", "-q"], cwd=wd, check=False)),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "upskill" in new(os_[0]) else "fails")},
    {"id": "P-12", "claims": ["C-040"], "title": "paths globs",
     "expect": "a skill with paths: ['**/*.py'] is not offered to the model until a matching file is touched (listing cost about 0)",
     "setup": lambda wd: skill(wd, "pyonly", extra="paths:\n  - '**/*.py'\n"),
     "check": lambda os_: (f"added tokens {added(os_[0])}", "holds" if added(os_[0]) < 15 else "fails")},
    {"id": "P-13", "claims": ["C-108"], "title": "skills under .agents/skills",
     "expect": "client guidance: a widely adopted location; Claude Code docs list only .claude/skills (either result is informative)",
     "setup": lambda wd: skill(wd, "agentsdir", folder=".agents/skills"),
     "check": lambda os_: (f"skills beyond bundled: {new(os_[0])}", "holds" if "agentsdir" in new(os_[0]) else "fails")},
    {"id": "P-14", "claims": ["C-044"], "title": "argument substitution",
     "expect": "$ARGUMENTS = all arguments, $0 and $1 the first two; a missing positional ($2) stays literal",
     "turns": 2, "prompt": "/argsprobe alpha beta",
     "setup": lambda wd: skill(wd, "argsprobe", body="Reply with exactly this line and nothing else: A=$ARGUMENTS|F=$0|S=$1|T=$2"),
     "check": lambda os_: (f"reply: {os_[0]['text'][:90]!r}", "holds" if "A=alpha beta|F=alpha|S=beta|T=$2" in os_[0]["text"] else "fails")},
    {"id": "P-15a", "claims": ["C-042"], "title": "shell injection runs before the content is sent",
     "expect": "the output replaces the placeholder (the reply contains INJECTED_OK_42)", "turns": 2, "prompt": "/inj",
     "setup": lambda wd: skill(wd, "inj", body="Reply with exactly the next line and nothing else:\n!`echo INJECTED_OK_42`"),
     "check": lambda os_: (f"reply: {os_[0]['text'][:80]!r}", "holds" if "INJECTED_OK_42" in os_[0]["text"] else "fails")},
    {"id": "P-15b", "claims": ["C-042"], "title": "a failing injected command",
     "expect": "the whole invocation aborts (no normal reply)", "turns": 2, "prompt": "/failinj",
     "setup": lambda wd: skill(wd, "failinj", body="Reply with exactly the word REACHED.\n!`exit 3`"),
     "check": lambda os_: (f"reply: {os_[0]['text'][:80]!r}", "fails" if "REACHED" in os_[0]["text"] else "holds")},
    {"id": "P-17", "claims": ["C-032"], "title": "disable-model-invocation stops automatic use",
     "expect": "with the flag the model never calls the skill; without it, it does", "turns": 2, "runs": 3,
     "prompt": "Please parse this invoice and list the line items: Invoice 17, 3 x widgets at 5.00, 2 x gadgets at 7.50.",
     "variants": [("with-flag", lambda wd: skill(wd, "invoice-parser", desc="Use when the user asks to parse invoices or list invoice line items.", extra="disable-model-invocation: true\n")),
                  ("without-flag", lambda wd: skill(wd, "invoice-parser", desc="Use when the user asks to parse invoices or list invoice line items."))],
     "check": None},
]


def observe(claude, env, wd, prompt, turns, model, cwd):
    cp = subprocess.run([claude, "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns", str(turns), "--model", model,
                         *CFG["claude_extra_args"]], cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=240)
    o = {"skills": [], "slash": [], "tokens": None, "text": "", "tools": [], "rl": None, "rc": cp.returncode}
    for l in cp.stdout.splitlines():
        if not l.startswith("{"):
            continue
        e = json.loads(l)
        t = e.get("type")
        if t == "system" and e.get("subtype") == "init":
            o["skills"], o["slash"] = e.get("skills", []), e.get("slash_commands", [])
        elif t == "assistant":
            u = (e.get("message") or {}).get("usage") or {}
            if o["tokens"] is None and u:
                o["tokens"] = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            for c in (e.get("message") or {}).get("content", []) or []:
                if c.get("type") == "text":
                    o["text"] += c.get("text", "")
                elif c.get("type") == "tool_use":
                    o["tools"].append({"tool": c.get("name"), "input": json.dumps(c.get("input"))[:100]})
        elif t == "rate_limit_event" and o["rl"] is None:
            o["rl"] = run.rate_limit(l)
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--stop-at", type=float, default=0.80)
    ap.add_argument("--experiment", default="claims")
    ap.add_argument("--resume", help="accepted so a supervisor can restart the run; finished probes in the results folder are skipped")
    a = ap.parse_args()
    if a.list:
        for p in PROBES:
            print(f"{p['id']:6s} {','.join(p['claims']):22s} {p['title']}\n         expect: {p['expect']}")
        return
    run.refuse_placeholders()
    shutil.rmtree(personal_dir("prec"), ignore_errors=True)   # leftover from an interrupted P-09
    claude, model = run.find_claude(), CFG["models"][0]
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    out = ROOT / "results" / f"{datetime.date.today().isoformat()}_{CFG['machine']}_{a.experiment}"
    out.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([claude, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    (out / "env.json").write_text(run.scrub(json.dumps({"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                                         "claude_version": version, "model": model, "probe_ids": [p["id"] for p in PROBES]}, indent=1)) + "\n", encoding="utf-8", newline="\n")
    only = set(a.only.split(",")) if a.only else None
    raw = open(out / "raw.jsonl", "a", encoding="utf-8", newline="\n")
    findings = []
    if (out / "findings.json").exists():
        findings = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    done_ids = {f["probe"] for f in findings}

    def fresh():
        if PROBE_ROOT.exists():
            shutil.rmtree(PROBE_ROOT)
        wd = PROBE_ROOT / "w"
        wd.mkdir(parents=True)
        return wd

    def go(label, setup, prompt, turns, cwd_sub):
        wd = fresh()
        if setup:
            setup(wd)
        cwd = wd / cwd_sub if cwd_sub else wd
        o = observe(claude, env, wd, prompt, turns, model, cwd)
        raw.write(run.scrub(json.dumps({"probe": label, **o})) + "\n")
        raw.flush()
        print(f"  {label}: skills+{len(set(o['skills']) - BASE_SKILLS)} tokens={o['tokens']} text={o['text'][:50]!r} tools={[t['tool'] for t in o['tools']]}", flush=True)
        rl = o["rl"] or {}
        if (rl.get("five_hour") or 0) >= a.stop_at:
            print(f"STOP: five-hour meter at {rl.get('five_hour')}; the window resets at {rl.get('five_hour_resets_local')}. Continue then with --resume {out.name}")
            sys.exit(3)
        return o

    ctl = go("CONTROL", None, "x", 1, None)
    BASE_SKILLS.update(ctl["skills"])
    CTL.update(ctl)
    for p in PROBES:
        if (only and p["id"] not in only) or p["id"] in done_ids:
            continue
        print(p["id"], p["title"], flush=True)
        prompt, turns = p.get("prompt", "x"), p.get("turns", 1)
        if p.get("variants"):
            res = {}
            for vname, setup in p["variants"]:
                runs = [go(f"{p['id']}:{vname}:{r}", setup, prompt, turns, p.get("cwd")) for r in range(p.get("runs", 1))]
                res[vname] = runs
            if p.get("cleanup"):
                p["cleanup"]()
            if p["id"] == "P-04":
                pts = [(int(k[1:]), added(v[0])) for k, v in res.items()]
                obs = ", ".join(f"{n}ch:+{t}" for n, t in pts)
                top = max(t for _, t in pts)
                plateau = next((n for n, t in pts if t >= 0.97 * top), None)
                verdict = "holds" if plateau and 1400 <= plateau <= 1700 else ("fails" if plateau else "inconclusive")
                note = f"{obs}; reaches 97% of the maximum at {plateau} characters"
            elif p["id"] == "P-05":
                note = ", ".join(f"{k[2:]}:+{added(v[0])}" for k, v in res.items())
                hidden = {k[2:]: added(v[0]) < 15 for k, v in res.items()}
                verdict = "holds" if all(hidden[v] for v in ("true", "True", "YES", "yes", "1", "on")) and not hidden["false"] else "fails"
            elif p["id"] == "P-07":
                s, b = added(res["single"][0]), added(res["block"][0])
                note = f"single +{s}, block +{b}; listed: {new(res['block'][0])}"
                verdict = "holds" if "blk" in new(res["block"][0]) and abs(s - b) <= 6 else "fails"
            elif p["id"] == "P-09":
                words = ["PERSONAL" if "PERSONALVERSION" in o["text"] else "PROJECT" if "PROJECTVERSION" in o["text"] else "NEITHER" for o in res["both"]]
                note = f"winners over {len(words)} runs: {words}"
                verdict = "holds" if all(x == "PERSONAL" for x in words) else ("fails" if all(x == "PROJECT" for x in words) else "inconclusive")
            elif p["id"] == "P-17":
                n_with = sum(1 for o in res["with-flag"] if any(t["tool"] == "Skill" for t in o["tools"]))
                n_without = sum(1 for o in res["without-flag"] if any(t["tool"] == "Skill" for t in o["tools"]))
                note = f"Skill calls: with flag {n_with}/{len(res['with-flag'])}, without {n_without}/{len(res['without-flag'])}"
                verdict = "holds" if n_with == 0 and n_without >= 2 else ("inconclusive" if n_without < 2 else "fails")
        else:
            o = go(p["id"], p["setup"], prompt, turns, p.get("cwd"))
            note, verdict = p["check"]([o])
        findings.append({"probe": p["id"], "claims": p["claims"], "title": p["title"], "expect": p["expect"], "observed": note, "verdict": verdict})
        print(f"  -> {verdict}: {note}", flush=True)
        (out / "findings.json").write_text(json.dumps(findings, indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "findings.json").write_text(json.dumps(findings, indent=1) + "\n", encoding="utf-8", newline="\n")
    shutil.rmtree(PROBE_ROOT, ignore_errors=True)
    print("done ->", run.scrub(str(out)))


if __name__ == "__main__":
    main()
