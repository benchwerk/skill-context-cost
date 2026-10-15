#!/usr/bin/env python3
"""Experiment X1 (splitting a monolithic skill): tokens added at the last request and which reference files the model opened.

Usage: python analysis/analyze_restructure.py results/<restructure run> results/<skills run>
The raw rows of the restructure run have no tool-call field, so the tool calls are read from the saved console streams
(results/<run>/stdout/*.jsonl, which are not published: they hold unscrubbed local paths). Only file names of reference files
are written out. Added tokens = window total of the last request minus the empty session (C0) of the same model in the skills run.
Writes restructure_findings.json."""
import collections, json, statistics as st, sys
from pathlib import Path


def tot(u):
    return sum((u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def main(run, main_run):
    run = Path(run)
    if not (run / "stdout").exists():
        sys.exit("the console streams (results/<run>/stdout/) are not published; the output of this script is restructure_findings.json in the run folder")
    rows = [json.loads(l) for l in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    base = json.loads((Path(main_run) / "findings.json").read_text(encoding="utf-8"))["models"][rows[0]["model"]]["C0_window_total"]["median"]
    by = collections.defaultdict(list)
    for r in rows:
        calls, reads = [], []
        s = run / "stdout" / f"{r['seq']:03d}_{r['config']}.jsonl"
        for line in s.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("{"):
                continue
            e = json.loads(line)
            if e.get("type") == "assistant":
                for c in (e.get("message") or {}).get("content", []) or []:
                    if c.get("type") == "tool_use":
                        calls.append(c.get("name"))
                        fp = (c.get("input") or {}).get("file_path") or (c.get("input") or {}).get("path") or ""
                        if c.get("name") == "Read":
                            reads.append(fp.replace("\\", "/").rsplit("/", 1)[-1])
        last = tot((r.get("iterations") or [r["usage"]])[-1]) - base
        by[r["config"]].append({"seq": r["seq"], "turns": r.get("num_turns"), "last_request_added_tokens": last, "tool_calls": calls, "files_read": reads})
    out = {"run": run.name, "empty_session_tokens": base, "configs": {}}
    for c, rs in sorted(by.items()):
        out["configs"][c] = {"runs": len(rs), "last_request_added_median": st.median(x["last_request_added_tokens"] for x in rs),
                             "runs_that_read_a_file": sum(1 for x in rs if x["files_read"]), "per_run": rs}
    (run / "restructure_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for c, v in out["configs"].items():
        print(c, "runs", v["runs"], "added (median)", v["last_request_added_median"], "runs that read a file", v["runs_that_read_a_file"], [x["files_read"] for x in v["per_run"]])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
