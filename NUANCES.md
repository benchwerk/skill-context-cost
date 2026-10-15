# Nuances: what to keep in mind when quoting a number

Each item says what a number means and where it stops meaning it. Numbers are from Claude Code 2.1.284; sources are the run folders in `results/`
and the findings files named in [`RESULTS.md`](RESULTS.md).

## Token counts

- **Window total, not billing.** A count is the window total of one request (`input_tokens + cache_creation_input_tokens + cache_read_input_tokens`).
  Prompt caching changes cost and speed, not the number of tokens in the window.
- **Empty session.** 18,919 tokens on Sonnet 5.5 and 23,513 on Haiku 4.5 are the baseline of this harness (isolated configuration, 16 bundled skills,
  `--setting-sources project,local`). Another setup has another baseline. "Added" always means a configuration minus this baseline on the same model.
- **Measured against estimated.** The listing cost (21 to 403 tokens) and the invocation cost are measured for the 20 most-installed skills. The figures for the other 118 of the 138 skills are estimates: the listing from a line fitted on a synthetic length sweep (0.29 tokens per listing character plus a constant of 17 tokens per skill) and the invocation at 0.37 tokens per body character plus 50 (measured across the 20: median 0.38, pooled slope 0.40, per skill 0.28 to 0.40 for bodies over 900 characters, 1.07 and 1.30 for the two one-line bodies). Among the 20 measured skills, 3 cost 0 (manual-only) and 17 cost 21 to 403; the popular median of 135 covers 96 automatic skills (17 measured, 79 estimated) and the random median of 87 covers 36 automatic skills, all estimated. The fit predicts C10 within 4% but C50 11.7% low and R50 15.9% low; it was fitted on English text and under-counts other languages.
- **The cap.** The listing stops growing at 1,536 characters per description (tested up to 6,000) and in total at roughly 1% of the window on the 1M
  model (C50 +8,237, C100 +8,804). On Haiku the plateau is 566 to 662 tokens, which is 0.3% of 200k: the 1% figure fits the 1M model only, and the exact
  cut was not isolated.
- **Two invocation figures.** Invoking `design-taste-frontend` cost 35,199 tokens in the invocation run and 35,298 in the restructuring run (X1). The 99 tokens are the listing entry of that skill: the invocation run counts invoked minus listed, the restructuring run counts the last request minus the empty session, which includes the listing. Both are one skill, one model, repeated exactly within their run.
- **Character counts.** Counts in `results/2026-10-02_x86-laptop_invocation/invocation_findings.json` are of the stored files (CRLF counts as two characters); `analysis/skill_features.json` and the
  predictions use LF-normalised text (86,807 against 88,009 characters for `design-taste-frontend`). The slope of 0.397 tokens per character uses the
  stored counts; with LF counts it is 1.3% higher (`analysis/derived_figures.json`). `prediction.md` also quotes 87,126 and 86,805 characters for the same skill (counts made at the design stage with other frontmatter and line-ending conventions) and 9,074 for `frontend-design` (the instruction text of the delivery test, `instruction_chars` in the manifest); the analysis uses the figures above.
- **Last request of two-turn runs.** The restructure rows hold one `iterations` entry per run; the last request of the two-turn `X1-split` run (one Glob call) equals the one-turn value, which was not investigated.
- **Idle cost is not zero for an automatic skill.** An installed skill costs its listing entry (21 to 403 tokens). Only `disable-model-invocation: true`
  makes it cost nothing until you invoke it.

## Triggering

- **Four skills, one model, an empty directory.** 96% recall alone (46 of 48, interval 86% to 99%) and 77% among 50 skills (interval 64% to 87%) are
  for `playwright-best-practices`, `seo-audit`, `deploy-to-vercel` and `frontend-design`. They do not describe skills in general.
- **Shortened descriptions.** Cutting to 100 or 40 characters did no measurable harm over all positive prompts when the skill was alone; for paraphrased prompts at 40 characters harm is not excluded (-12.5 points, interval -31.0 to 3.5). In the crowd the 100-character result
  (-6.2 points, interval -23.2 to 11.2) neither shows harm nor excludes it; the pre-registered rule is not met: the lower bound (-23.2) is below the -15 criterion.
- **Print mode.** Skills do trigger in `claude -p`; that is how every run here worked.

## Quality

- **Checks, not judgement.** The 16 checks are mechanical (patterns such as em-dashes, gradient text, three equal cards). 6 never failed in any
  condition and 9 never failed without the skill, so the headroom is small: with the skill the score is 98.4%, so only about 1.6 points of further
  improvement could show. The judged stage of the quality protocol was not run, so "same quality" is never claimed, only "no difference detected".
