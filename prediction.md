# Prediction: skill context cost

Written 2026-10-02, **before any measurement** and before the first read-only checks. Parts are appended, each dated
before its run; no prediction is edited after its run (wording changes made later are listed in the note headed "Wording changes after the runs, 2026-10-04"), and wrong predictions stay in place. Basis: the official documentation and secondary posts, no measured data.

## Hypotheses

1. **Linear then flat.** Added start-of-session tokens grow roughly linearly with the number of installed skills
   while all descriptions fit, then flatten when the listing budget is reached and descriptions are dropped (names
   stay). The plateau is reached before N = 100 on the 200k-token window and later (or not at all in the N range measured)
   on the 1M window.
2. **Per-skill cost with a description.** Between 50 and 150 tokens per skill for real-world descriptions (median
   about 80–100), which matches the unmeasured rule of thumb. Names alone cost far less (under 25 tokens each).
3. **Typical heavy setup.** 50 real skills cost between 2,000 and 7,000 tokens before the first prompt: about 1–3% of a
   200k window and well under 1% of a 1M window. The plateau (if reached) is below 5,000 tokens.
4. **Description length matters more than count at small N.** At fixed N = 50, long descriptions (near the
   1,536-character cap) cost at least 5 times the tokens of short ones (about 100 characters).
5. **Boring outcome is likely.** For most users the answer will be "small in window share, so do not worry, but the
   number is not zero and the tail of a large collection is invisible to the model". 
6. **Newer tokeniser costs more.** The same skill files count about 20–40% higher tokens on a 4.7-or-later tokeniser
   than on an older one, if both are measured.

## What would falsify

- A per-skill cost far outside 25–400 tokens, or a curve with no flattening up to N = 100 on a 200k window.
- 50 real skills costing over 10,000 tokens (hypothesis 3 is wrong high), or under 800 (wrong low).
- Names costing as much as described entries (the cap does not drop descriptions as documented).
- Setup overhead at N = 0 larger than the whole N = 50 delta (the signal would then be in the baseline, not skills).

## Confidence

Low on exact numbers (the listing format is unpublished), moderate on the shape (documented budget behaviour).

## Added 2026-10-02, still before any run

7. **Bodies do not count.** S50-bodyheavy adds the same tokens as S50-mid within run-to-run spread (difference under
   2% of the S50-mid addition). If bodies counted, the 20,000-character bodies would add tens of thousands of tokens.
8. **Cost is linear in description characters** at fixed N: the fitted line explains the three synthetic lengths
   with an error under 10% on the real sets, and about 0.2 to 0.35 tokens per character of description plus a small
   fixed overhead per skill.
9. **`disable-model-invocation: true` removes most of the cost**: at least 80% of the C50 addition. Names may still
   cost something, so the saving may be less than 100%.
10. **Trimming descriptions to 100 characters saves a share proportional to the characters removed**: if the median
    real description is well above 100 characters, the saving is at least 30% of the C50 addition. Trigger quality is
    not measured, so no claim is made that trimming is free.
11. **Individual estimates are within 20% of the measured value** for at least 4 of the 5 individually measured skills.

## Added 2026-10-02 (selection fixed), still before any run

12. **Popular skills are not cheaper than average.** R50 (random sample of the leaderboard) adds between 0.6 and 1.6
    times the tokens of C50 (popular). Popular skills tend to be written with more care, which would push the ratio
    above 1; bundle publishers with long descriptions would push it below.
13. **Description length varies a lot between skills**: the longest description in the top 100 is at least 5 times the
    median. The per-skill estimate will therefore be dominated by a few long descriptions.

## Amended 2026-10-02, still before any run (after an independent review of the design)

- **Hypotheses 1 and 3 (shares of a window):** shares are stated only against the context window of the model that ran;
  hypothesis 1's plateau is tested on the one-million-token model and, for the 200k model, on the C1 to C100 sets.
- **Hypothesis 6 (tokeniser):** compared only on sets below the listing cap (C1, C10), because the two models also differ
  in window and therefore in cap.
- **Hypotheses 4 and 8 (description length):** tested with a sweep of ten skills at five lengths (100, 300, 600, 1,000 and
  1,500 characters), kept below the cap, instead of fifty skills at three lengths.
- **Hypothesis 2:** the range 50 to 150 tokens per skill is the prediction; 25 to 400 is the range outside which it is
  called falsified.
