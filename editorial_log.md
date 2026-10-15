# Editorial log: skill context cost

Dated record of what was done and what changed. Entries are not rewritten in substance; wording corrections made after the
independent verification of 2026-10-04 are listed in the entry "Corrections after an independent verification".

## 2026-10-02

- **Design and pre-registration.** Prediction, selection rule, popularity snapshot, harness and models were fixed and
  committed (the prediction was first committed in `501a73b` at 19:27, whose message also mentions design-stage raw output of smoke tests, which is not evidence; `526cb69` at 19:48 added the selection rule and the popularity snapshot; the first measurement started at 19:53) before the first measurement. An independent review of the design found problems in the
  window shares, the length sweep, one analysis loop, the trimmed-description frontmatter, output decoding and path
  privacy; all were fixed before any run.
- **Probes and smoke tests (not evidence).** Two single probe calls (one per model) and 10 smoke-test calls were made
  to check the output format, the isolation and repeatability. The probes inherited the desktop application's
  environment, which adds bundled skills and tools; the harness removes those variables, and the probe numbers are not
  used. Smoke-test folders are not published.
- **Full run.** 125 calls on a Claude Pro subscription, no API key. The run was interrupted twice by the harness's own subscription-meter guard and resumed after the window reset (one stop is in the console recordings: the status `allowed_warning`, a warning that the five-hour allowance was running high, which the guard treated as a stop; the first resume came before the reset, made one call and stopped again), with the same
  Claude Code version (2.1.284) and the same manifest. The first five calls were made before the console recorder was
  producing output; their data is in `raw.jsonl` and `stdout/`, but they are not in the console recordings.
- **Correction after the run (analysis only, raw data unchanged).** The first analysis excluded every C100 run because
  the skill `shadcn` was missing from the skills Claude Code reports. The skill is marked `user-invocable: false`, which
  keeps a skill out of that list although it is offered to the model. `bench/skill_flags.py` now records this flag and
  the `disable-model-invocation` flag of every skill (`analysis/skill_flags.json`), and the analysis expects such
  skills to be absent from the start-up list. The same flags show that three of the five most-installed skills
  (`grill-me`, `grill-with-docs`, `improve-codebase-architecture`) are already manual-only and add zero tokens.

- **Part 2, invocation cost.** Added after the first results. Predictions I1 to I5 were committed
  (`feb728d`) before any real skill was invoked. They were informed by probe calls on synthetic skills (identical
  descriptions, bodies of 200 to 32,000 characters), which also confirmed that bodies never load unless a skill is
  invoked. One earlier probe of a real skill read about 12,000 tokens too high because it ran with the desktop
  application's environment variables still set; the harness removes them, a repeat in the harness environment
  matched the model of body size, and the probe is not used. The run itself is 40 calls (each of the 20 most-installed
  skills alone, once listed only and once invoked by hand with a slash command), one run each, since earlier
  repetitions of every configuration were identical. The empty-session baseline is taken from the main run.

- **Part 3, delivery mechanisms.** The 9,074-character body of `frontend-design` (`anthropics/skills`, Apache-2.0) delivered as
  a listed skill, an invoked skill, a CLAUDE.md, a pasted prompt and a pointer to a file, 14 calls on the one-million-token
  model, two runs each, identical within each configuration. Predictions M1 to M6 were committed (`40a5685`) before
  running. Outcome against them: M1, M3 and M5 held; M2 failed on its second clause (the pasted prompt came out 112 below the CLAUDE.md figure, not a few above); M4 failed too (the pointer-only file added 150, not under 100). Both have the same cause: any CLAUDE.md adds about 112
  tokens of framing (2,855 for the CLAUDE.md minus 2,743 for the pasted prompt). The measurement counts window tokens of the request;
  prompt caching changes cost and speed, not the size of the window.

- **Part 5, experiment X1 (splitting a monolithic skill).** `design-taste-frontend` (MIT) split mechanically into a 13,117-character
  core and 15 reference files, 6 calls on the one-million-token model (two runs each). Predictions X1a to X1d were committed
  (`b48a931`) before running. Results: invoked, the original adds 35,298 tokens and the split version 5,464 (84.5% less,
  X1a held); with the model asked to read the forbidden-patterns reference the last request is 10,623 above an empty
  session (X1b held); the model opened a reference file in both runs and it was the intended one both times, found from
  the index alone (X1c held); the description is unchanged by construction and the listing was not measured separately
  (X1d not tested as a measurement). Whether the split skill gives output as good as the original was not measured.