- **Interval wording.** Q1 asked for at least +3 points and found +6.8 with an interval from 2.8 to 10.6; the lower bound is just under the criterion.
  Q2 asked for a placebo within 3 points of no skill and found -1.9 with an interval from -4.9 to 1.0. Both are reported as holding on the point estimate; the intervals cross the criteria. Under a stricter rule (the whole interval inside the criterion) Q1 and Q2 would not hold; the point-estimate reading was adopted on 2026-10-04, after the results, because their wording named no interval. The pasted run's `original_minus_none_part9` (3.13 to 10.07) uses that run's own original pages; `quality_findings.json` (2.78 to 10.59) uses the Part 9 originals.
- **The split skill.** It scored 5.4 points below the original (interval -8.5 to -2.6): within the pre-registered 10-point margin, outside the stricter
  "within 5 points" of the prediction. The model never opened a reference file in 36 runs, which is a likely explanation; it was not tested.
- **Skill against pasted text.** No difference was detected between the invoked skill and the same body pasted into the prompt (pasted +0.2, interval
  -0.7 to 1.0) on this skill and these checks. It is not evidence that the two are the same for every skill.
- **Slash invocation.** The skill conditions invoke the skill with a slash command, so the quality runs say nothing about whether a model would choose it.
- **Placebo.** The placebo matches the skill in characters, not in tokens.

- **Generated pages.** The pages in `results/*/outputs/` are verbatim model output; they contain invented business names and addresses. In four pages (`results/2026-10-03_x86-laptop_quality/outputs/039…` and `071…`, `results/2026-10-03_x86-laptop_quality_pasted/outputs/011…` and `012…`) the invented domains ending in `.pt` were replaced with `.example` on 2026-10-08; the check results of those pages are unchanged and the stored `html_chars` of those rows is 10 to 15 lower than the edited page.

## Probes and the documentation

- **"Fails" means the documentation's statement did not hold in this version,** not that a probe broke. The folder of 2026-10-02 holds only a control row; all 18 verdicts come from the run of 2026-10-03, which ran every probe from the start.
- **Precedence.** With the same skill name in the personal folder and in the project, the project skill won 3 of 3 runs for a slash-invoked skill. The
  documentation says personal over project; the CLI help says the reverse. One skill name, one way of invoking it.

## Popularity data

- **Install counts are not use.** The 20 most-installed skills were chosen by a fixed rule from a frozen snapshot of a public leaderboard. Some skills
  are manual-only already (three of the five most-installed), so install count tells little about idle cost.
- **Clone repositories.** Several repositories that copy one skill show near-identical weekly install counts; the study reports the counts of such
  groups, not the values, and does not claim the counts were manipulated.
- **Withheld values.** The ranking, install and weekly counts of individual skills are not published. The manifests in the run folders had these values
  removed after the runs, so the hash in each token-measurement `env.json` is the hash of the manifest as it was run (the trigger, quality and probe runs record no manifest hash; their prompts and briefs are identified by the hashes in their own `env.json`) (`results/manifest_hashes.json`; `alias_crowded` is the exception: its manifest was copied after the values were removed).

## Versions and the meter

- **Two Claude Code versions.** The numbers are for 2.1.284; a replication on 2.1.286 (Part 13) repeated the trigger recalls, the probe verdicts and the alias hit rates and differed in three ways. (1) A 17th bundled skill, `plugin-authoring`, is listed from the start on 2.1.286 (83 of 83 rows of the sweep) and was absent from 125 of 125 rows of the first run; it appeared in one of 72 rows of a 2.1.284 re-test, so it is not tied to the version alone. It costs about 88 tokens on Sonnet and about 60 on Haiku, which accounts for the single-call jumps of about 88 tokens (a call with it, a call without it) and for part of the larger empty session. Net of it the empty session is about 235 tokens larger on Sonnet and about 219 on Haiku (277, 279 and 323 gross in the sweep and the re-test); the rest is unexplained, and an auto-memory prompt is one unchecked candidate (the model read its `MEMORY.md` in three rows of the 2.1.286 sweep, and whether it did on 2.1.284 cannot be checked). (2) The Haiku listing cost is lower (10 skills 405 against 457 to 479, 50 skills 498 against 563 to 571, 100 skills 615 against 672) while 1 skill is unchanged (70): a fixed listing budget now shared with the extra bundled skill fits the data, but the cause is not established and the changelog of 2.1.285 and 2.1.286 states none. (3) More alias runs ended in `error_max_turns` (10 of 60 against none of 60): all ten made three tool calls (Skill, then Bash, then Glob) exploring the working directory, where no 2.1.284 run made more than two. Also unexplained: a 23-token shift of the fixed prompt between two sessions (15,598 and 15,621 tokens), which moved three small invocation configurations by exactly 23; the same 2.1.284 executable did not reproduce its own numbers exactly eight days later (Sonnet C100 8,679 and 8,752 against 8,804; Haiku C10 457 against 479); and a 73-token difference on 2.1.284 between an explicit and an unset permission mode (Sonnet C100), which does not change the empty session. Claude Code changes quickly: quote a number with its version, and with several runs.
- **The subscription meter.** Runs were stopped at a guard on the five-hour allowance and resumed after the reset; the meter is shared with any other
  use of the account. Token counts do not depend on it; the readings of the meter taken during the runs do.
