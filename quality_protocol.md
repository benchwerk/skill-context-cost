# Output-quality protocol

Written 2026-10-02, before any quality run. Purpose: decide whether a skill, or an edited version of it (trimmed,
split, aliased, manual-only), changes the quality of what the agent produces, so that a claim such as "saves 85% of the
tokens" can be made with or without the words "and works as well". No test is foolproof; this protocol is built to fail
loudly instead: every shortcut that would let a flattering result through is closed in advance.

## What can go wrong, and what closes it

| Failure | Closed by |
| :-- | :-- |
| Choosing tasks or rubrics after seeing outputs | tasks, checks and rubric are written and committed before any generation |
| One lucky or unlucky sample | at least 3 samples per task and condition; every sample kept; results as rates with intervals, never one run |
| A judge that likes its own style | judge is a different model family from the one under test; two judges; position of the two answers randomised and swapped |
| A judge that cannot tell good from bad | judge is first calibrated on pairs with a known answer (a real skill against a placebo of the same size) and must pass |
| "Any extra text helps" | a placebo condition: same number of tokens of irrelevant but plausible guidance |
| "The skill does nothing" | a no-skill baseline on the same tasks |
| Subjective scoring only | each task has mechanical checks (counted, regex, parsed, run) in addition to the judge |
| Cherry-picking the edited version | every edit is specified before it is measured; failed edits are reported |
| Drift between conditions | same model, same Claude Code version, same machine, interleaved order, order logged |
| Reading the result into the numbers | the non-inferiority margin and the analysis are fixed beforehand |
| Judge errors hidden | a human scores a random 15% of pairs blind; agreement with the judges is reported |

## Design

- **Conditions** (per skill under test): `none` (no skill, same prompt), `original`, one or more `variant`s, `placebo`.
- **Tasks**: 12 per skill, written before generation: 8 where the skill should help, 2 outside its scope (it should not
  change the answer), 2 that need the part the variant moves out of sight (a reference file; the nested skill).
- **Samples**: 3 per task and condition. Cost for one skill with 4 conditions: 12 x 3 x 4 = 144 generations; run in
  batches under the subscription-meter guard.
- **Checks** (mechanical, per skill): the skill's own testable rules turned into code (patterns that must or must not
  appear, structure, length, whether a question is asked before an answer is given, whether a file is read first).
  Each check returns pass or fail; the score is the pass rate over checks.
- **Judge**: pairwise, blind, on a written rubric of 4 criteria; each pair judged twice with the order swapped; a win
  counts only if both orders agree, otherwise a tie. Judges: Antigravity (Gemini) and a second independent reader.
- **Calibration** (must pass before any result is read): on 12 pairs of original-skill output against placebo output
  where the checks already say which is better, the judge picks the better one in at least 80% of pairs.

## Decision rules (fixed now)

- **Quality**: for the checks, variant minus original in pass rate with a 95% bootstrap interval over tasks. A variant is
  *not worse* if the lower bound of that difference is above -10 percentage points. For the judge, the variant's win rate
  against the original excluding ties; *not worse* if the lower bound of a Wilson interval is above 40%.
- **Value of the skill itself**: original against none, and original against placebo; the skill earns its tokens only if it
  beats both on checks.
- **Efficiency claim** may be stated as "same quality" only if both rules say not worse. If either fails, the report
  says which, and the token saving is stated without the words "same quality".
- **Reporting**: all conditions, all tasks, all samples, including ties, failures and the cases the judge disagreed on.

## Cost control

Generation uses the subscription meter, far more than the one-token counts: a full answer can be thousands of tokens.
Runs stop when a guard on the five-hour allowance is reached (default 80%; 90% in the main runs; wording added 2026-10-04) and resume after the reset; a skill with 4 conditions needs about 144
generations and may take more than one window.

## What this protocol cannot show

Real long-session behaviour, subjective taste, other models, other agents, rare tasks, and whether a person would
prefer the output. Results apply to the tasks written, the model and the Claude Code version recorded.
