# Skills: what they cost, whether they trigger, whether they help

A measurement study of agent skills in Claude Code: how many tokens installed skills add before the first prompt, what an invoked skill
costs, how often the model calls a skill on its own, what the documented rules turn out to be in practice, and whether a skill changes the
quality of what the model writes. Every number comes from a run folder in `results/`. All runs use a Claude Pro subscription through
Claude Code; no API key is used. The subscription plan (Claude Pro) is not recorded in the run files.

**Video:** on the benchwerk YouTube channel, [@benchwerkdev](https://www.youtube.com/@benchwerkdev).

## Status

Measured 2026-10-02 to 2026-10-03 on Claude Code 2.1.284 (Sonnet 5.5 with a 1M-token window, Haiku 4.5 with 200k for the token counts).
Replicated on Claude Code 2.1.286 on 2026-10-07 and 2026-10-08 (Part 13 of [`prediction.md`](prediction.md)): the trigger recalls, all 18 probe verdicts and the alias hit rates repeat, the Sonnet token counts repeat within 3% for 63 of 66 configurations, and the Haiku listing cost is lower; the empty session is larger on 2.1.286, partly because of a new bundled skill (see [`RESULTS.md`](RESULTS.md)).
Every prediction was committed before its run (the commit times, taken from the git history, are in [`results/prediction_commits.json`](results/prediction_commits.json); the hashes can be checked only if the history is published); [`RESULTS.md`](RESULTS.md) scores each one, including the ones that failed.
[`NUANCES.md`](NUANCES.md) lists what to keep in mind when quoting a number. [`editorial_log.md`](editorial_log.md) is the dated record,
including corrections.

## What was found

| Question | Finding (Claude Code 2.1.284) | Run |
| :-- | :-- | :-- |
| What does an empty session already hold? | 18,919 tokens on Sonnet 5.5 (23,513 on Haiku 4.5), including 16 bundled skills (17 on Claude Code 2.1.286, see `NUANCES.md`) | `skills` |
| What do skill bodies cost before use? | Nothing. A synthetic skill with a 20,000-character body costs the same as one with a short body (S10-B600 and S10-L600 both add 1,909 tokens for 10 skills); a split skill's reference files are not loaded until opened (5,464 tokens invoked, against 35,298 for the whole skill) | `skills`, `restructure` |
| What does one installed skill cost? | A listing entry of 21 to 403 tokens for an automatic skill (0 for the 3 manual-only skills among the 20 most-installed); 1 skill +90, 10 skills +1,167, 50 skills +8,237, 100 skills +8,804 on the 1M model | `skills`, `invocation` |
| Is there a cap? | The listing flattens: on the 1M model after about 50 skills, on the 200k model after about 10 (C10 +479, C50 +566, C100 +662). A description stops counting at about 1,536 characters (+670 tokens at 1,536, +671 at 1,600, 3,000 and 6,000) | `skills`, `claims` |
| Can it be switched off? | `disable-model-invocation: true` adds 0 tokens (C50: +8,237 without, 0 with); cutting descriptions to 100 characters saves 76% of C50. With the flag the model can no longer call the skill by itself, and trimmed descriptions may lower the call rate in a crowd (harm is not excluded: -6.2 points, interval -23.2 to 11.2) | `skills`, `trigger` |
| What does an invoked skill cost? | About 0.4 tokens per body character; median 2,630 tokens for the 20 most-installed, largest 35,199 | `invocation` |
| Skill, CLAUDE.md or prompt? | The same 9,074 characters: 69 tokens as an idle skill, 2,855 in every session as CLAUDE.md, 0 idle and about 2,743 as a prompt used once, about 2,846 as an invoked skill | `mechanisms` |
| Does splitting a huge skill help? | Invoking one 88 KB skill cost 35,298 tokens (last request minus the empty session; the invocation run's 35,199 leaves out the skill's 99-token listing entry); split into a core and 15 reference files, 5,464 (84.5% less). The mechanical-check score fell by 5.4 points (interval -8.5 to -2.6), and the references were opened in 0 of 36 runs | `restructure`, `quality` |
| Does the model call a skill on its own? | For four skills: 96% of prompts that should trigger one when it is alone (46 of 48), 77% among 50 skills (46 or 47 of the 50 are offered to the model; 3 or 4 are manual-only, depending on the skill under test); 0 false triggers on 288 prompts; skills also trigger in `claude -p` | `trigger` |
| Does it help? | For one design skill on 12 briefs, 98.4% of mechanical checks passed with the skill against 91.7% without (+6.8 points, interval 2.8 to 10.6); a placebo of the same length scored 89.8% | `quality` |
| Skill or the same text pasted? | 98.6% pasted against 98.4% invoked (+0.2, interval -0.7 to 1.0); the invoked skill used 160 more input tokens | `quality_pasted` |
| Alias pattern (a manual skill that calls a shared one)? | The nested call fired 10 of 10 times for all three wordings, alone and among 50 skills; the alias costs about 360 tokens more than inlining | `alias`, `alias_crowded` |
| Documented rules in practice | 18 probes: `.agents/skills` is not loaded; a SKILL.md without frontmatter is not loaded; a skill beats a same-named command; the project skill won over a personal one of the same name in 3 of 3 runs | `claims` |
| How many skills do real projects commit? | Median 1 per repository, 85% have exactly one (8,827 files in 6,032 public repositories; the search is capped and partial, repositories with many skills are under-counted, and personal and plugin skills are not covered) | `analysis/census_findings.json` |

## Limits

- One model family (Sonnet 5.5 and Haiku 4.5 for tokens; Sonnet 5.5 for everything else) and two Claude Code versions, 2.1.284 and, for a partial replication, 2.1.286 (the quality run was not repeated).
- The trigger test uses four skills and an empty working directory, with no project files, CLAUDE.md or memory. Recall in a real project may differ.
- The quality test is one design skill, 12 briefs, three samples each, scored by 16 mechanical checks. The checks sit near their ceiling:
  6 of 16 never failed in any condition (9 of 16 in the no-skill baseline). The judged comparison was not run. The skill is invoked by a slash
  command in the quality runs, so they measure the content of a skill, not whether the model chooses it.
- Costs per skill are measured for 20 skills and estimated for the rest of the 138 (the listing from a line fitted on a synthetic length sweep and checked against the 20 measured skills); the estimate was fitted on English.
- The labels for the form of a skill agree with a hand-labelled sample only 46% of the time and are reported with that caveat; domain (82%)
  and clarity (86%) agree better. Install counts do not measure use.
- Compaction, long sessions and other agents that read the same file format were not tested.
- The subscription meter is shared with everything else on the account; the runs were interrupted at a guard and resumed.
- Popularity data: the repository publishes the selection rule, the hash of the snapshot and the study's own ordering of the selected skills (`popular_rank`); the leaderboard ranks, install counts and weekly counts of individual skills are withheld.

## Reproduce

See [`bench/README.md`](bench/README.md): the commands of every run and analysis, the isolation (`CLAUDE_CONFIG_DIR` must point to an
empty, logged-in configuration folder), and how to start from the published manifest (the snapshot and selection files are withheld).
Results are valid only for the Claude Code and model versions recorded in each run's `env.json`.

## Licence

Code: MIT ([`LICENSE`](LICENSE)). Data: CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)). Third-party skill files are not
redistributed; the manifest records collection, commit and sha256 for each.
