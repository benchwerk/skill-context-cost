# Results: every prediction against its outcome

Claude Code 2.1.284, measured 2026-10-02 to 2026-10-03 (Part 13: Claude Code 2.1.286, 2026-10-07 and 2026-10-08) (Sonnet 5.5 with a 1M window, Haiku 4.5 with 200k for the token counts). One row per
labelled prediction in [`prediction.md`](prediction.md); every Part was written and committed before its run. The result column quotes the
findings file named in the last column. `met?` is judged against the criterion the prediction itself set: holds = every clause is met (a point estimate that meets its criterion counts, and the row says when its interval crosses the criterion); fails = at least one clause is contradicted by the data; partly = no clause is contradicted but at least one could not be tested; inconclusive = the data cannot decide; not run. The rule that a point estimate which meets its criterion counts was adopted on 2026-10-04, after the results; under a rule that requires the whole interval inside the criterion, Q1 and Q2 would not hold. Failed predictions are kept: they are results.

Part numbers follow `prediction.md`. Part 1 hypotheses are written H1 to H13 here; Part 4 and later keep their own ids.

## Part 1: Hypotheses 1 to 13 (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| H1 | Plateau reached before N=100 on 200k window and later (or not at all) on 1M window | The 200k window is flat by C10 (479, then 566 at C50); the 1M window flattens after C50 (8,237, then 8,804 at C100): later than on 200k, and before N = 100 on both; the clause that descriptions are dropped while names stay was not tested; on Haiku C10 to C50 adds only 87 tokens for 39 more visible skills (about 2.2 per skill, less than a name costs) | partly | results/2026-10-02_x86-laptop_skills/findings.json |
| H2 | Per-skill cost 50 to 150 tokens; names alone under 25 tokens | Typical skill 176.75 tokens; a minimal one-skill entry (F1) added 21 tokens | fails | results/2026-10-02_x86-laptop_skills/findings.json |
| H3 | 50 real skills cost 2000 to 7000 tokens; plateau below 5000 | 1M C50 added 8237 tokens (0.8%); 200k C50 added 566 tokens; plateau > 8000 on 1M | fails | results/2026-10-02_x86-laptop_skills/findings.json |
| H4 | Long descriptions (1500 chars) cost at least 5x short (100 chars) | S10-L1500 (4535) is 9.79x S10-L100 (463) | holds | results/2026-10-02_x86-laptop_skills/findings.json |
| H5 | Small in window share, number not zero, tail invisible | 1M C50 added share 0.008; 200k share 0.0028; cap_suspected is true; the claim that the tail is invisible to the model was not tested (`cap_suspected` is a flag, not evidence) | partly | results/2026-10-02_x86-laptop_skills/findings.json |
| H6 | Newer tokeniser costs 20-40% higher than older one | Only C1 lies below both caps (+28.6%, a 20-token difference); C10 differs by +144% but the Haiku set is already flat there, so the comparison is not a pure tokeniser test | partly | results/2026-10-02_x86-laptop_skills/findings.json |
| H7 | 20,000-character bodies add same tokens as mid within 2% | S10-B600 and S10-L600 both added exactly 1909 tokens | holds | results/2026-10-02_x86-laptop_skills/findings.json |
| H8 | Cost linear in description characters; fitted error under 10% | Slope 0.291 tokens per listing character (inside 0.2 to 0.35); fit error +3.9% at C10, -11.7% at C50 and -15.9% at R50 (over 10%), +66% at C100 (beyond the cap); the error clause failed on 2 of the 3 real sets below the cap | fails | results/2026-10-02_x86-laptop_skills/findings.json |
| H9 | disable-model-invocation saves at least 80% of C50 addition | C50-disable added 0 tokens (saved 100% of 8237) | holds | results/2026-10-02_x86-laptop_skills/findings.json |
| H10 | Trimming descriptions to 100 chars saves at least 30% of C50 addition | C50-trim100 saved 6281 tokens (76.2% of 8237) | holds | results/2026-10-02_x86-laptop_skills/findings.json |
| H11 | Individual estimates within 20% of measured for at least 4 of 5 skills | Within 20% for T1 and T5, but misses widely for T2, T3, and T4; all three misses are manual-only skills, which the estimator ignores | fails | results/2026-10-02_x86-laptop_skills/findings.json |
| H12 | Popular skills not cheaper than average; R50 adds 0.6 to 1.6 times C50 | R50 added 7184, C50 added 8237; ratio is 0.87 | holds | results/2026-10-02_x86-laptop_skills/findings.json |
| H13 | Longest description is at least 5x the median length | Max listing chars 1017, median 314.5; ratio is 3.2x; the prediction named the top 100, the result uses all 138 skills; on the predicted top 100 only: 1,017 / 402 = 2.5 times | fails | analysis/offline_claims_findings.json |

