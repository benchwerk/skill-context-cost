# Harness: skill context cost

Measures how many tokens installed skills add to the start of a Claude Code session. Standard-library Python 3 and
git; Claude Code logged in with a subscription. No API key is used or needed.

```bash
python bench/snapshot_popularity.py # freeze the skills.sh leaderboard (once; never overwritten)
python bench/select_popular.py      # apply the fixed selection rule -> workload/selection.json
python bench/fetch_skills.py        # shallow-clone the selected repositories into workload/src/ (local only)
python bench/build_workload.py      # resolve skills to files, write workload/manifest.json
python bench/run.py --dry-run       # build the plan and working directories, call nothing
python bench/run.py --only C0,C10 --runs 1    # smoke test
python bench/run.py                 # the full plan -> results/<date>_<machine>_skills/
python analysis/analyze.py results/<run>      # -> findings.json
```

Isolation: `CLAUDE_CONFIG_DIR` must point to an empty directory in which Claude Code is logged in once with the
subscription (`run.py` refuses to run without it, or with the default `~/.claude`), so the user's own skills, memory and
settings cannot enter a run. Each run uses the same fixed working directory (`workdir_root` in the config, recreated
before every run) so that the path in the system prompt is identical. Every run records the skills and tools Claude Code
reports; the analysis excludes runs whose reported skills differ from the expected set. Paths and the user name are
scrubbed from everything written outside `results/*/stdout/`, which is not published.

Pin the Claude Code version by pointing `CLAUDE_BIN` at the executable; the version and path are recorded in
`env.json`. Models are set in `bench/config.json`. `run.py` refuses to start while placeholders remain in the config.

## What `run.py` does for each run

1. Builds a fresh empty working directory (not a git repository) whose `.claude/skills/` holds exactly the
   configuration's skills.
2. Starts `claude -p "x" --output-format stream-json --verbose --max-turns 1 --model <model> --setting-sources
   project,local --strict-mcp-config --no-session-persistence` there, with `ANTHROPIC_API_KEY` and similar variables
   removed from the environment.
3. Stores the raw output (`stdout/`), the skills Claude Code reports having loaded (compared against the expected set:
   `unexpected_skills`, `missing_skills`) and the usage of the single request (`raw.jsonl`).

Configuration order is shuffled with a fixed seed and logged in `plan.json`, so configurations are interleaved in time.

## Files

| Path | Role |
| :-- | :-- |
| `bench/config.json` | models, run count, seed, selection rule parameters |
| `bench/snapshot_popularity.py` | freezes the popularity ranking (skills.sh) with a hash of the raw page |
| `bench/select_popular.py` | applies the selection rule to the snapshot |
| `bench/fetch_skills.py` | clones the selected repositories, records each commit |
| `bench/build_workload.py` | resolves skills to files, builds nested real sets, the random set and the labelled synthetic sets |
| `bench/run.py` | the measurement |
| `analysis/analyze.py` | medians, spread, added tokens against the empty baseline, window shares |
| `workload/manifest.json` | every skill used: collection, commit, path, sha256, description length |

## Footage

`python bench/record_console.py <name> -- <command>` records a command's console output as timestamped, scrubbed evidence
(`results/footage/<name>.jsonl`); `python bench/prepare_workdir.py <config>` builds the working directory of one
configuration so a session can be screen-recorded there.

## Every run and its analysis

Set the environment first (Git Bash; on Windows `workdir_root` in `bench/config.json` is `C:\skillctx`, change it on another machine):

```bash
export CLAUDE_BIN=<path to the pinned claude executable>      # the version is recorded in env.json
export CLAUDE_CONFIG_DIR=<an empty folder in which Claude Code is logged in once with a subscription>
```