- **Part 4, types of skills.** 138 skills labelled against `analysis/taxonomy.md` by an external reader (Antigravity, model
  gemini-3.1-pro-high), after a 28-skill sample (every fifth skill) had been labelled by hand and saved
  (`analysis/labels_sample_manual.tsv`). Agreement with the sample: domain 82%, trigger clarity 86% exactly (100% within one
  point), form 46%. The form axis is therefore not reliable and is reported with that caveat; conclusions rest on
  domain, clarity and counted features. Predictions T1 to T6 (committed in `6b0514c`): T4 held (70% of skills score 3 for
  clarity, and their descriptions are longer, median 510 against 64 and 201 characters); T3 held (platform-reference
  skills have the highest deferred share, median 82%); T5 held for domain and failed for form; T1 failed (platform
  reference and tool operation are 35.5% of the 138, not 40%); T2 held for stubs and failed for persona-or-mode (large, not small), and its first clause (reference and tool-wrapper skills have the largest bodies) also failed; T6 failed (reference skills cost 1.4 times rules-and-style skills to invoke, not 3). Costs per skill are
  measured for the 20 most-installed and estimated for the rest (listing from the fitted line, invocation at 0.37 tokens
  per body character); the listing estimate was fitted on English text and under-counts tokens of non-English
  descriptions.

- **Part 6, the alias pattern.** 50 calls (five conditions, ten runs each, up to three turns) on the one-million-token
  model. Predictions A1 to A6 were committed before running (`prediction.md`). Results: A1 held (the original wording
  called the nested skill 10 of 10 times); A2 failed (the bare `/grilling` and the prose wording also called it 10 of 10,
  so no difference in hit rate was found; the 95% interval for 10 of 10 is 72% to 100%, and the test was run in an
  otherwise empty session, which says nothing about crowded ones); A3 could not be distinguished; A4 held (the alias
  flow ends 362 tokens above the inline version at the last request); A5 held (typing the target directly, 58 above
  inline); A6 was not measured separately. The author's design note was read from the author's repository; the repository text is
  the source for the stated reasons, and no claim is made about the author's intent beyond it. Quality parity of the alias was not
  measured.

- **Part 7, trigger test, and Part 8, claim probes.** The trigger test ran 576 calls (4 skills, 3 description variants, 2 settings, 8
  prompts, 3 runs) across two subscription windows under a supervisor that resumed it after the reset; the claim probes ran 17 probes (the probe run of 2026-10-02 stopped at the meter guard after its control call; all probes ran on 2026-10-03); predictions were committed first (`6e22578`, `2beda9b`). Trigger results against predictions: TR1 held for keyword prompts
  and the unrelated-prompt rate, failed for paraphrases (they triggered more, not less, when the skill was alone); TR2 held (96%
  against a predicted at least 70%); TR3 held; TR4 held for the 100-character description and failed for the 40-character one (alone
  the drop on paraphrases was 12.5 points with an interval from -31.0 to +3.5, not the predicted 15 or more); TR5 held for the
  original and 100-character descriptions and failed for the 40-character one (a 33-point drop); TR6 could not be evaluated (no false
  triggers); TR7 held (11 of 192 cells mixed). The test stopped at the guard once and resumed automatically; one model, four skills and
  an empty working directory limit what can be concluded. Probe P-09 (personal against project precedence) and the quality test were
  not yet run. In the probes, "fails" means the documentation's statement did not hold in Claude Code 2.1.284, not that the probe broke.

- **Terms check (2026-10-03).** The Anthropic terms for the accounts used were read before the runs. The study runs the documented command-line tool in its documented print mode with a subscription login and no API key. The details are not published.

- **Quality analysis review (2026-10-03).** The analysis script and the mechanical checks were reviewed by Antigravity (gemini-3.1-pro-high), which
  read four real pages and found the computed results right for those pages, and listed regular-expression weaknesses and one misleading verdict
  label. Adopted: the Q3 label, a version 2 of the checks and a "checks that can vary" score as secondary exploratory analyses; the primary
  analysis is unchanged (see the deviation notice in `prediction.md`). Not adopted: re-seeding the bootstrap per comparison is deliberate (common
  random numbers); multiple-comparison corrections (five comparisons were fixed beforehand and all are reported); dropping the forced slash
  invocation (stated as a limit instead: the test measures the content of the skill, not whether it is chosen).