## Part 2: Invocation cost (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| I1 | By hand adds 0.20 to 0.35 tokens per character of body | Tokens per body char is 0.397 (r2 = 0.995) | fails | results/2026-10-02_x86-laptop_invocation/invocation_findings.json |
| I2 | Fixed overhead of an invocation is under 150 tokens | Invoking the 40-character `grill-me` adds 52 tokens in total (invoked minus listed, the body included), so the overhead is at most 52; the regression intercept (-335) is not usable | holds | results/2026-10-02_x86-laptop_invocation/invocation_findings.json |
| I3 | Median body 2000-10000 chars (adds 500-2700 tokens); at least one > 5000 | Median 6773.5 chars (2630 tokens); max invocation 35199 tokens | holds | results/2026-10-02_x86-laptop_invocation/invocation_findings.json |
| I4 | Listing entry repays one invocation after median 3 to 30 sessions | Median invocations to equal listing is 23.3 | holds | results/2026-10-02_x86-laptop_invocation/invocation_findings.json |
| I5 | Manual-only cost the same per invocation as automatic of same body size | Manual-only skills fit the same pooled line (r2 = 0.995), but only one manual-only skill (`improve-codebase-architecture`) has a body large enough to matter (n = 1) | partly | results/2026-10-02_x86-laptop_invocation/invocation_findings.json |

## Part 3: Delivery mechanisms (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| M1 | CLAUDE.md holding the text adds 2500 to 3100 tokens | CLAUDE.md added 2855 tokens | holds | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |
| M2 | Skill invoked and pasted prompt each within 150 tokens of CLAUDE.md | Skill added 2,846 (9 below CLAUDE.md), prompt added 2,743 (112 below CLAUDE.md, not a few above as predicted): both within 150 | fails | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |
| M3 | Listed but not used skill adds under 100 tokens | Idle skill added 69 tokens; 69 was already known before the prediction, from the probe quoted in its preamble | holds | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |
| M4 | Pointer-only CLAUDE.md adds under 100 tokens | Idle file pointer added 150 tokens | fails | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |
| M5 | File read context within 15% of CLAUDE.md + 300; read in >= 1 run | File read added 3157; read in 2 of 2 runs | holds | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |
| M6 | Expected cost per session depends on rate; sizes decide crossings | skill_vs_file_pointer_p is -0.35 (skill always cheaper) | inconclusive | results/2026-10-02_x86-laptop_mechanisms/mechanism_findings.json |