- **Hypothesis 11:** compares the measured increment of a single skill over the one-skill synthetic probe with the
  estimate, since a single skill also carries a fixed overhead.
- **Headline:** the cost of a typical popular skill is the marginal cost between C10 and C50 on the one-million-token
  model, in tokens per skill, with the range between the extreme runs.

## Part 2, invocation cost: written 2026-10-02, before any invocation measurement of real skills

Disclosure: before these predictions, a handful of probe calls on synthetic skills (identical descriptions, bodies of 200 to
32,000 characters, invoked with a slash command) showed a linear cost of about 0.27 tokens per body character plus under
100 tokens, and that an un-invoked skill never loads its body. Hypotheses I1 and I2 are therefore informed by those
probes; they have not been tested on real skills.

I1. Invoking a real skill by hand adds between 0.20 and 0.35 tokens per character of its body; across the 20 most-installed
    skills the linear fit has r-squared of at least 0.9.
I2. The fixed overhead of an invocation (cost beyond the body) is under 150 tokens.
I3. The median body of the 20 most-installed skills is between 2,000 and 10,000 characters, so a typical invocation adds
    roughly 500 to 2,700 tokens; at least one of the 20 adds more than 5,000.
I4. For automatic skills, one invocation costs more than that skill's listing entry in the same session. A listing entry
    repays one invocation after a median of 3 to 30 sessions without use.
I5. Skills that are already manual-only (cost 0 in the listing) cost the same per invocation as automatic skills of the same
    body size.

## Part 3, delivery mechanisms: written 2026-10-02, before any mechanism measurement

The same instruction text (the 9,074-character body of the `frontend-design` skill from `anthropics/skills`, Apache-2.0) is
delivered five ways in an otherwise empty session, on the one-million-token model: as a skill (listed, and invoked by
hand), as a project CLAUDE.md, pasted into the prompt, and as a file that a short CLAUDE.md pointer tells the model to
read. Added tokens are measured against an empty session with the same one-character prompt. The single-skill listing and
invocation of this skill were already measured in the main runs (listing 69, invocation 2,777 tokens).

M1. A CLAUDE.md holding the text adds between 2,500 and 3,100 tokens in every session, used or not.
M2. The skill invoked by hand, and the text pasted into the prompt, each add within 150 tokens of the CLAUDE.md figure
    (the same text), the prompt by a few more tokens for the task sentence.
M3. The skill that is listed but not used adds under 100 tokens.
M4. The pointer-only CLAUDE.md (the file not read) adds under 100 tokens.
M5. When the model is told to read the file, the context at the second request is within 15% of the CLAUDE.md figure plus
    300 tokens (the tool call and its framing), and the model reads the file in at least one of two runs.
M6. Expected cost per session depends on how often the instruction is needed: a CLAUDE.md pays its full size every session,
    a skill pays its listing every session plus its body when used, a pasted prompt pays only when used, and a file
    pointer pays its pointer every session plus the file when used. The measured sizes decide where these cross; no
    claim about quality or about being followed is made in this part.

## Part 4, anatomy and types of skills: written 2026-10-02, before reading any type label

Counted features of the 138 skills (100 most-installed that pass the rule, plus 38 further skills from the random
comparison sample) were extracted first (`skill_features.json`): 92 are multi-file, 73 point to files in their own folder
(median 71% of their material deferred), 6 are manual-only, the median body is 8,086 characters and the largest
(`design-taste-frontend`, 86,807 characters in one file) defers nothing. Each skill is then labelled on two axes
(`taxonomy.md`: domain D1 to D9, form F1 to F6) and a trigger-clarity score by an external reader, and a 28-skill sample is
labelled by hand beforehand (`labels_sample_manual.tsv`) to measure agreement.

T1. Platform-reference (D3) and tool-operation (D4) skills together are the largest group, at least 40% of the 138.
T2. By form, reference (F2) and tool-wrapper (F4) skills have the largest median body; persona-or-mode (F5) and
    stub-pointer (F6) the smallest, under 3,000 characters.
T3. Deferred share (material in files the body points to) is highest for platform-reference skills.
T4. At least 60% of skills score 3 for trigger clarity, and their descriptions are longer at the median than those scoring 1 or 2.
T5. Agreement between the external labels and the manual sample is at least 70% on domain and 60% on form.
T6. The cost of invoking a skill by hand differs more between forms than the listing cost does; the median invocation cost
    of reference skills is at least three times that of rules-and-style skills.