- **Quality run finished and analysed (2026-10-03).** 144 of 144 pages; all five preregistered statements evaluated as written (`results/2026-10-03_x86-laptop_quality/quality_findings.json`): Q1, Q2, Q4 and Q5 hold; Q3 meets the fixed 10-point rule but not the prediction's "within 5 points" (split minus original -5.4 points, interval -8.5 to -2.6), reported as a miss of the stricter wording. The split skill's references were opened in 0 of 36 runs. Secondary analyses (v2 checks, checks that can vary) point the same way and are exploratory.
- **Precedence probe P-09 (2026-10-03).** Predicted (Part 10, committed before the run): personal skill wins. Observed: the project skill won 3 of 3 runs. The documented order "personal over project" did not hold in Claude Code 2.1.284 for a slash-invoked skill. The personal test skill was removed from the isolated config dir afterwards. The code of the probe was added to `bench/claim_probes.py`.
- **Alias pattern in a crowded session (2026-10-03).** Prediction Part 11 (committed before the run): B1 at least 9 of 10 per wording, B2 gap under 20 points, B3 no wording more than 10 points below its empty-session result. Observed (`results/2026-10-03_x86-laptop_alias_crowded/alias_findings.json`): 10 of 10 for all three wordings, so B1, B2 and B3 hold; the author's "higher hit rate" claim is not reproduced in a session with 50 skills either. Limit: ten runs per wording, one prompt, one pair of skills.
- **What a skill is, by the documentation (2026-10-03).** Read: Claude Code skills page (code.claude.com/docs/en/skills), the API Agent Skills overview (platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, full text) and the Agent Skills specification (agentskills.io/specification, full text). Reading: a skill is a folder with a `SKILL.md` (frontmatter + Markdown), an open file format (agentskills.io) that Anthropic's three products implement separately, not a model capability. Claude Code: the harness lists names and descriptions in the context, offers a Skill tool and `/name`, and has its own extra fields (`disable-model-invocation`, `user-invocable`, `context: fork`). API: skills are passed in the `container` parameter together with the code execution tool, uploaded through `/v1/skills`, and the model reads `SKILL.md` with bash inside the sandbox. claude.ai: zip upload in settings. Custom skills do not sync across the three surfaces. The documentation does not say the model was trained on skills; it says Claude matches the description against the request. The measurements are consistent with a harness feature: the listing, its 1,536-character cap, the hidden manual-only flag, project-over-personal precedence, skill-over-command, argument substitution and shell injection (run before the model sees the text) are all behaviour of the program around the model; in these tests the decision to call a skill (96% alone, 77% in a crowd, four skills, one model) is the model's.
- **Recordings of `/context` (2026-10-03).** Decision: a reconstructed terminal (real output, drawn window and typing) instead of an interactive screen capture. Console recordings of six configurations, privacy-scanned (only hit: a skill called `gws-gmail`), replay file built by `bench/footage_replay.py`.
- **Part 12: skill against pasted text, finished and analysed (2026-10-03).** 72 pages (`results/2026-10-03_x86-laptop_quality_pasted/quality_pasted_findings.json`). R1 to R5 all hold: pasted 98.6% against the invoked skill 98.4% (+0.2 points, interval -0.7 to 1.0); pasted +6.9 points over no skill; the invoked skill costs 160 tokens more input than the pasted text (R3 predicted 0 to 250); one turn and no tool calls; the original reproduced Part 9 (98.44%, difference 0.0). One generation failed on the network (seq 48), was excluded by a rule written before any score (deviation notice in `prediction.md`) and re-run. Reading: for this one skill, on these heuristic checks, no difference was detected between the invoked skill and the same text pasted into the prompt. The checks are near their ceiling (98.4%), so only a difference larger than the remaining headroom could show. For this skill and these checks, no difference in quality was detected; what a skill adds over pasted text is a different cost profile (the invoked skill used 160 more input tokens, from a wrapper that is not visible in the files) and extra features: an idle cost of one listing entry (21 to 403 tokens for an automatic skill, 0 for a manual-only one), arguments, shell injection and reference files.
- **Corrections after an independent verification (2026-10-04).** An independent review on 2026-10-04 found six errors that had to be corrected and a number of smaller ones. Changes made in response, none of which alters a measurement:
  (1) the Part 12 entry said a skill's idle cost is 0 tokens; the measured idle cost is the listing entry, 21 to 403 tokens for an automatic skill
  and 0 only for a manual-only skill; the entry now says so and no longer states a general equivalence between a skill and pasted text;
  (2) sentences that generalised from four skills or one model were qualified; process wording and a draft note were removed;
  (3) the example weekly install counts in `analysis/offline_claims_findings.json` were withheld like the other row-level leaderboard values, and
  `analysis/analyze_claims_offline.py` no longer writes them (`bench/withhold_leaderboard.py` strips them from the published copy);
  (4) results and limits are collected in `README.md`, `RESULTS.md` and `NUANCES.md`.