| Run folder (`results/<date>_<machine>_<experiment>`) | Command | Analysis |
| :-- | :-- | :-- |
| `skills` (125 calls) | `python bench/run.py --experiment skills` | `python analysis/analyze.py results/<skills run>` |
| `invocation` (40) | `python bench/run.py --experiment invocation --runs 1 --only I1,I2,I3,I4,I5,I6,I7,I8,I9,I10,I11,I12,I13,I14,I15,I16,I17,I18,I19,I20,L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12,L13,L14,L15,L16,L17,L18,L19,L20` | `python analysis/analyze_invocation.py results/<invocation run> results/<skills run>` |
| `mechanisms` (14) | `python bench/run.py --experiment mechanisms --runs 2 --only M-base,M-skill-idle,M-skill-used,M-claudemd,M-prompt-used,M-docs-idle,M-docs-used` | `python analysis/analyze_mechanisms.py results/<mechanisms run>` |
| `restructure` (6) | `python bench/run.py --experiment restructure --runs 2 --only X1-orig,X1-split,X1-split-read` | `python analysis/analyze_restructure.py results/<restructure run> results/<skills run>` (reads the saved console streams, which are not published; the published output is `restructure_findings.json`) |
| `alias` (50) | `python bench/run.py --experiment alias --runs 10 --only G-original,G-slash,G-prose,G-inline,G-direct` | `python analysis/analyze_alias.py results/<alias run> results/<skills run>` |
| `alias_crowded` (30) | `python bench/run.py --experiment alias_crowded --runs 10 --only G2-original,G2-slash,G2-prose` | `python analysis/analyze_alias.py results/<alias_crowded run> results/<skills run>` |
| `trigger` (576) | `python bench/trigger_test.py --runs 3` | `python analysis/analyze_trigger.py results/<trigger run>` |
| `claims` (probes) | `python bench/claim_probes.py` | `findings.json` is written by the probe script |
| `quality` (144) | `python bench/quality_run.py --samples 3` | `python analysis/analyze_quality.py results/<quality run>` |
| `replication_skills` (83), `replication_trigger` (576), `replication_claims` (18), `replication_alias` (60) | Claude Code 2.1.286 (`CLAUDE_BIN`): `python bench/run.py --runs 1 --experiment replication_skills`; `python bench/trigger_test.py --runs 3 --experiment replication_trigger`; `python bench/claim_probes.py --experiment replication_claims`; `python bench/run.py --only G-original,G-slash,G-prose,G2-original,G2-slash,G2-prose --runs 10 --experiment replication_alias` | `python analysis/analyze_replication.py --alias 2026-10-08_x86-laptop_replication_alias` (without `--alias` V4 is not computed) |
| `v1check_<version>_<default or notset>` (36 each) | both executables via `CLAUDE_BIN`: `python bench/run.py --runs 2 --only C0,C1,C10,C50,C100,C50-disable,F1,I2,L2,I3,L3,I10,L10 --experiment v1check_<version>_<mode> [--permission-mode default]` | `python analysis/analyze_v1check.py` |
| `quality_pasted` (72) | `python bench/quality_run.py --conds pasted,original --samples 3 --experiment quality_pasted` | `python analysis/analyze_pasted.py results/<pasted run> results/<quality run>` |

Long runs stop when the five-hour allowance reaches the guard (`--stop-at`) and continue with `--resume <results folder>`;
`python bench/supervisor.py <name> -- <command>` does this unattended. A resume needs the same Claude Code version and,
for `run.py`, the same manifest. Further analyses: `analysis/analyze_types.py <skills run> <invocation run>` (types of skills),
`bench/skill_anatomy.py` (features of the 138 skill files), `analysis/derived_figures.py` (label agreement, the slope with LF counts, descriptive medians), `bench/github_census.py` and `analysis/analyze_claims_offline.py`
(census and offline claims; these need the network, optionally a `GITHUB_TOKEN` in the environment to lift the search rate limit, or the withheld popularity snapshot).

## Starting from the published manifest

The popularity snapshot and the selection files are withheld (the study publishes the selection rule and the hash of the
snapshot, not the ranking), so `snapshot_popularity.py`, `select_popular.py` and `build_workload.py` cannot be repeated from
this repository. To rerun the measurements, use `workload/manifest.json` as it is and run `python bench/fetch_pinned.py`: it fetches each repository named in
`workload/fetched.json` at the recorded commit into `workload/src/<owner>__<repo>/` and checks the `sha256` of every skill file against the manifest
(it prints how many match; all 152 manifest entries matched when checked on 2026-10-04, some skills appear in more than one set); then run the commands above. The
`manifest_sha256` stored in each run's `env.json` is the hash of the manifest as it was run; the published manifests had
their rank and install values removed afterwards, so the hashes differ (`results/manifest_hashes.json`).

The raw rows of the trigger and quality runs were written before the later edits to `trigger_test.py` and `quality_run.py`; a new run writes extra fields (for example `first_request_usage`, `usage`).