## Part 5, building a skill efficiently: experiment X1, written 2026-10-02, before it was run

`design-taste-frontend` (`leonxlnx/taste-skill`, MIT) is a single 87,126-character file whose invocation was measured at
35,199 tokens. Mechanical edit, no sentence changed: the frontmatter, the introduction and the first sections stay in
SKILL.md up to 12,000 characters of body, every later top-level section becomes its own file under `references/`, and
SKILL.md ends with an index of those files (15 files). Measured by invoking the skill by hand on the one-million-token
model, two runs each: the original, the split version, and the split version with the prompt asking for the reference about
forbidden AI-tell patterns (up to three turns).

X1a. The split version adds between 4,000 and 6,000 tokens when invoked, at least 80% less than the original.
X1b. In the split-and-read run, the context at the last request is between 8,000 and 11,500 tokens above an empty session.
X1c. The model opens a reference file in at least one of two runs, and it is the file about forbidden patterns in at least one.
X1d. The listing cost is unchanged (the description is not edited).
Not measured here: whether the model, given only the core and an index, produces output as good as with the full text.

## Part 6, the alias pattern: written 2026-10-02, before it was run

In `mattpocock/skills` the skill `grill-me` is manual-only and holds one line (`Call the Skill tool with "grilling"`); the
shared interview loop is the automatic skill `grilling` (2,015 bytes). The author's own design note (`.agents/invocation.md`)
says that spelling out the Skill tool "gets a higher hit rate" than a bare `/name` in prose, and that a manual skill is for
orchestration while the automatic one holds the reusable discipline. Tested on the one-million-token model with the
prompt `/grill-me I want to build a todo app.`, up to three turns, ten runs per condition: the original wording; the body
replaced by `Run /grilling.`; the body replaced by `Use the grilling skill to interview the user.`; the body replaced by the
full text of `grilling` with no second skill installed (inline); and `/grilling` typed directly (no alias).

A1. With the original wording the model calls the Skill tool for `grilling` in at least 9 of 10 runs.
A2. The hit rate of the original wording is at least 20 percentage points above that of `Run /grilling.`.
A3. The hit rate of the prose wording lies between the other two.
A4. The context at the last request of the original (alias) flow is within 600 tokens of the inline version; the extra turn
    and tool call cost under 600 tokens.
A5. Typing `/grilling` directly costs within 150 tokens of the inline version.
A6. Because the alias is manual-only, the listing cost of having both skills installed equals that of `grilling` alone.
Not measured here: whether the interview itself is as good through the alias as without it (see the quality protocol).

## Part 7, trigger test: written 2026-10-02, before it was run (design revised once after an independent review)

Four real automatic skills (`playwright-best-practices`, `seo-audit`, `deploy-to-vercel`, `frontend-design`), each with three
descriptions (original; cut at a word boundary within 100 characters; within 40), in two settings (the skill alone; among the 49
most-installed other skills), eight prompts per skill (two that should trigger and use the skill's keywords, two that should trigger
and are paraphrased without them, three unrelated, one near-miss), three runs per cell: 576 calls on the one-million-token model,
up to three turns, in an otherwise empty working directory. Outcome per call: the model calls the Skill tool for the target skill
(hit), calls another skill, or answers in text (no skill). Other tools called first do not end the observation.

TR1. Original description, alone: the skill is called on at least 85% of keyword prompts and on fewer paraphrase prompts, by at
     least 10 points; it is called on at most 5% of unrelated prompts.
TR2. Over all positive prompts with the original description, alone, the skill is called at least 70% of the time (the claim of
     about 50% in the community writing is not reproduced).
TR3. Skills do trigger in print mode (`claude -p`) on this version: recall is above 0 (the claim of 0% is not reproduced).
TR4. The 100-character description keeps the call rate within 15 points of the original; the 40-character description lowers the
     rate on paraphrase prompts by at least 15 points but keeps keyword prompts within 15 points (the name still says what it is).
TR5. Among 50 skills the call rate is lower than alone by 0 to 25 points over all positive prompts.
TR6. At least 60% of the calls to the skill on unrelated or near-miss prompts occur on the near-miss prompts.
TR7. Over three runs, at least one prompt-and-variant cell gives different outcomes on different runs (the behaviour is not deterministic).