- **Notes recorded for the reader (2026-10-04).**
  - *Part 7 deviation.* The prediction said cells with mixed outcomes would be repeated on later days. They were not: the 11 mixed cells of 192 were
    reported as they came, and the replication on a newer Claude Code version (Part 13) has not been run yet (superseded: run on 2026-10-07 and 2026-10-08, see the entry on the replication).
  - *Part 8 probes.* The run folder of 2026-10-02 holds one control row only. All 17 probe verdicts, and P-09, come from the folder of 2026-10-03,
    which re-ran every probe from the start; the verdicts were not carried over from the first day.
  - *Manifests.* The `manifest.json` files in the run folders were rewritten after the runs by `bench/withhold_leaderboard.py` (rank and install
    values removed), so they no longer match the `manifest_sha256` stored in each `env.json` (the hash of the manifest as it was run), except in `alias_crowded`, whose manifest was copied after the values were removed.
    `results/manifest_hashes.json` lists, per run folder, the recorded hash and the hash of the published file.
  - *Character counts.* `results/2026-10-02_x86-laptop_invocation/invocation_findings.json` counts characters of skill files as stored (CRLF line endings count as two characters);
    `skill_features.json` and the predictions count LF-normalised text. The difference is one character per line (86,807 against 88,009 for
    `design-taste-frontend`; 9,076 against 9,142 for `frontend-design`). The invocation slope of 0.397 tokens per character uses the
    stored counts; with LF-normalised counts it is 1.3% higher (`analysis/derived_figures.json`).
  - *Placebo.* The placebo skill of Part 9 matches the original in characters, not in tokens (the quality protocol said tokens).
  - *Code changed after the runs.* After the runs, `bench/trigger_test.py` was edited to record the first request's token usage, the guards of `bench/run.py`, `bench/trigger_test.py` and `bench/quality_run.py` were edited to accept the status `allowed_warning` (it appeared at 91% of the five-hour meter in the main run and on every call once the weekly meter passed 75% in later runs; it is a warning, not a limit), and the quality runner was edited during Part 12 to re-run a generation that failed on the network. Probe P-09 and the crowded alias sets were added before their own runs. None of these edits changes how a measurement is made; the commits are in the history.
  - *Interval wording.* Q1 (lower bound 2.78 against a 3-point criterion), Q2 (lower bound -4.86 against 3 points) and the trigger statements TR4 and TR5
    for the crowded setting hold or fail on the point estimate, with intervals that include the criterion; `RESULTS.md` states this per row.
  - *Not run.* Part 13 (replication on 2.1.286) is pending; no document should be read as reporting it (superseded: run on 2026-10-07 and 2026-10-08, see the entry on the replication).
- **Second review (2026-10-04).** A second independent review found further errors, corrected the same day: a wrong sign in the delivery-mechanism row, the count of manual-only skills in the trigger crowd, the range of `popular_rank`, the verdict rule applied unevenly across rows, an undisclosed change to H7 and to the quality briefs, the probe run of 2026-10-02, the stop reason of the main run, and wording. The scorecard now uses one rule (see `RESULTS.md`).
- **Decisions after the verification (2026-10-04).** (1) The details of the terms check were moved from this log to private notes; the entry above
  keeps one neutral sentence. (2) The study's own ordering of the selected skills (`popular_rank`, based on install counts) stays published; the
  leaderboard ranks, install counts and weekly counts per skill stay withheld. `methodology.md` states this.
