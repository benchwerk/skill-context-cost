#!/usr/bin/env python3
"""Apply the fixed selection rule to the frozen popularity snapshot and write workload/selection.json.

The rule (parameters in config.json "selection", fixed before any measurement; no keyword or publisher judgement):
  1. source must be a GitHub owner/repo (so the files can be fetched and hashed);
  2. established: installs above zero in each of the last 8 weeks, and at least 1,000 installs in the last week;
  3. order by all-time installs;
  4. at most 3 skills per source (the next-best skills of that source are skipped);
the main list is every row that passes, in that order. The comparison list is a seeded random sample of
rows ranked <= 500 that pass 1 and 2 (no cap).
Usage: python bench/select_popular.py"""
import collections, json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "bench" / "config.json").read_text(encoding="utf-8"))
SEL = CFG["selection"]


def owner_repo(src):
    m = re.fullmatch(r"([\w-]+)/([\w.-]+)", src)
    return bool(m) and "." not in m.group(1)


def established(r):
    w = r["weekly"]
    return len(w) >= SEL["weeks_required_nonzero"] and all(x > 0 for x in w[-SEL["weeks_required_nonzero"]:]) \
        and w[-1] >= SEL["min_installs_last_week"]


def main():
    snap = json.loads((ROOT / SEL["snapshot"]).read_text(encoding="utf-8"))
    rows = snap["rows"]
    drop = collections.Counter()
    pool = []
    for r in rows:
        if SEL["require_github_owner_repo"] and not owner_repo(r["source"]):
            drop["not_github_owner_repo"] += 1
        elif not established(r):
            drop["not_established"] += 1
        else:
            pool.append(r)
    per, main_list = collections.Counter(), []
    for r in pool:
        if per[r["source"]] < SEL["cap_per_source"]:
            per[r["source"]] += 1
            main_list.append(r)
        else:
            drop["over_source_cap"] += 1
    rnd_pool = [r for r in pool if r["rank"] <= SEL["random_pool_max_rank"]]
    sample = random.Random(CFG["seed"]).sample(rnd_pool, min(SEL["random_n"] + 20, len(rnd_pool)))  # +20 spares for unfetchable
    out = {"rule": SEL, "seed": CFG["seed"], "snapshot_fetched": snap["fetched"], "snapshot_raw_page_sha256": snap["raw_page_sha256"],
           "dropped_counts": dict(drop), "pool_size": len(pool), "main_candidates": main_list,
           "random_candidates": sample,
           "composition_top100_sources": collections.Counter(r["source"] for r in main_list[:100]).most_common()}
    (ROOT / "workload" / "selection.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"snapshot rows {len(rows)}; pool {len(pool)}; main candidates {len(main_list)}; dropped {dict(drop)}; "
          f"random candidates {len(sample)}")


if __name__ == "__main__":
    main()