Decision rule (fixed now). Differences between variants are reported with 95% Newcombe intervals on proportions pooled over the four
skills (48 positive calls per variant and setting). A trimmed description is said to show no evidence of harm only if the lower
bound of its difference from the original is above -15 percentage points; with this sample size smaller differences cannot be
excluded, and the result is stated that way. Cells with mixed outcomes are repeated on later days.
Not measured here: the quality of what the skill then does, other models, other agents, an existing codebase in the directory.

## Part 8, claim probes: written 2026-10-02, before they were run

Each probe in `bench/claim_probes.py` carries, in its `expect` field, what the cited documentation or source says should happen.
That text, not the author's guess, is the prediction; the verdict (holds, fails, inconclusive) is computed by the probe's `check`
function from what Claude Code reports. Probes: skills without frontmatter; a name that differs from the directory; the reserved
word `claude` in a name; description length from 500 to 6,000 characters against listing tokens (the 1,536-character cap against the
1,024 of the specification and the 250 of an old issue); boolean spellings of `disable-model-invocation`; invalid optional fields;
block-scalar descriptions; a skill and a command with the same name; nested and parent skill directories (with and without git);
`paths` globs; `.agents/skills`; argument substitution; shell injection and a failing injected command; whether
`disable-model-invocation` stops the model from calling the skill. One run per probe except the last (three per arm), on the
one-million-token model. Precedence between personal and project skills is deferred until the trigger test no longer needs the
shared configuration directory.

## Part 9, output quality of the design skill: written 2026-10-03, before the full run

Skill: `design-taste-frontend` (MIT). Conditions: none (the bare brief), original, split (the 13 KB core and 15 reference files of
experiment X1), placebo (the skill's name and description over the same number of characters taken from unrelated backend, cloud and
tooling skills). Twelve briefs (`bench/quality_tasks.json`), three samples each, 144 generations on the one-million-token model,
explicit slash invocation for the three skill conditions (so the test measures the content, not triggering), up to eight turns, pages
of 120 to 180 lines. Sixteen mechanical checks (`bench/quality_checks.py`), each a prohibition in section 9 of the skill; a page passes a
check when the forbidden pattern is absent. Score of a page = share of the 16 checks passed. Two pilot runs of 3 to 4 generations
checked the pipeline and the cost (not used as data): without any skill pages passed 14 to 16 of 16 checks, so the checks have little
headroom, and in three split-skill pilot runs the model opened no reference file.

Q1 (positive control). The original skill raises the mean score over none by at least 3 percentage points. If the interval for the
   difference includes 0, the checks are not sensitive enough on this model and no later comparison can show "same quality";
   it can show only that no difference was detected.
Q2. Placebo is within 3 points of none.
Q3. Split is within 5 points of original (the fixed rule in `quality_protocol.md`: not worse if the lower bound of the
   difference is above -10 points, with the caveat of Q1).
Q4. The model opens a reference file in fewer than 25% of split runs.
Q5. Em-dashes appear in at least 25% of pages written without the skill and in fewer with the original skill.
Deviations from `quality_protocol.md`, stated now: this part is the mechanical-check stage only; the blinded pairwise judge,
its calibration and a blind human sample come later and only if the checks leave room to compare; briefs were shortened
to compact pages after the pilot because full pages cost about 1.5 to 2 percent of the five-hour allowance each.

### Deviation notice for Part 9, 2026-10-03 (before the run finished; 74 of 144 pages existed)

An independent review of the analysis script and checks (Antigravity, which read the code and four generated pages) found weaknesses in several
regular expressions and in one verdict label. Changes: (1) the label for Q3 now distinguishes "within the margin and no decrease detected",
"within the margin but a decrease is detected" and "harm not excluded"; (2) a second version of the checks (`bench/quality_checks_v2.py`) and a
score restricted to the checks that fail on at least one page are reported as secondary, exploratory analyses. The primary analysis,
the original 16 checks (hash in env.json) and the decision rules above are unchanged. Disclosure: before these additions the analysis script
had been run once on the 74 finished pages to test that it works; no generation, prompt or check used for the primary analysis was changed
after that look. The pages are saved, so both versions are computed offline from the same replies.

## Part 10: precedence probe P-09 (written 2026-10-03, before the run)