## Part 4: Anatomy and types of skills (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| T1 | Platform-reference and tool-operation skills >= 40% of the 138 | D3 (0.261) and D4 (0.094) total 35.5% | fails | analysis/type_findings.json |
| T2 | Persona/mode and stub-pointer have smallest bodies, under 3000 chars | F2 and F4 do not have the largest median body (F5's 9,750.5 characters is the largest; fails); F6 median body 1,744.5 characters, under 3,000 (holds); F5 is not under 3,000 (fails); the form labels agree with the hand labels only 46% of the time | fails | analysis/type_findings.json |
| T3 | Deferred share is highest for platform-reference (D3) skills | D3 deferred share is 0.815, highest among domains | holds | analysis/type_findings.json |
| T4 | >= 60% score 3 for clarity, with longer median descriptions | 69.6% (96/138) score 3; median 509.5 chars vs 64 and 201 | holds | analysis/type_findings.json |
| T5 | Agreement with manual sample >= 70% domain and >= 60% form | Agreement with the manual sample is 82% on domain (held) and 46% on form (failed); both were required | fails | analysis/derived_figures.json |
| T6 | Invocation cost of reference skills >= 3x rules-and-style skills | F2 invocation 3443, F3 invocation 2439.5 (ratio 1.4x); the form labels agree with the hand labels only 46% of the time; the first clause (invocation differs more between forms than listing does) holds: 5.3 times against 1.75 times | fails | analysis/type_findings.json |

## Part 5: Building a skill efficiently: experiment X1 (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| X1a | Split version invoked adds 4000-6000 tokens, >= 80% less than original | Original 35298, split 5464 tokens (84.5% less) | holds | results/2026-10-02_x86-laptop_restructure/restructure_findings.json |
| X1b | Split-and-read last request context is 8000 to 11500 tokens | Last request is 10623 tokens above empty session | holds | results/2026-10-02_x86-laptop_restructure/restructure_findings.json |
| X1c | Model opens reference file in >= 1 of 2 runs, correct one >= 1 | Opened intended reference file in 2 of 2 runs | holds | results/2026-10-02_x86-laptop_restructure/restructure_findings.json |
| X1d | Listing cost is unchanged | Listing was not measured separately | not run | editorial_log.md |

## Part 6: The alias pattern (2026-10-02)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| A1 | Original wording calls nested skill in >= 9 of 10 runs | Called nested skill in 10 of 10 runs (hit_rate 1.0, 95ci 0.72-1.0) | holds | results/2026-10-02_x86-laptop_alias/alias_findings.json |
| A2 | Original hit rate is >= 20 points above 'Run /grilling.' | Both were 10 of 10 (0 points difference) | fails | results/2026-10-02_x86-laptop_alias/alias_findings.json |
| A3 | Hit rate of prose wording lies between the other two | All three wordings were 10 of 10 | inconclusive | results/2026-10-02_x86-laptop_alias/alias_findings.json |
| A4 | Alias flow last request within 600 tokens of inline version | Alias flow ends 361.5 tokens above inline | holds | results/2026-10-02_x86-laptop_alias/alias_findings.json |
| A5 | Typing /grilling directly costs within 150 tokens of inline | Direct costs 58.0 tokens above inline | holds | results/2026-10-02_x86-laptop_alias/alias_findings.json |
| A6 | Listing cost of having both installed equals 'grilling' alone | Not measured separately; inferred from `grill-me` costing 0 alone (T2, L2), not measured as a pair | not run | editorial_log.md |

## Part 7, trigger test (2026-10-02)

| id | prediction | result | met? | evidence |
| :--- | :--- | :--- | :--- | :--- |
| TR1 | Original description alone: called on >=85% keyword, fewer paraphrase by >=10pp, <=5% unrelated | Keyword prompts 91.7% (held) and unrelated prompts 0% (held); paraphrases triggered more, not less, 100% against 91.7% (failed) | fails | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR2 | Over all positive prompts with original alone, called >=70% | 95.8% [0.86, 0.988] | holds | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR3 | Trigger in print mode recall is above 0 | 96% of prompts that should trigger the skill when it is alone (46 of 48) and 77% among 50 skills; 236 calls of the target skill in 576 runs, all in print mode | holds | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR4 | 100-char within 15pp of original; 40-char lowers paraphrase by >=15pp but keeps keyword within 15pp | 100 characters: -2.1 points, interval -13.1 to 8.5 (held); 40 characters: paraphrase drop -12.5 points, interval -31.0 to 3.5, against a predicted drop of 15 or more (failed); crowded setting (50 skills): 100 characters -6.2 points (interval -23.2 to 11.2), 40 characters -16.7 (-33.7 to 1.9); the 100-character interval does not exclude harm | fails | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR5 | Among 50 skills, call rate is lower than alone by 0 to 25 points on positive prompts | Original -18.8 points (interval -32.7 to -5.0) and 100 characters -22.9 (-37.5 to -7.7) are inside 0 to 25; 40 characters -33.3 (-48.0 to -16.9) is beyond it. Intervals of the first two extend past 25 | fails | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR6 | >=60% of calls on unrelated or near-miss prompts occur on near-miss | 0 false triggers | inconclusive | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |
| TR7 | Over three runs, at least one prompt-and-variant cell gives different outcomes | 11 cells had mixed outcomes | holds | results/2026-10-02_x86-laptop_trigger/trigger_findings.json |

## Part 8, claim probes (run 2026-10-03; one probe per documented claim, expectation written first)

| probe | claim | expected (from the documentation) | observed | verdict |
| :-- | :-- | :-- | :-- | :-- |
| P-01 | C-031 | Claude Code: loads, named after its directory (the open spec calls frontmatter required) | skills beyond bundled: [] | fails |
| P-02 | C-090 | spec: name must match the directory; client guidance: load leniently (either name may appear) | skills beyond bundled: ['dirname-a'] | holds |
| P-03 | C-068 | platform docs: forbidden; Claude Code docs reserve only anthropic-skills and synced (claim = not loaded) | skills beyond bundled: ['claude-helper'] | fails |
| P-04 | C-004, C-069, K-030 | the listing cap is 1,536 characters: tokens grow until about 1,536 characters and then stop (the spec says 1,024; an old issue says 250) | 500ch:+220, 1000ch:+437, 1100ch:+480, 1536ch:+670, 1600ch:+671, 3000ch:+671, 6000ch:+671; is within 1 token of the maximum at 1,536 characters | holds |
| P-05 | C-045 | true, True, YES, yes, 1, on all hide the skill from the model (listing cost 0); false does not | true:+0, True:+0, YES:+0, yes:+0, 1:+0, on:+0, false:+21 | holds |
| P-06 | C-047 | accepted but ignored: the skill still loads | skills beyond bundled: ['optfields'] | holds |
| P-07 | K-010 | both load and cost the same (the claim of a broken loader concerns reflowed files) | single +27, block +27; listed: ['blk'] | holds |
| P-08 | C-025 | the skill wins (the reply contains SKILLVERSION) | reply: 'SKILLVERSION' | holds |
| P-10 | C-021 | not listed at start; loads only when a file in that subdirectory is read | skills beyond bundled: []; (tested at start only); `findings.json` says holds; the second clause of the expectation was not tested | partly |
| P-11a | C-022 | parent .claude/skills is found up to the repository root | skills beyond bundled: ['upskill']; `findings.json` says holds; the second clause of the expectation was not tested | partly |
| P-11b | C-022 | parent .claude/skills is found up to the repository root | skills beyond bundled: ['upskill']; `findings.json` says holds; the second clause of the expectation was not tested | partly |
| P-12 | C-040 | a skill with paths: ['**/*.py'] is not offered to the model until a matching file is touched (listing cost about 0) | added tokens 0; (tested at start only); `findings.json` says holds; the second clause of the expectation was not tested | partly |
| P-13 | C-108 | client guidance: a widely adopted location; Claude Code docs list only .claude/skills (either result is informative) | skills beyond bundled: [] | fails |
| P-14 | C-044 | $ARGUMENTS = all arguments, $0 and $1 the first two; a missing positional ($2) stays literal | reply: 'A=alpha beta|F=alpha|S=beta|T=$2' | holds |
| P-15a | C-042 | the output replaces the placeholder (the reply contains INJECTED_OK_42) | reply: 'INJECTED_OK_42' | holds |
| P-15b | C-042 | the whole invocation aborts (no normal reply) | reply: '' | holds |
| P-17 | C-032 | with the flag the model never calls the skill; without it, it does | Skill calls: with flag 0/3, without 3/3 | holds |
| P-09 | C-024 | documentation: personal over project (the CLI help calls project over user the universal convention); reply names the winner | winners over 3 runs: ['PROJECT', 'PROJECT', 'PROJECT'] | fails |

A verdict of "fails" means the documented statement did not hold in Claude Code 2.1.284, not that the probe broke.

## Part 9, output quality of the design skill (2026-10-03)

| id | prediction | result | met? | evidence |
| :--- | :--- | :--- | :--- | :--- |
| Q1 | Original skill raises mean score over none by at least 3 percentage points | +6.77 points, interval 2.78 to 10.59: the point estimate meets the 3-point criterion; the lower bound is just below it; (rule set after the results) | holds | results/2026-10-03_x86-laptop_quality/quality_findings.json |
| Q2 | Placebo is within 3 points of none | -1.91 points, interval -4.86 to 1.04: the point estimate is within 3 points; the interval extends past -3; (rule set after the results) | holds | results/2026-10-03_x86-laptop_quality/quality_findings.json |
| Q3 | Split is within 5 points of original (not worse if lower bound above -10) | -5.38 points, interval -8.51 to -2.60: inside the fixed 10-point margin, outside the prediction's 'within 5 points'; a decrease is detected; the verdict label was set after an interim look at 74 pages (see amendments) | fails | results/2026-10-03_x86-laptop_quality/quality_findings.json |
| Q4 | Model opens a reference file in fewer than 25% of split runs | 0.0% (0 of 36 runs) | holds | results/2026-10-03_x86-laptop_quality/quality_findings.json |
| Q5 | Em-dashes in >= 25% of pages without skill, fewer with original skill | none: 61.1%, original: 0.0% | holds | results/2026-10-03_x86-laptop_quality/quality_findings.json |

## Part 10: precedence probe P-09 (2026-10-03)

| id | prediction | result | met? | evidence |
| :--- | :--- | :--- | :--- | :--- |
| P-09 | Personal skill wins in 3 of 3 runs | Project won 3 of 3 runs | fails | results/2026-10-03_x86-laptop_claims/findings.json |

## Part 11: The alias pattern in a crowded session (2026-10-03)

| id | prediction | result | met? | evidence |
|---|---|---|---|---|
| B1 | Each wording calls nested skill in >= 9 of 10 runs | 10 of 10 for all three wordings (hit_rate 1.0, 95ci 0.72-1.0) | holds | results/2026-10-03_x86-laptop_alias_crowded/alias_findings.json |
| B2 | Gap between original and 'Run /grilling.' under 20 points | Both were 10 of 10 (0 points difference) | holds | results/2026-10-03_x86-laptop_alias_crowded/alias_findings.json |
| B3 | No wording loses more than 10 points against empty-session result | All remained 10 of 10 (0 points loss) | holds | results/2026-10-03_x86-laptop_alias_crowded/alias_findings.json |

## Part 12: the skill against the same text pasted into the prompt (2026-10-03)

| id | prediction | result | met? | evidence |
| :--- | :--- | :--- | :--- | :--- |
| R1 | Mean score of pasted is within 3pp of original, interval includes 0 | +0.17pp [-0.69, 1.04] | holds | results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json |
| R2 | Pasted is at least 3pp above none of Part 9 (interval above 0) | +6.94pp [3.30, 10.24] | holds | results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json |
| R3 | Median input of original exceeds pasted by 0 to 250 tokens | 160.5 tokens | holds | results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json |
| R4 | Pasted runs take one turn and open no file | Median 1.0 turn, 0 tool calls | holds | results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json |
| R5 | Original is within 5 points of 98.4% (its score in Part 9) | 98.44%, diff 0.0pp [-1.04, 1.04] | holds | results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json |

## Part 13: replication on Claude Code 2.1.286 (run 2026-10-07 and 2026-10-08)

Same machine and isolated configuration, Claude Code 2.1.286 (the first run used 2.1.284). Run folders `2026-10-07_x86-laptop_replication_skills` (one run per configuration, 83 calls),
`2026-10-07_x86-laptop_replication_trigger` (576 calls), `2026-10-08_x86-laptop_replication_claims` (18 probes) and `2026-10-08_x86-laptop_replication_alias` (60 calls, 10 per wording,
started after the main sweep because that made one call per wording); compared with `analysis/analyze_replication.py`, output `results/replication_findings.json`.

| id | prediction | result | met? |
| :-- | :-- | :-- | :-- |
| V1 | Added tokens equal the 2.1.284 values within 3% (the empty session may move) | Replication sweep (one run per configuration): the empty session grew by 277 tokens on Sonnet (18,919 to 19,196, +1.5%) and by 279 on Haiku (23,513 to 23,792). Sonnet: 63 of 66 configurations within 3% (the three outside, I2, I3 and I10, each differ by exactly 23 tokens, a shift of the fixed prompt between the two sessions, cause unknown; in a controlled re-test with two runs they are identical on both versions; the 66 configurations include some that V1 did not name: the S10 sets, R50, T1 to T5, F1 and C50-trim100). Haiku: 1 of 4 within 3%; C10 479 to 405 (-15%), C50 566 to 488 (-14%), C100 662 to 616 (-7%); a controlled re-test confirms the lower Haiku listing cost on 2.1.286 (C10 457 to 479 against 405, C50 563 to 571 against 498, C100 672 against 615) | fails (the Haiku listing cost changed; the Sonnet headline numbers replicate) |
| V2 | Trigger test: recall within 10 points of 96% alone and 77% among 50 skills; 0 false triggers on 288 prompts | alone 45 of 48 (93.8%, interval 83.2% to 97.9%) against 46 of 48; among 50 skills 34 of 48 (70.8%, 56.8% to 81.8%) against 37 of 48; 0 false triggers; mixed-outcome cells 7 of 192 (11 before) | holds |
| V3 | Every probe verdict equals the 2.1.284 verdict | 18 of 18 identical, including P-09 (the project skill wins over the personal one) | holds |
| V4 | Alias test: the nested call fires 10 of 10 for all three wordings, empty and crowded | 10 of 10 in all six cells | holds |

Differences worth knowing, none of which was predicted:
- The Haiku listing cost is lower on 2.1.286 (plateau 405 to 615 tokens instead of 457 to 672 in a controlled re-test with two runs per configuration), while 1 skill is unchanged (70). The cause is not established and the changelog of 2.1.285 and 2.1.286 states none; a listing budget now shared with a 17th bundled skill (`plugin-authoring`, below) fits the data but was not tested.
- The alias runs hit the turn limit more often: 10 of 60 ended with `error_max_turns` (the limit was 3), against none of the 60 alias flows on 2.1.284 (20 of them with 4 turns, all `success`). All ten made three tool calls (Skill, then Bash, then Glob) exploring the working directory; no 2.1.284 run made more than two. The nested call fired in every run either way, so the hit rates are unaffected. Counts are in `results/replication_findings.json` (`alias_turns`).
- The trigger recall is lower in both settings by 2 and 6 points, inside the interval of each; one repeat cannot separate a version change from chance.
- A 17th bundled skill, `plugin-authoring`, is listed from the start in 83 of 83 rows of the 2.1.286 sweep, 60 of 60 alias rows and 71 of 72 re-test rows on 2.1.286; it was absent from all 125 rows of the first run and appeared in one of 72 rows on 2.1.284 (`bundled_skill_plugin_authoring` in `results/replication_findings.json`). It costs about 88 tokens on Sonnet and about 60 on Haiku, so single calls with and without it differ by about that much. Net of it, the empty session is about 235 tokens larger on Sonnet and about 219 on Haiku on 2.1.286; the rest is unexplained (an auto-memory prompt is one unchecked candidate: the model read its `MEMORY.md` in three rows of the 2.1.286 sweep). A controlled re-test (`results/*_v1check_*`, `analysis/analyze_v1check.py`, not in the prediction) shows that an explicit `--permission-mode default` does not change the empty session, that the same 2.1.284 executable does not reproduce its first-run numbers exactly eight days later (Sonnet C100 8,679 and 8,752 against 8,804; Haiku C10 457 against 479), and that a 73-token difference between the explicit and unset modes on 2.1.284 (Sonnet C100) is unexplained.
- What the replication does not cover: the quality run was not repeated, and only one run was made per configuration in the token sweep (the counts repeated exactly within a run on 2.1.284).
- Failures during the replication, disclosed: the first trigger attempt (48 of an intended 192 calls, planned without `--runs 3`) stopped, probably because the laptop went to sleep; its folder is kept privately as `..._replication_trigger_aborted_runs1` (not published) and is not analysed. The published trigger file has 578 rows: calls 254 and 492 were each cut off once (no decision) and run again. The resumed run then stopped once on a locked working folder; the harness now retries the removal and ends the whole process tree of a cut-off call. These edits do not change how a measurement is made.

## Part 14A to 14D: starting size, listing cap, `@file`, skill-writing skills (run 2026-10-08)

Claude Code 2.1.286, same machine and isolated config. Run folder `2026-10-08_x86-laptop_part14` (`bench/part14.py`, first-request window totals, 156 calls), scored with
`analysis/analyze_part14.py` into `results/2026-10-08_x86-laptop_part14/part14_findings.json`. 14E (skills written with help) is reported separately below.

| id | prediction | result | met? |
| :-- | :-- | :-- | :-- |
| A1 | Runs of the same setting repeat exactly | 21 of 21 settings x models identical across two runs | holds |
| A2 | `--disable-slash-commands` removes 2,500 to 3,500 tokens on each model | Sonnet 2,911, Opus 2,911, Haiku 2,110 | fails (Haiku) |
| A3 | Three tools remove more than 10,000 tokens on each model, and tool definitions are more than 60% of the default | Sonnet 13,904 (72.3%), Opus 13,811 (71.8%), Haiku 12,141 (51.0%) | fails (the 60% clause on Haiku) |
| A4 | A one-line system prompt removes 1,500 to 3,000 tokens on each model | Sonnet 2,166, Opus 2,166, Haiku 6,368 | fails (Haiku) |
| A5 | `--exclude-dynamic-system-prompt-sections` removes fewer than 500 tokens | 238, 238, 145 | holds |
| A6 | Haiku default larger than Sonnet; Opus within 500 of Sonnet | Haiku 23,793 against Sonnet 19,242; Opus 19,246 | holds |
| A7 | No skills, three tools, one-line prompt: no model above 4,000 | Sonnet 3,221, Opus 3,318, Haiku 5,483 | fails (Haiku) |
| B1 | Added tokens at 200 and 400 skills within 5% of the value at 100 | 100: 5,700; 200: 8,359; 400: 8,909 (+46.6% and +56.3% over 100) | fails |
| B2 | Total listing at 400 skills (bundled 2,911 + added) between 9,500 and 12,500 | 11,820 tokens, 1.18% of the window | holds |
| B3 | Sharing reading only if B1 and B2 both hold | B1 failed, so no statement about a shared budget is made | not applicable |
| C1 | A `@path` file costs no idle tokens (within 30 of the empty session) | file present but not referenced: 19,248 against 19,242 (+6, the prompt text) | holds |
| C2 | The `@path` reference costs within 150 of the pasted prompt | `@file` raises the first request by 2,962, the pasted text by 2,737: 225 apart | fails |
| C3 | The `@path` reference adds at least 2,000 tokens | +2,962 | holds |
| D1 | Each of `plugin-authoring` and `run-skill-generator` costs more than 1,000 tokens when invoked | +4,283 to +4,353 and +6,142 to +6,144 | holds |
| D2 | Neither listing entry costs more than 150 tokens | not tested: one listing entry cannot be separated from the others | not run |

What this shows, in plain terms: most of the starting size is tool definitions, not skills, on Sonnet and Opus; Haiku's starting prompt is different (a one-line system prompt
removes 6,368 tokens there against 2,166), so the Haiku breakdown must not be inferred from Sonnet. The listing was still growing slightly between 200 and 400 skills (+6.6%),
and with 150-character descriptions 100 skills had not reached it, so the plateau in this test is about 8,400 to 8,900 added tokens.
A literal `@file` costs nothing until it is referenced, then about 225 tokens more than the same text pasted (the file's path and wrapper text are the likely cause; not isolated).

Disclosures: the first launch of the runner was started twice by mistake and several copies ran at once for a short time; the rows written before that were checked
(no duplicates, all settings identical to the earlier exploratory look) and the run was finished by a single process that skips finished rows. The two Sonnet default
rows written by the interrupted first launch were removed and measured again. `bench/run.py` `rm_tree` now empties a work folder it cannot delete because another process holds
it, which changes no measurement. The `error_max_turns` status on some C rows is the one-turn limit; the first request is what is measured.
- **Two copies of the isolated configuration folder.** The variable `CLAUDE_CONFIG_DIR` was set from Git Bash as `$HOME/claude-bench`, which is `/c/Users/.../claude-bench`; Claude Code reads that as a path on the drive root and used `C:/c/Users/.../claude-bench`, a second isolated folder (logged in to the same account, with no personal skills or settings), next to the intended `C:/Users/.../claude-bench`. Runs in this study may have used either; a check on 2026-10-08 gave the same first request (19,242 tokens, 27 tools, 17 skills) under both. Whether the folder explains the 46-token difference from the 19,196 of the replication sweep on 2026-10-07 was not established; that difference remains in the list of unexplained drift. Later runs set the variable in the `C:/...` form.

## Part 14E: skills written with Claude's help (run 2026-10-08)

Sonnet 5.5 wrote 10 skills in each of three arms (a plain request, the bundled `plugin-authoring` skill, Anthropic's `skill-creator` installed from the local clone of anthropics/skills), 30 in all, from the same brief
(`bench/skillwriting_tasks.json`, written before any generation). Each skill was then installed alone and tried on 4 prompts that should trigger it and 4 near-miss prompts that should not (240 calls).
Run folder `2026-10-08_x86-laptop_skillwriting`, scored with `analysis/analyze_skillwriting.py` into `results/2026-10-08_x86-laptop_skillwriting/skillwriting_findings.json`.

| id | prediction | result | met? |
| :-- | :-- | :-- | :-- |
| E1 | Skills asked for in plain words load and parse in at least 9 of 10 cases | 10 of 10 (frontmatter parses, name equals the folder, description within the cap, trigger wording and 3 or more steps present); all three arms 10 of 10 | holds |
| E2 | The plain and tool-assisted arms write longer descriptions than the hand-written arm | no hand-written arm was made (see below); against the published human-written skills (mean 415 characters, median 314.5, over 150 skill files in which the 12 skills of both samples count twice; see the editorial log, static flags): plain 313, `plugin-authoring` 278, `skill-creator` 460 | fails (two of three arms are shorter) |
| E3 | The trigger score of the tool-assisted arms is not more than 1 point of 4 above the plain arm | should-trigger hits per skill (of 4): plain 2.9, `plugin-authoring` 2.9, `skill-creator` 3.2 (differences 0.0 and 0.3) | holds |
| E4 | No arm has a false trigger rate above 10% | 1 of 40 in each arm, and in each case the skill that fired was the bundled `dataviz` skill on "Plot the second column of this CSV", not the generated skill: 0 of 40 for the generated skills | holds |

Other measured differences: the `skill-creator` arm wrote the longest descriptions (460 against 313 and 278 characters), the fewest body items (19.1 against 24.8 and 24.8) and the most output tokens (2,200 against 1,918 and 2,060 on average);
no arm wrote more than one file. The should-trigger rate was 72.5% for the plain and `plugin-authoring` arms and 80.0% for `skill-creator` (29, 29 and 32 of 40); the misses cluster on the same prompts in all three arms
(for example the standup-recap and the HTTP-500 prompts missed in all three), which points to the prompts and not to the arm. The differences between arms are within what 40 prompts per arm can resolve.

Deviations and disclosures, all decided before any score existed except where stated:
- **No hand-written arm.** No person wrote skills for this part, and a skill written by hand for this study would not be independent of the plain arm, so E2 compares with the human-written skills of the workload instead. This changes the comparison the prediction named.
- **Output folder.** The first generation attempt asked for the skills under `.claude/skills/`; Claude Code blocks writes there in `acceptEdits` mode, so the skill was not written. That row is kept as `generation_failed_permission.jsonl` and excluded; every arm was then asked for `out/<slug>/SKILL.md`, and the folder was installed as a skill afterwards.
- **Instruction to every arm:** "do not ask questions, do not run tests, evals or benchmarks, write only the skill folder". This keeps the runs unattended but means `skill-creator` was not used the way its own workflow intends (it normally runs test prompts and iterates).
- **"No decision" counted as no trigger (decided during the run).** On three near-miss prompts the model searched files with other tools and gave no skill call or text within three turns. The runner first stopped on that; it was changed to record it as a non-trigger, and the affected rows are re-run or kept as such. The trigger rows are one per prompt (the last row wins).
- "Loads" is judged from the file (frontmatter, name, cap) and from the fact that the skill was called in the trigger test, not from the session's skill list.
- One run per skill and prompt, one model, one brief per skill: this says little about other skills or models.
- **A flaw in the prompts, found after the scoring.** 7 of the 14 should-trigger prompts that were missed by at least one arm refer to material that is not attached ("the function below", "notes below", "the commit list below", "this transcript"); the model asked for the material or answered in text instead of calling the skill. The rates (72.5%, 72.5%, 80.0%) therefore understate how often a skill fires when the material is present, and the same prompts were missed in all three arms, so the comparison between arms is unaffected. A re-test would put the material in the prompt.

## Amendments and deviations (dated in `editorial_log.md`; the last status notes of `prediction.md` list the later disclosures)

- **2026-10-02, after the main run (analysis only).** The first analysis excluded every C100 run because the skill `shadcn` was missing from the
  list of skills Claude Code reports (`user-invocable: false` keeps a skill out of that list although the model is offered it). The analysis now
  expects such skills to be absent; raw data unchanged.
- **Part 7.** The prediction said cells with mixed outcomes would be repeated on later days; they were not (11 of 192 cells were mixed).
- **Part 9, 2026-10-03.** After the analysis script had been run once on 74 of 144 pages, the Q3 verdict labels were refined and secondary
  analyses (repaired checks, checks that can vary) were added. The primary analysis and the decision rules did not change.
- **Part 12, 2026-10-03.** One generation failed on the network. A rule written before any score excluded rows with zero output tokens and re-ran
  their cells.
- **After the runs, 2026-10-04.** The harness was edited after the runs: the trigger test records the first request's token usage (after the trigger run); the guards accept the status `allowed_warning` (after the runs; the same status had stopped the main run once); the quality runner re-runs a generation that failed on the network (during Part 12). Probe P-09 and the crowded alias sets were added before their own runs (Parts 10 and 11). None of these edits changes how a measurement is made. See `editorial_log.md`.

- **H7, disclosed 2026-10-04.** The prediction named S50 configurations (body-heavy against mid); the test used the synthetic sets S10-B600 and S10-L600 (same descriptions, bodies of about 20,000 characters against short ones), because the synthetic sets have 10 skills.
- **Part 9 briefs, disclosed 2026-10-04.** The quality protocol describes 8 in-scope briefs, 2 out of scope and 2 that need the moved part; Part 9 used 12 in-scope design briefs because only the mechanical stage was run.

## Notes

- A "partly" row is a prediction with no clause contradicted by the data and at least one clause that could not be tested; the row says which.
- The mechanical quality checks are near their ceiling: 6 of 16 never failed in any condition (9 of 16 without the skill), so an improvement beyond the skill's 98.4% of more than about 1.6 points cannot show. No judged comparison was run.
- Hit rates of 10 of 10 have a 95% interval of 72% to 100%; ten runs cannot show a difference smaller than about 28 points.
- Costs per skill are measured for 20 skills and estimated for the rest; rows that rely on estimated costs are H11 and T6.
- Part 13 (replication on 2.1.286) was run on 2026-10-07 and 2026-10-08; the quality run was not repeated.
- The protocol's second comparison for Part 9, original minus placebo, is +8.68 points (interval 5.56 to 11.81) in `quality_findings.json`.
- The expectation of probe P-02 cannot fail ("either name may appear"); P-13 is informative either way; the probe id P-16 was never used.
- Part 9 used 12 in-scope design briefs. The quality protocol also describes out-of-scope briefs and briefs that need the moved part; those belong to the judged
  stage, which was not run.
- The alias runs allowed up to three turns, and some report four in `num_turns`; how Claude Code counts the final reply was not investigated.
- In the trigger test the crowd is 50 skills, of which 3 or 4 are manual-only (46 or 47 are offered to the model), depending on the skill under test.
- Pre-registration times are in `results/prediction_commits.json`; wording changes made to `prediction.md` after the runs are listed in its last dated note.
- Rows that rest on files that are not published cannot be re-run from this repository: X1c (the console streams) and H13 and the offline-claims figures (the withheld snapshot); their findings files are published.
- `prediction.md` keeps every prediction as written (its wording was edited for publication on 2026-10-15; see its last line); the 4.7-or-later tokeniser of Hypothesis 6 means the tokeniser of the newer model generation.

