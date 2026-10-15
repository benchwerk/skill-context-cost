#!/usr/bin/env python3
"""Build the replay file for the video's terminal scene from the real /context recordings (footage shots 2, 3 and 6).

Usage: python bench/footage_replay.py
Reads results/footage/ctx_<config>.jsonl (made by record_console.py + footage_context.py) and writes
  results/footage/ctx_replay.jsonl       same event format as the Shorts demo recordings: one object per output line
                                         {"cmd": i, "t": seconds since the command started, "line": text} and {"cmd": i, "exit": code, "t": duration}
  results/footage/ctx_replay_commands.txt  the command line typed for each cmd index (what was really run)
  results/footage/ctx_replay_env.json      shot list (config, model, skills installed, date), source hashes, what was changed
Owner decision (2026-10-03): the video shows a reconstructed terminal, not a screen capture of the interactive session. What is
reconstructed is only the window and the typing; every output line and its timing is the real output of `claude -p "/context"`.
The only change to a recording is dropping its first line, which our wrapper prints (config id and model), not Claude Code."""
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOOT = ROOT / "results" / "footage"
SHOTS = [("C0", "claude-sonnet-5-5[1m]"), ("C10", "claude-sonnet-5-5[1m]"), ("C50", "claude-sonnet-5-5[1m]"), ("C100", "claude-sonnet-5-5[1m]"),
         ("C50-disable", "claude-sonnet-5-5[1m]"), ("C100_haiku", "claude-haiku-4-5-20251001")]


def main():
    out, cmds, shots = [], [], []
    for i, (name, model) in enumerate(SHOTS):
        src = FOOT / f"ctx_{name}.jsonl"
        env = json.loads((FOOT / f"ctx_{name}_env.json").read_text(encoding="utf-8"))
        ev = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert ev[0]["line"].startswith("config "), f"{name}: first line is not the wrapper header"
        body = [e for e in ev[1:] if "line" in e]
        end = next(e for e in ev if "exit" in e)
        first_out = body[0]["t"]
        for e in body:   # rebase so the clock starts at the first Claude Code output line; the gaps between lines are unchanged
            out.append({"cmd": i, "t": round(e["t"] - first_out, 3), "line": e["line"]})
        out.append({"cmd": i, "exit": end["exit"], "t": round(end["t"] - first_out, 3)})
        cmds.append('claude -p "/context"' + ("" if model.startswith("claude-sonnet") else f" --model {model}"))
        shots.append({"cmd": i, "config": name.split("_")[0], "model": model, "skills_in_project": int(re.search(r"(\d+) skills in the project", ev[0]["line"]).group(1)), "recorded": env["date"],
            "source": src.name, "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest()})
    (FOOT / "ctx_replay.jsonl").write_text("".join(json.dumps(e) + "\n" for e in out), encoding="utf-8", newline="\n")
    (FOOT / "ctx_replay_commands.txt").write_text("\n".join(cmds) + "\n", encoding="utf-8", newline="\n")
    (FOOT / "ctx_replay_env.json").write_text(json.dumps({
        "what": "real output of Claude Code /context in print mode, replayed in a drawn terminal window (decision 2026-10-03)",
        "changed": "first line of each recording dropped (printed by the wrapper); clock rebased to the first output line; nothing else",
        "shots": shots}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(SHOTS)} shots, {len(out)} events -> results/footage/ctx_replay.jsonl")


if __name__ == "__main__":
    main()