Claim C-024: when a personal skill and a project skill have the same name, which one is used? The Claude Code skills documentation says
enterprise over personal over project; the CLI help text calls "project over user" the universal convention. Probe: skill `prec` in the
isolated config dir (personal, replies PERSONALVERSION) and in the project (replies PROJECTVERSION), invoked with `/prec`, 3 runs,
Sonnet 5.5, Claude Code 2.1.284. The personal copy is deleted after the probe.
Prediction: the personal skill wins in 3 of 3 runs (the documentation). If the project skill wins, or the runs differ, the claim as
documented fails or is inconclusive; any mixed result is reported as it is.

## Part 11, the alias pattern in a crowded session: written 2026-10-03, before it was run

Part 6 found, in an empty session, that the nested call to `grilling` fired 10 of 10 times for all three wordings of the alias, so the
author's "higher hit rate" claim was not reproduced. The author's claim may concern real sessions with many skills installed. Test: the same
prompt (`/grill-me I want to build a todo app.`, up to three turns, ten runs per wording, Sonnet 5.5 1M, Claude Code 2.1.284), with
`grill-me` and `grilling` installed among the 48 most-installed other skills (50 skills in all, the setting of the trigger test; the
listing stays under its cap on this model). Wordings: the original; the body replaced by `Run /grilling.`; the body replaced by
`Use the grilling skill to interview the user.`

B1. Each wording calls the Skill tool for `grilling` in at least 9 of 10 runs (the instruction sits in a body the model has already
    loaded, so the crowd of descriptions should not matter much, unlike autonomous triggering in Part 7).
B2. The original wording is less than 20 percentage points above `Run /grilling.` (the claim stays not reproduced).
B3. No wording loses more than 10 points against its empty-session result of 10 of 10.
If B1 fails for a wording, that wording's hit rate is reported as measured; the sample is ten per wording, so a difference of one run is
not evidence.

## Part 12: the skill against the same text pasted into the prompt, written 2026-10-03 before it was run

Question: is a skill, once it is invoked, the same as a text that holds the instructions, or does the model do something different?
Test: the same design skill and the same 12 briefs and suffix as Part 9, Sonnet 5.5 1M, Claude Code 2.1.284, three samples per brief, in one run
with two conditions: `original` (the skill installed, invoked by `/design-taste-frontend <brief>`, as in Part 9) and `pasted` (no skill
installed; the skill file without its frontmatter, 86,805 characters, placed in the prompt in front of the brief and the suffix, sent on
stdin because a Windows command line cannot hold it). 72 generations. Scoring: the 16 checks of Part 9 (the primary set, unchanged),
exploratory secondary analyses as in Part 9. The earlier `none` and `original` pages of Part 9 are pooled only as a secondary comparison
(different hours of the same day: drift is possible). Tokens: every row keeps the full usage of the result.

R1. Mean score of `pasted` is within 3 percentage points of `original` of the same run, and the interval for pasted minus original includes 0:
    the model has the same text in both cases, so no difference is expected. If the interval excludes 0, the delivery route matters and
    the direction is reported.
R2. `pasted` is at least 3 points above `none` of Part 9 (interval above 0): the instructions work from the prompt as well.
R3. Tokens: for runs of one turn, the median total input of `original` (input + cache creation + cache read of the result) exceeds that of
    `pasted` by between 0 and 250 tokens (the one-line listing of the installed skill and the harness wrapper around the body).
R4. `pasted` runs take one turn and open no file (the median number of turns is 1).
R5. Replication of Part 9: `original` in this run is within 5 points of 98.4%, its score in Part 9.
Limits stated now: one skill, one model, heuristic checks with a ceiling (6 of 16 never fail), forced slash invocation (the test measures
the content and its route, not whether the model chooses the skill), the harness wrapper around an invoked skill body is not visible in the output.

### Deviation notice for Part 12, 2026-10-03 (during the run, 49 of 72 generations existed)

One generation (seq 48, `pasted`, brief T09, sample 1) returned the text "API Error: Can't reach the API server" after 332 seconds: a network failure, not a page. The runner had stored it as a finished row (zero output tokens, no meter reading). Rule added now, independent of any score: a row with zero output tokens is an infrastructure failure; it stays in `raw.jsonl` and is reported (`failed_attempts_excluded_and_rerun` in the findings), it is excluded from the analysis, and its cell is run again by a resume (the runner now treats such a row as not done). No generation, prompt or check of the primary analysis changed; the decision was taken before any Part 12 score was computed.

## Part 13: replication on a newer Claude Code, written 2026-10-03 before it was run

