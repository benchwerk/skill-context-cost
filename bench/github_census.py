#!/usr/bin/env python3
"""Census of skills committed to public GitHub repositories (read-only search).

Searches public code for SKILL.md files under `.claude/skills/`, in file-size slices so more than one result page budget is
reached, groups the hits by repository, and reports how many skills real repositories keep and which skill names recur.
The GitHub token, if the environment variable GITHUB_TOKEN is set, is used (never printed, never written) only to lift the search rate
limit. Raw hits (third-party repository names) are kept in build/ (not published); only aggregates go to analysis/.
Limits, stated up front: GitHub caps a search at 1,000 results, ranks them by its own relevance, and indexes only part of GitHub;
the sample is therefore neither random nor complete. A repository that commits skills is not proof the skills are used.
Usage: python bench/github_census.py [--pages 10] [--max-requests 120]"""
import argparse, collections, json, os, re, statistics as st, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = None   # the token comes from the environment variable GITHUB_TOKEN (optional: it only lifts the search rate limit)
SLICES = ["<400", "400..700", "701..1000", "1001..1500", "1501..2200", "2201..3200", "3201..5000", "5001..8000", "8001..14000", "14001..30000", ">30000"]


def token():
    return os.environ.get("GITHUB_TOKEN") or None


def get(url, tok):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "benchwerk-census/1", "X-GitHub-Api-Version": "2022-11-28",
                                               **({"Authorization": f"Bearer {tok}"} if tok else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8")), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, None, dict(e.headers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=10)
    ap.add_argument("--max-requests", type=int, default=120)
    a = ap.parse_args()
    tok = token()
    print("token available:", bool(tok), flush=True)
    (ROOT / "build").mkdir(exist_ok=True)
    raw = open(ROOT / "build" / "census_raw.jsonl", "w", encoding="utf-8", newline="\n")
    seen, reqs, hits = set(), 0, []
    for sl in SLICES:
        for page in range(1, a.pages + 1):
            if reqs >= a.max_requests:
                break
            q = f"filename:SKILL.md path:.claude/skills size:{sl}"
            url = "https://api.github.com/search/code?" + urllib.parse.urlencode({"q": q, "per_page": 100, "page": page})
            status, data, hdr = get(url, tok)
            reqs += 1
            if status in (403, 429):
                wait = int(hdr.get("Retry-After", "0") or 0) or 65
                print(f"rate limited ({status}); waiting {wait}s", flush=True)
                time.sleep(wait)
                status, data, hdr = get(url, tok)
            if status != 200 or not data:
                print(f"slice {sl} page {page}: status {status}; stopping this slice", flush=True)
                break
            items = data.get("items", [])
            for it in items:
                key = (it["repository"]["full_name"], it["path"])
                if key in seen:
                    continue
                seen.add(key)
                rec = {"repo": it["repository"]["full_name"], "path": it["path"], "fork": it["repository"].get("fork"), "slice": sl}
                hits.append(rec)
                raw.write(json.dumps(rec) + "\n")
            raw.flush()
            print(f"slice {sl:>11s} page {page}: +{len(items)} (total unique {len(seen)})", flush=True)
            if len(items) < 100:
                break
            time.sleep(2.5)
    raw.close()
    # aggregate: skills per repository, recurring skill names
    per_repo = collections.defaultdict(set)
    for h in hits:
        m = re.search(r"\.claude/skills/([^/]+)/SKILL\.md$", h["path"])
        if m:
            per_repo[h["repo"]].add(m.group(1))
    counts = sorted(len(v) for v in per_repo.values())
    names = collections.Counter(n for v in per_repo.values() for n in v)
    projects = [c for c in counts if c < 30]
    out = {"hits": len(hits), "repositories": len(per_repo), "requests": reqs, "token_used": bool(tok),
           "skills_per_repository": {"median": st.median(counts) if counts else None, "mean": round(sum(counts) / len(counts), 2) if counts else None,
                                     "p90": counts[int(len(counts) * .9)] if counts else None, "max": counts[-1] if counts else None,
                                     "share_with_1": round(sum(1 for c in counts if c == 1) / len(counts), 3) if counts else None,
                                     "share_with_10_plus": round(sum(1 for c in counts if c >= 10) / len(counts), 3) if counts else None},
           "projects_under_30_skills": {"n": len(projects), "median": st.median(projects) if projects else None, "p90": projects[int(len(projects) * .9)] if projects else None},
           "most_vendored_skill_names": names.most_common(30),
           "limits": "search capped at 1,000 results per slice, ranked by GitHub, partial index; a committed skill is not a used skill"}
    (ROOT / "analysis" / "census_findings.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "most_vendored_skill_names"}, indent=1))
    print("top names:", out["most_vendored_skill_names"][:15])


if __name__ == "__main__":
    main()