- **Sources of figures not in the published data (2026-10-04).** Figures that are not in `results/`, with their sources.
  - *Design-stage probes.* The 0.27 tokens per character and the overhead under 100 tokens in the basis of Part 2, the 200 to 32,000 character synthetic
    bodies, and the pilot results of Part 9 (pages passed 14 to 16 of 16; a full page costing 1.5 to 2 percent of the five-hour allowance) come from
    probe and pilot calls made before the runs. Those calls are not in `results/` and are not evidence; they only informed how the predictions were written.
  - *File sizes.* The 2,015 bytes of the skill `grilling` is the size of the file at the commit recorded in `workload/manifest.json` (check the sha256);
    the 13,117-character core of the split skill (Part 5) is what `bench/skilltx.py` `split_sections` produces from the 12,000-character target, because it
    cuts at a section boundary, and it gives 15 reference files.
  - *X1c.* The raw rows of the restructure run have no tool-call field; `analysis/analyze_restructure.py` reads the saved console streams (not published) and
    writes `results/2026-10-02_x86-laptop_restructure/restructure_findings.json`: in both `X1-split-read` runs the model opened
    `06-9-ai-tells-forbidden-patterns.md`, the intended file, and no other reference file in any run.
  - *Commit hashes.* The hashes cited in the log refer to the history of the working repository. If the study is published from a clean commit, the
    hashes disappear; the dated Parts of `prediction.md` and the entries of this log are then the record of what was written before each run.
  - *Subscription.* The runs used a Claude Pro subscription; `env.json` does not record the plan.
  - *Withheld snapshot.* The statement that the unfiltered top 100 is 68% three publishers is computed on the withheld popularity snapshot.
  - *Probe sessions.* The probe folder of 2026-10-03 holds two sessions: probes P-01 to P-17 ran during the night before 07:40, and P-09 at about 14:00 (the date in its `env.json`).
  - *Static flags.* The share of skills with a static flag is 62 of 138 (44.9%); an earlier figure of 62 of 150 counted the 12 skills that are in both the popular list and the random sample twice. `analysis/analyze_claims_offline.py` now counts each skill once.
- **Replication on Claude Code 2.1.286 (2026-10-07 and 2026-10-08).** Run as in Part 13, scored by `analysis/analyze_replication.py` (`results/replication_findings.json`; table in `RESULTS.md`). V2, V3 and V4 hold; V1 fails: the empty session grew by 277 tokens on Sonnet and 279 on Haiku, 63 of 66 Sonnet configurations stay within 3%, and the Haiku listing cost fell by 7 to 15%. The alias runs ended with `error_max_turns` in 10 of 60 runs, where none of the 60 alias flows had on 2.1.284. Failures during the run: the first trigger attempt (planned without `--runs 3`, 48 calls) stopped, probably because the laptop went to sleep and is kept privately as `..._replication_trigger_aborted_runs1` (not published), not analysed; the published trigger file has 578 rows because calls 254 and 492 were each cut off once and run again; the resumed run stopped once on a locked working folder. The harness (`bench/run.py`, `bench/trigger_test.py`) now retries the folder removal and ends the whole process tree of a cut-off call, and the chain was changed to run the trigger test with `--runs 3`. None of these edits changes how a measurement is made.
- **Part 14 (2026-10-08).** Starting size by model and by removal, the listing cap, `@file`, and skills written with Claude's
  help: run folders `results/2026-10-08_x86-laptop_part14` and `results/2026-10-08_x86-laptop_skillwriting`, scored by
  `analysis/analyze_part14.py` and `analysis/analyze_skillwriting.py`; predictions in `prediction.md`, verdicts in `RESULTS.md`.
- **Replication discrepancy: re-test and explanation so far (2026-10-08).** The headline configurations were run again on both versions, with and without `--permission-mode default`, two runs each (`results/*_v1check_*`, `analysis/analyze_v1check.py`; exploratory, not in the prediction; `bench/run.py` gained `--permission-mode` for it). An independent review of the result then found that a 17th bundled skill, `plugin-authoring`, is listed from the start on 2.1.286 (83 of 83 sweep rows, absent from 125 of 125 rows of the first run, present in one of 72 rows on 2.1.284). It costs about 88 tokens on Sonnet and about 60 on Haiku and explains the single-call jumps of about 88 tokens that this entry first called random. Net of it the empty session is about 235 tokens (Sonnet) and 219 (Haiku) larger on 2.1.286; that remainder, the lower Haiku listing cost (10 skills 405 against 457 to 479, 50 skills 498 against 563 to 571, 100 skills 615 against 672), a 23-token shift of the fixed prompt between sessions and a 73-token difference between permission-mode arms on 2.1.284 are unexplained. The changelog of 2.1.285 and 2.1.286 names no cause. The permission mode does not change the empty session. The extra `error_max_turns` endings come from three tool calls (Skill, Bash, Glob) exploring the working directory in all ten failing runs. The same 2.1.284 executable did not reproduce its first-run numbers exactly eight days later (Sonnet C100 8,679 and 8,752 against 8,804; Haiku C10 457 against 479).
- **Generated pages and the channel handle (2026-10-08).** Three invented domains ending in `.pt` (in four generated pages) were replaced with `.example`; the 16 checks were re-run on those pages and give the same results, and the stored `html_chars` of the four rows is 10 to 15 lower than the edited pages. The channel handle `@benchwerkdev` in the README is intended and stays.