The desktop app installed Claude Code 2.1.286 after the whole study ran on 2.1.284. Replication on 2.1.286, same machine, same isolated config
(`results/<date>_x86-laptop_replication_*`): the token measurements (`bench/run.py`, one run per configuration: the token counts repeated exactly in
every run on 2.1.284), the trigger test (576 calls, `bench/trigger_test.py`) and the claim probes (`bench/claim_probes.py`, including P-09). The quality
run is not repeated. Every call of the replication also records full usage and the meter for a separate study of the subscription meter.

V1. Added tokens (a configuration minus the empty session of the same version) equal the 2.1.284 values within 3%: C1, C10, C50, C100, C50-disable,
    the invocation configurations and the mechanisms. The empty session itself may move (the harness prompt changes between versions); if it does, the
    size of the change is reported and the deltas are compared.
V2. Trigger test: recall of the original description alone within 10 percentage points of 96%, recall among 50 skills within 10 points of 77%,
    0 false triggers on 288 should-not-trigger prompts.
V3. Every probe verdict equals the 2.1.284 verdict (cap 1,536 characters; `.agents/skills` not loaded; no frontmatter not loaded; `claude-helper` loads;
    skill beats command; boolean spellings hidden; P-09: project over personal).
V4. Alias test: the nested call fires 10 of 10 for all three wordings, empty and crowded.
A difference is reported as measured, with the version change as the only known change; a difference of one call in a cell is not evidence.

## Status notes, 2026-10-04 (added after the runs; no prediction above was changed)

- **Part 7.** The prediction said cells with mixed outcomes would be repeated on later days. They were not: the 11 mixed cells of 192 are reported as measured.
- **Part 9.** The change of the Q3 verdict labels and the secondary analyses were decided after the analysis script had been run once on 74 of the 144 pages
  (disclosed above): an amendment informed by an interim look at the script's output, not by new data; the primary analysis and the decision rules are unchanged.
- **Part 13.** Not run yet at the time of this note. No results folder exists for it.

### Wording changes after the runs, 2026-10-04 (no prediction changed)

- Header: the sentence on how the file is edited was corrected (it said Parts are never edited; it now says no prediction is edited after its run).
- Process wording removed from Parts 9 and 12: "the owner's blind sample" became "a blind human sample", "Question (owner)" became "Question", "not visible to us" became "not visible in the output".
- The line endings of the file were converted from CRLF to LF, which is why the commit of 2026-10-04 shows every line as changed.
- The deviation notice of Part 12 says 49 of 72 pages existed when it was written; the output files show that 50 existed.
- The status notes of 2026-10-04 above and this note were appended; nothing else in the file was changed.

### Further disclosures, 2026-10-04 (no prediction changed)

- **H7.** The prediction named S50 configurations (body-heavy against mid); the test used the synthetic sets S10-B600 and S10-L600, because the synthetic sets have 10 skills.
- **Part 9.** The quality protocol describes 8 in-scope briefs, 2 out of scope and 2 that need the moved part; Part 9 used 12 in-scope design briefs because only the mechanical stage was run.
- **Part 2.** It was committed before any invoked measurement of a real skill in the harness. One earlier probe of a real skill, made before the harness removed the desktop application's environment variables, read about 12,000 tokens too high; it is described in `editorial_log.md` and not used.
- **Part 13.** The sentence on the meter study was reworded before the replication (it said "the quota study"); the replication itself has not been run.
- The changes made to this file after the runs are listed as an end-of-line-insensitive diff in `results/prediction_changes_after_runs.diff`.

### Part 13 was run, 2026-10-07 and 2026-10-08 (no prediction changed)

The replication ran as written, with one addition: the alias test needed ten runs per wording, which the main sweep did not make, so it was run separately (60 calls). Results and the failures during the run are in `RESULTS.md`. The earlier note that Part 13 had not been run is superseded.

## Part 14: the starting size, delivery by `@file`, and skill-writing help, written 2026-10-08 before it was run

Questions after the review: can the empty session be made smaller, does the listing cap include the bundled skills, how does a literal `@file`
reference compare with a skill and a pasted prompt, and does a skill written with Claude's own help differ from one written by hand. Claude Code 2.1.286,
the same machine and isolated config, first-request token counts from `bench/run.py` style runs (window total = input + cache creation + cache read of the
first request). An exploratory look on 2026-10-08 (Sonnet, two runs per setting, not study data) preceded this text: the settings below were chosen from it,
the three models and the predictions were not. That look measured: default 19,242; no skills 16,331; one-line system prompt 17,076; three tools 5,338;
one tool 3,455; no skills, three tools and one-line prompt 3,221 tokens.

