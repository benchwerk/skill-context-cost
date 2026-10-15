#!/usr/bin/env python3
"""Freeze a dated snapshot of the public skills.sh all-time leaderboard into workload/popularity_snapshot.json.

The skills.sh home page embeds the first 600 leaderboard rows (source, skill, all-time installs, last eight weekly
installs). This script fetches the page once, stores the parsed rows and the sha256 of the raw page, and never
overwrites an existing snapshot. The API needs a Vercel project token and is not used.
Usage: python bench/snapshot_popularity.py"""
import datetime, hashlib, json, re, sys, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "workload" / "popularity_snapshot.json"
URL = "https://skills.sh/"


def main():
    if OUT.exists():
        sys.exit(f"{OUT.name} exists: a snapshot is never overwritten (it is the frozen selection input)")
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "benchwerk-snapshot/1"}), timeout=60).read()
    (OUT.parent / "src").mkdir(exist_ok=True)
    (OUT.parent / "src" / f"skills_sh_raw_{datetime.date.today().isoformat()}.html").write_bytes(raw)   # kept locally, not published
    text = raw.decode("utf-8").replace("\\", "")
    pat = re.compile(r'"source":"([^"]+)","skillId":"([^"]+)","name":"([^"]+)","installs":(\d+),"weeklyInstalls":\[([\d,]*)\]')
    rows = []
    for m in pat.finditer(text):
        rows.append({"rank": len(rows) + 1, "source": m.group(1), "skill": m.group(2), "name": m.group(3),
                     "installs": int(m.group(4)), "weekly": [int(x) for x in m.group(5).split(",") if x]})
    seen, uniq = set(), []
    for r in rows:
        k = (r["source"], r["skill"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    for i, r in enumerate(uniq):
        r["rank"] = i + 1
    snap = {"source_url": URL, "fetched": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "raw_page_sha256": hashlib.sha256(raw).hexdigest(), "view": "all-time", "rows_parsed": len(rows),
            "rows_unique": len(uniq), "rows": uniq}
    OUT.write_text(json.dumps(snap, indent=1) + "\n", encoding="utf-8")
    print(f"{len(uniq)} rows -> {OUT}")


if __name__ == "__main__":
    main()
