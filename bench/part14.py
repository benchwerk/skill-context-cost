"""Part 14 (prediction.md): starting size by setting (14A), listing cap at 100/200/400 skills (14B), delivery by @file (14C), bundled
skill-writing skills (14D). First-request window totals only: one request per call, max one turn, no output used.

  CLAUDE_CONFIG_DIR=<isolated dir> python bench/part14.py [--parts A,B,C,D]  ->  results/<date>_<machine>_part14/raw.jsonl
"""
import argparse, datetime, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"sonnet": "claude-sonnet-5-5[1m]", "haiku": "claude-haiku-4-5-20251001", "opus": "claude-opus-5-5[1m]"}
A_SETTINGS = {
    "default": [],
    "no-skills": ["--disable-slash-commands"],
    "tools3": ["--tools", "Read,Edit,Bash"],
    "tools1": ["--tools", "Read"],
    "system-prompt": ["--system-prompt", "You are a helpful coding assistant."],
    "exclude-dynamic": ["--exclude-dynamic-system-prompt-sections"],
    "minimal": ["--disable-slash-commands", "--tools", "Read,Edit,Bash", "--system-prompt", "You are a helpful coding assistant."],
}


def synth_skills(n, chars=150):
    out = []
    for i in range(n):
        d = f"Use when the user asks about topic number {i:03d} (synthetic skill). Covers creating, reviewing and summarising the files, with a short report."
        out.append((f"syn150-{i:03d}", (d + " Extra filler words to fill the line." * 5)[:chars]))
    return out


def build(extra_skills=(), files=None):
    wd = run.build_workdir("C0")
    for name, desc in extra_skills:
        d = wd / ".claude" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nSynthetic placeholder, never invoked.\n", encoding="utf-8", newline="\n")
    for rel, text in (files or {}).items():
        p = wd / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    return wd


def call(exe, wd, model, prompt, extra, env):
    cmd = [exe, "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns", "1", "--model", model, *run.CFG["claude_extra_args"], *extra]
    cp = subprocess.run(cmd, cwd=wd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    init, first, result = run.parse_events(cp.stdout)
    u = ((first or {}).get("message") or {}).get("usage") or {}
    total = sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return {"window_total": total, "usage": u, "n_tools": len((init or {}).get("tools", [])), "n_skills": len((init or {}).get("skills", [])),
            "skills": sorted((init or {}).get("skills", [])), "status": (result or {}).get("subtype"), "exit": cp.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="A,B,C,D")
    a = ap.parse_args()
    exe = run.find_claude()
    env = {k: v for k, v in os.environ.items() if not run.strip_var(k)}
    env["CLAUDE_CONFIG_DIR"] = os.environ["CLAUDE_CONFIG_DIR"]
    out = ROOT / "results" / f"{datetime.date.today()}_x86-laptop_part14"
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "raw.jsonl"
    seq = [0]

    done = {(r["part"], r["condition"], r["model"], r["rep"]) for r in map(json.loads, raw.read_text(encoding="utf-8").splitlines())} if raw.exists() else set()
    seq[0] = len(done)

    def rec(part, cond, model, prompt, extra, wd, rep):
        if (part, cond, model, rep) in done:   # resume: a finished row is never repeated
            return
        r = call(exe, wd, MODELS[model], prompt, extra, env)
        seq[0] += 1
        row = {"seq": seq[0], "part": part, "condition": cond, "model": model, "rep": rep, "prompt_chars": len(prompt), **r}
        with raw.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
        print(part, cond, model, rep, r["window_total"], r["n_tools"], r["n_skills"], r["status"], flush=True)

    parts = a.parts.split(",")
    if "A" in parts:
        for model in MODELS:
            for cond, extra in A_SETTINGS.items():
                for rep in (1, 2):
                    rec("A", cond, model, "x", extra, build(), rep)
    if "B" in parts:
        for n in (0, 100, 200, 400):
            for rep in (1, 2, 3):
                rec("B", f"syn{n}", "sonnet", "x", [], build(synth_skills(n)), rep)
    if "C" in parts:
        text = run.instruction_text()
        task = run.MAN["mechanisms"]["task"]
        files = {"docs/ui-rules.md": text}
        for rep in range(1, 6):
            rec("C", "base", "sonnet", task, [], build(), rep)
            rec("C", "file-present-unreferenced", "sonnet", task, [], build(files=files), rep)
            rec("C", "at-file", "sonnet", task + " @docs/ui-rules.md", [], build(files=files), rep)
            rec("C", "pasted", "sonnet", text + "\n\n" + task, [], build(), rep)
    if "D" in parts:
        for rep in (1, 2, 3):
            rec("D", "baseline", "sonnet", "x", [], build(), rep)
            for sk in ("plugin-authoring", "run-skill-generator"):
                rec("D", "invoke-" + sk, "sonnet", "/" + sk, [], build(), rep)


if __name__ == "__main__":
    main()