**14A. Starting size by setting (Sonnet, Haiku, Opus; two runs each).**
- A1. Runs of the same setting repeat exactly (as in all earlier token runs).
- A2. `--disable-slash-commands` removes between 2,500 and 3,500 tokens on each model.
- A3. `--tools Read,Edit,Bash` removes more than 10,000 tokens on each model; the tool definitions are more than 60% of the default starting size.
- A4. A one-line `--system-prompt` removes between 1,500 and 3,000 tokens on each model.
- A5. `--exclude-dynamic-system-prompt-sections` removes fewer than 500 tokens on each model.
- A6. The Haiku default is larger than the Sonnet default (as in Part 13); the Opus default is within 500 tokens of Sonnet.
- A7. With a one-line system prompt, no skills and three tools, no model starts above 4,000 tokens.

**14B. Does the listing cap include the bundled skills? (Sonnet, 1M window; synthetic sets of 100, 200 and 400 automatic skills with 150-character descriptions.)**
The bundled skills cannot be switched off without switching off every skill, so this test measures the total listing, not the sharing itself.
- B1. The added tokens at 200 and at 400 skills are within 5% of the added tokens at 100 skills (the cap holds).
- B2. The total listing at 400 skills (bundled 2,911 plus added) lies between 9,500 and 12,500 tokens, that is between 0.95% and 1.25% of the 1M window.
- B3. Reading: if B1 and B2 both hold, a total near 1% is reported as consistent with a shared budget; it is not reported as proof, because the budget that would remain with the bundled skills off was not measured.

**14C. Delivery of the same 9,074 characters by a literal `@file` reference (Sonnet; the Part 12 text; five runs each).**
- C1. A prompt that names the file as `@path` costs no idle tokens (idle cost within 30 tokens of the empty session).
- C2. Its used cost is within 150 tokens of the pasted prompt of Part 12 (2,743).
- C3. The file's text reaches the model in the first request (the count rises by at least 2,000 tokens over the prompt without the reference).

**14D. The two bundled skills about writing skills (`plugin-authoring`, `run-skill-generator`).** Their listing entries and body costs are measured when invoked.
- D1. Each body costs more than 1,000 tokens when invoked.
- D2. Neither listing entry costs more than 150 tokens (the long descriptions of the bundled skills are cut by the cap, as the replication suggested for `plugin-authoring`).

**14E. A skill written with Claude's help against one written by hand (Sonnet; ten skills per arm; arms: hand-written to the quality protocol; asked for in plain words; written with `plugin-authoring`; written with Anthropic's separately published skill-creator).**
The fourth arm needs a download from a public repository and runs only after approval; the others do not.
Each skill is checked by script: it loads (appears in the session's skill list), its frontmatter parses, the description is within 1,536 characters, the body
contains a trigger condition and at least three steps or rules, and it triggers on at least 3 of 4 should-trigger prompts and on 0 of 4 should-not-trigger prompts.
- E1. Skills asked for in plain words load and parse in at least 9 of 10 cases.
- E2. The mean description length of the plain-words and tool-assisted arms is above that of the hand-written arm.
- E3. The trigger score (should-trigger hits) of the tool-assisted arms is not more than 1 point of 4 above the plain-words arm. A larger difference would be reported as a finding.
- E4. No arm has a false trigger rate above 10%.
Any quality judgment beyond these scripted checks is out of scope for this part.

**Not in this part:** the behaviour of skill text after context compaction, and whether an explicit instruction makes the model open reference files of a split skill. Both need a separate preregistration.

Verdict rule: as in `RESULTS.md`. A change of any prediction above after its run is written as a dated note below, not as an edit.

### Part 14 was run, 2026-10-08 (no prediction changed)

14A to 14D and 14E ran as written with these changes, all listed in `RESULTS.md`: D2 could not be tested; the hand-written arm of 14E was replaced by the published human-written skills of the workload; the skills of 14E were written to `out/<slug>/` and installed afterwards; a trigger call with no skill call and no answer was counted as a non-trigger. Compaction and reference-file reading were not run.

_Edited for publication on 2026-10-15: wording only (one remark outside the study, two references to who asked or approved); every prediction, date and verdict is unchanged._
