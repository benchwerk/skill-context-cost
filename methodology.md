# Methodology: skill context cost

Written 2026-10-02, before any measurement. Paragraphs and sections added after the runs are dated where they begin.

## Question

How many tokens do installed Claude Code skills add to the starting context of a session, how does that change with the
number of skills and the length of their descriptions, and what share of the context window is it?

(Added 2026-10-04.) The method below is that of the first run (token counts at the start of a session). Later parts of the study, each with its predictions
written first in `prediction.md`, measure what an invoked skill costs (Part 2), other ways to deliver the same text (Part 3), the types of skills
(Part 4), splitting a large skill (Part 5), the alias pattern (Parts 6 and 11), whether the model calls a skill on its own (Part 7), the behaviour
the documentation describes (Parts 8 and 10), whether a skill changes the quality of the output (Part 9) and whether a skill differs from the
same text pasted into the prompt (Part 12); a replication on a newer Claude Code version (Part 13); and the
starting size of a session, the listing budget, `@file` and skills written with Claude's help (Part 14). The commands of every run are in `bench/README.md`; the checks and decision rules of the quality
runs are in `quality_protocol.md`.

Later Parts measured whether a skill triggers (Part 7) and whether it helps (Part 9); sentences further down that say these were not measured describe the first run only.

**Not measured:** dollar cost of a task, MCP tools, the effect of memory files, compaction and long sessions, other agents that read the
same format, models other than Sonnet 5.5 and Haiku 4.5, Claude Code versions other than 2.1.284 and 2.1.286 (the replication on 2.1.286, added 2026-10-08, is partial), and the judged
comparison of output quality (the quality results rest on mechanical checks).

Every Part except Part 13 ran on one Claude Code version (2.1.284); the partial replication in Part 13 used 2.1.286. All runs are in an empty working directory, in an isolated configuration, on a subscription whose usage meter is
shared with any other use of the account; see the limits in `README.md`.

## Method

For each configuration, model and run, a fresh empty working directory is created whose `.claude/skills/` holds exactly
the configuration's skills. Claude Code is started there in print mode with a one-character prompt and a single turn.
The usage reported for that request is recorded, together with the list of skills Claude Code says it loaded. The
window total of a request is `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; output tokens are
reported separately. The tokens added by a configuration are its median window total minus the median of the empty
configuration (`C0`) for the same model.

| Configuration | Skills | Descriptions |
| :-- | :-- | :-- |
| C0 | 0 | none (baseline) |
| C1, C10, C50, C100 | 1, 10, 50, 100 | real popular skills; each set contains the previous one |
| R50 | 50 | real, seeded random sample of the leaderboard (comparison) |
| S10-L100, L300, L600, L1000, L1500 | 10 | synthetic, listing text of that many characters each (length sweep, kept below the cap) |
| S10-B600 | 10 | synthetic, same descriptions as S10-L600 but bodies of about 20,000 characters |
| F1 | 1 | synthetic, minimal description (probe for the fixed overhead of having any skill) |
| C50-disable | 50 | C50 with `disable-model-invocation: true` added to each skill |
| C50-trim100 | 50 | C50 with each description cut at a word boundary within 100 characters; every other key and the body unchanged |
| T1 to T5 | 1 | each of the five most-installed skills of the main list, alone |

Models: the first model has a one-million-token context window and runs every configuration; the second model runs
C0, C1, C10, C50 and C100 only. Five runs per configuration and model. Configuration order is shuffled with a fixed seed
and logged. Each run is a fresh session in a working directory that is deleted and recreated before every run (a cold start of the
command-line tool); usage is taken from the first request. The server-side prompt cache may be warm or cold and is not
controlled: the window total adds input, cache-creation and cache-read tokens, so it does not depend on cache state, and the
three fields are published separately. Billing and latency, which do depend on the cache, are not measured.

**Reported figures.** Tokens added by a configuration = median window total minus the C0 median of the same model, with
the smallest and largest single run. The share of the window is always against the window of the model that ran. The
cost of a typical popular skill is the marginal cost between C10 and C50 ((added C50 - added C10) / 40), not C1 minus
C0, which also contains the fixed overhead. A per-skill estimate is fitted from the length sweep (tokens per character of
listing text) and the probe F1; it is labelled an estimate, with its error against the measured sets and the five
single skills published. The estimate is fitted on synthetic English text, so descriptions in other languages may be
under-estimated.

**Savings.** Disabling model invocation makes a skill manual-only: it is no longer offered to the model and can only be
started by name, so the saving is not free. Shortening descriptions saves tokens, but whether a skill still triggers
when it should was not measured.

## Controls

- One machine (`x86-laptop`), one Claude Code executable (path and version in `env.json`), one working-directory layout.
- User settings, memory, MCP servers and plugins are switched off (`--setting-sources project,local`,
  `--strict-mcp-config`). The list of skills Claude Code reports is compared with the expected set on every run, so a
  leak from outside the experiment is visible in the data.
- No API key. The subscription login is used; billing environment variables are removed from the process.
- The skill sets are chosen and written to `workload/manifest.json` before any run. Skill files are hashed (sha256).

## Workload and what it favours

The real skills are the most-installed skills on the skills.sh all-time leaderboard that pass the filters below, at most
three per repository, from a snapshot taken on 2026-10-02 (withheld; the sha256 of the raw page is in `workload/manifest.json`). The selection rule is fixed before any
measurement and applied mechanically (`bench/select_popular.py`): the source must be a GitHub owner/repo; the skill must
have installs in each of the last eight weeks and at least 1,000 in the last week; skills are ordered by all-time
installs; at most three skills per source. The first 100 that can be fetched form the main list; the sets measured
are its prefixes of 1, 10, 50 and 100. A seeded random sample of 50 from rows ranked 500 or better that pass the first two filters (no per-source cap, and
some of its skills are also in the main list) is measured as a comparison; it differs from the main list in both
popularity and the cap. Skipped candidates, with reasons, are recorded in `workload/manifest.json`.

The rule was chosen after inspecting this snapshot (on the withheld snapshot, the unfiltered top 100 is 68% three publishers, and several skills
of one source show identical weekly series); it was then fixed before any measurement. Thresholds (eight weeks, 1,000
installs, cap of three) are judgement calls; the composition under other values is estimated from the fitted line.

Install counts are anonymous telemetry of a command-line installer used by many agents; they are not unique people
and they include repeated and automated installs. The ranking therefore describes what is installed through that tool,
not what is used, and not only Claude Code. Skills of one repository are installed together and carry near-identical
counts, which is why the per-source cap exists. The snapshot is one day.

Synthetic skills are used only for the description-length sweep and the body check, and are labelled synthetic
everywhere. Third-party skill files are read from local clones and are not republished; the manifest records
repository, commit, path and sha256.

## Known limits

- The format of the skill listing inside the request is not published; only what Claude Code reports is measured.
- Documentation says the listing is capped at a fraction of the context window and that descriptions are dropped
  beyond it while names are kept. The pre-cap and post-cap regions are reported separately.
- Token counts depend on the model's tokeniser. Every number carries the model and the Claude Code version.
- Prompt caching changes the bill, not the size of the context window.

Results are valid for the versions recorded in `env.json` on the date of the run.

## Popularity data and what is published (added 2026-10-04)

The most-installed skills were chosen by a fixed rule from a frozen snapshot of a public leaderboard (`bench/snapshot_popularity.py`,
`bench/select_popular.py`). The repository publishes the selection rule and the hash of the raw snapshot page, not the snapshot: the leaderboard
rank, install counts and weekly counts of individual skills are withheld (`bench/withhold_leaderboard.py` removes them from the published
files; the originals are kept privately). What is published is the study's own ordering of the selected skills (`popular_rank` in
`analysis/skill_features.json`: positions 1 to 100 for the main list, empty for the 38 random-sample skills), which follows from applying the rule to the install counts. Names, sources, commits and file hashes
of every skill used are in `workload/manifest.json`.

## Note on memory in the replication (added 2026-10-08)

The statement above that memory is switched off describes the first run. In the replication on Claude Code 2.1.286 the model read the file `MEMORY.md` of the isolated configuration in three rows of the token sweep (a Glob and a Read of its projects folder), so an auto-memory prompt was active there. The first run recorded no tool calls in its rows, so whether the same happened on 2.1.284 cannot be checked. It is one unchecked candidate for the larger empty session on 2.1.286 (see `NUANCES.md`).
